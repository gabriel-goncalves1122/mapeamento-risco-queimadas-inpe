import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed

FORBIDDEN_REFERENCES = ('dim_rel_', 'queimadas_focos_calor')
FORBIDDEN_COMMANDS = ('alter', 'create', 'delete', 'drop', 'insert', 'kill', 'load', 'replace', 'truncate', 'update')

@dataclass(frozen=True)
class BenchmarkQuery:
    query_id: str
    scenario: str
    name: str
    path: Path
    sql: str

def strip_comments(texto):
    linhas = []
    for linha in texto.splitlines():
        if linha.strip().startswith("--"):
            continue
        linhas.append(linha)
    return "\n".join(linhas)

def split_sql(texto):
    statements = []
    atual = []
    in_string = False
    escape = False

    for char in texto:
        if char == "'" and not escape:
            in_string = not in_string
        if char == ";" and not in_string:
            statement = "".join(atual).strip()
            if statement:
                statements.append(statement)
            atual = []
            continue
        atual.append(char)
        escape = char == "\\" and not escape

    statement = "".join(atual).strip()
    if statement:
        statements.append(statement)
    return statements

def validar_statement(statement, caminho):
    normalizado = statement.strip().lower()
    if not (normalizado.startswith("select") or normalizado.startswith("with")):
        raise ValueError(f"{caminho} contem comando nao permitido; use apenas SELECT.")

    for termo in FORBIDDEN_REFERENCES:
        if termo in normalizado:
            raise ValueError(f"{caminho} referencia datasource fora do escopo: {termo}")

    for comando in FORBIDDEN_COMMANDS:
        if re.search(rf"\b{comando}\b", normalizado):
            raise ValueError(f"{caminho} contem comando mutante ou operacional: {comando}")

def descobrir_sqls(sql_dir):
    return sorted(sql_dir.rglob("*.sql"))

def carregar_queries(sql_dir):
    queries = []
    for sql_file in descobrir_sqls(sql_dir):
        texto = sql_file.read_text(encoding="utf-8")
        statements = split_sql(strip_comments(texto))
        if len(statements) != 1:
            raise ValueError(f"{sql_file} deve conter exatamente uma consulta.")
        statement = statements[0]
        validar_statement(statement, sql_file)
        scenario = sql_file.parent.name
        queries.append(
            BenchmarkQuery(
                query_id=f"{scenario}/{sql_file.stem}",
                scenario=scenario,
                name=sql_file.stem,
                path=sql_file,
                sql=statement,
            )
        )
    return queries

def executar_sql(url, query, cache_mode, timeout):
    use_cache = cache_mode == "warm"
    payload = json.dumps(
        {
            "query": query,
            "resultFormat": "object",
            "context": {
                "useCache": use_cache,
                "populateCache": use_cache,
            },
        }
    ).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    inicio = time.perf_counter()
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
    latencia_ms = (time.perf_counter() - inicio) * 1000.0
    dados = json.loads(raw.decode("utf-8"))
    linhas = len(dados) if isinstance(dados, list) else 0
    return latencia_ms, linhas, len(raw)

def executar_requisicao(
    query,
    profile,
    capacity_scenario,
    concurrency,
    round_index,
    cache_mode,
    broker_url,
    timeout,
):
    started_epoch = time.time()
    started_at = datetime.fromtimestamp(started_epoch).isoformat(timespec="seconds")
    try:
        latencia_ms, linhas, bytes_retornados = executar_sql(
            broker_url,
            query.sql,
            cache_mode,
            timeout,
        )
        status = "OK"
        erro = ""
    except HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="replace")
        latencia_ms = (time.time() - started_epoch) * 1000.0
        linhas = 0
        bytes_retornados = len(detalhe.encode("utf-8"))
        status = "ERRO"
        erro = f"HTTP {exc.code}: {detalhe}"
    except (TimeoutError, URLError, RuntimeError, OSError) as exc:
        latencia_ms = (time.time() - started_epoch) * 1000.0
        linhas = 0
        bytes_retornados = 0
        status = "ERRO"
        erro = str(exc)

    ended_epoch = time.time()
    ended_at = datetime.fromtimestamp(ended_epoch).isoformat(timespec="seconds")
    return {
        "profile": profile,
        "capacity_scenario": capacity_scenario,
        "concurrency": concurrency,
        "round": round_index,
        "cache_mode": cache_mode,
        "scenario": query.scenario,
        "query_id": query.query_id,
        "query_name": query.name,
        "query_file": str(query.path.relative_to(PROJECT_ROOT)),
        "status": status,
        "latencia_ms": round(latencia_ms, 3),
        "linhas_retornadas": linhas,
        "bytes_retornados": bytes_retornados,
        "started_at": started_at,
        "ended_at": ended_at,
        "started_epoch": round(started_epoch, 6),
        "ended_epoch": round(ended_epoch, 6),
        "erro": erro,
    }

def build_work_items(queries, rounds, cache_modes, seed, concurrency, round_offset=0):
    items = []
    for round_index in range(round_offset + 1, round_offset + rounds + 1):
        for cache_mode in cache_modes:
            for query in queries:
                if cache_mode == "warm" and query.scenario.startswith(("01", "02", "03", "04", "05")):
                    continue
                items.append((query, round_index, cache_mode))
    random.Random(seed + concurrency + round_offset).shuffle(items)
    return items

def executar_items(items, profile, concurrency, broker_url, timeout):
    return executar_items_capacity(items, profile, "manual", concurrency, broker_url, timeout)

def executar_items_capacity(items, profile, capacity_scenario, concurrency, broker_url, timeout):
    resultados = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                executar_requisicao,
                query,
                profile,
                capacity_scenario,
                concurrency,
                round_index,
                cache_mode,
                broker_url,
                timeout,
            )
            for query, round_index, cache_mode in items
        ]
        for future in as_completed(futures):
            resultados.append(future.result())
    return resultados

def fetch_json(url, timeout):
    request = Request(url, headers={"Content-Type": "application/json"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def coletar_druid_segments(broker_url, timeout):
    query = """
        SELECT
          datasource,
          COUNT(*) AS segmentos,
          SUM(num_rows) AS linhas,
          SUM(size) AS tamanho_bytes
        FROM sys.segments
        WHERE is_available = 1
        GROUP BY datasource
        ORDER BY tamanho_bytes DESC
    """
    payload = json.dumps({"query": query, "resultFormat": "object"}).encode("utf-8")
    request = Request(
        broker_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return [
            {
                "datasource": "ERRO",
                "segmentos": 0,
                "linhas": 0,
                "tamanho_bytes": "falha_ao_coletar",
            }
        ]

def healthcheck(broker_url, timeout):
    try:
        executar_sql(broker_url, "SELECT 1 AS ok", "cold", timeout)
    except Exception as exc:
        raise RuntimeError(f"Nao foi possivel consultar o Druid Broker em {broker_url}: {exc}") from exc

