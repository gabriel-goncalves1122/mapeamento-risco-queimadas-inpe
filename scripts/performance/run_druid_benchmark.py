"""
Executa benchmarks de latencia e carga contra o Apache Druid SQL.

A suite usa apenas dimensoes batch ja ingeridas. O objetivo e medir o limite
operacional do OLAP local sem alterar dados nem recriar ingestion tasks.
"""
import argparse
import csv
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from src.config.constants import PROJECT_ROOT


DEFAULT_SQL_DIR = PROJECT_ROOT / "scripts" / "sql" / "performance"
DEFAULT_OUT_ROOT = PROJECT_ROOT / "data" / "results" / "performance" / "druid_benchmark"
DEFAULT_BROKER_URL = "http://localhost:8082/druid/v2/sql"
DEFAULT_COORDINATOR_URL = "http://localhost:8081"
DEFAULT_CONTAINERS = (
    "broker",
    "historical",
    "coordinator",
    "middlemanager",
    "router",
    "postgres",
)
FORBIDDEN_REFERENCES = (
    "fato_focos_incendio",
    "fogo_eventos_stdbscan",
    "dim_rel_",
    "queimadas_focos_calor",
)
FORBIDDEN_COMMANDS = (
    "alter",
    "create",
    "delete",
    "drop",
    "insert",
    "kill",
    "load",
    "replace",
    "truncate",
    "update",
)

PROFILE_CONFIGS = {
    "smoke": {
        "concurrency_levels": [1],
        "rounds": 1,
        "cache_modes": ["cold"],
        "duration_seconds": 0,
        "stop_on_saturation": False,
        "max_p95_ms": 10000.0,
        "max_error_rate": 5.0,
    },
    "baseline": {
        "concurrency_levels": [1, 2, 4],
        "rounds": 1,
        "cache_modes": ["cold", "warm"],
        "duration_seconds": 0,
        "stop_on_saturation": True,
        "max_p95_ms": 10000.0,
        "max_error_rate": 5.0,
    },
    "stress": {
        "concurrency_levels": [1, 2, 4, 8, 16],
        "rounds": 3,
        "cache_modes": ["cold", "warm"],
        "duration_seconds": 0,
        "stop_on_saturation": True,
        "max_p95_ms": 15000.0,
        "max_error_rate": 10.0,
    },
    "soak": {
        "concurrency_levels": [4],
        "rounds": 1,
        "cache_modes": ["warm"],
        "duration_seconds": 300,
        "stop_on_saturation": True,
        "max_p95_ms": 15000.0,
        "max_error_rate": 10.0,
    },
    "breaker": {
        "concurrency_levels": [1, 2, 4, 8, 16, 32, 64],
        "rounds": 3,
        "cache_modes": ["cold", "warm"],
        "duration_seconds": 0,
        "stop_on_saturation": False,
        "max_p95_ms": 30000.0,
        "max_error_rate": 25.0,
    },
}


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


def percentile(valores, percentil):
    if not valores:
        return None
    ordenados = sorted(float(valor) for valor in valores)
    if len(ordenados) == 1:
        return ordenados[0]
    posicao = (len(ordenados) - 1) * (percentil / 100.0)
    baixo = int(posicao)
    alto = min(baixo + 1, len(ordenados) - 1)
    fracao = posicao - baixo
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * fracao


def _media(valores):
    return sum(valores) / len(valores) if valores else None


def _round_or_none(valor, casas=3):
    return round(valor, casas) if valor is not None else None


def summarizar_registros(records, group_fields, max_p95_ms, max_error_rate):
    grupos = {}
    for record in records:
        chave = tuple(record[field] for field in group_fields)
        grupos.setdefault(chave, []).append(record)

    linhas = []
    for chave, itens in sorted(grupos.items(), key=lambda item: item[0]):
        sucessos = [item for item in itens if item["status"] == "OK"]
        erros = len(itens) - len(sucessos)
        latencias = [float(item["latencia_ms"]) for item in sucessos]
        inicio = min(float(item["started_epoch"]) for item in itens)
        fim = max(float(item["ended_epoch"]) for item in itens)
        duracao_s = max(fim - inicio, 0.001)
        p95 = percentile(latencias, 95)
        error_rate = (erros / len(itens)) * 100.0 if itens else 0.0

        linha = {field: chave[indice] for indice, field in enumerate(group_fields)}
        linha.update(
            {
                "requests_total": len(itens),
                "requests_ok": len(sucessos),
                "requests_erro": erros,
                "error_rate_percent": round(error_rate, 3),
                "duration_s": round(duracao_s, 3),
                "qps": round(len(itens) / duracao_s, 3),
                "lat_min_ms": _round_or_none(min(latencias) if latencias else None),
                "lat_avg_ms": _round_or_none(_media(latencias)),
                "lat_p50_ms": _round_or_none(percentile(latencias, 50)),
                "lat_p90_ms": _round_or_none(percentile(latencias, 90)),
                "lat_p95_ms": _round_or_none(p95),
                "lat_p99_ms": _round_or_none(percentile(latencias, 99)),
                "lat_max_ms": _round_or_none(max(latencias) if latencias else None),
                "linhas_retornadas_total": sum(int(item["linhas_retornadas"]) for item in sucessos),
                "bytes_retornados_total": sum(int(item["bytes_retornados"]) for item in sucessos),
                "saturado": bool(error_rate >= max_error_rate or (p95 is not None and p95 >= max_p95_ms)),
            }
        )
        linhas.append(linha)
    return linhas


def parse_int_list(texto):
    valores = []
    for parte in texto.split(","):
        parte = parte.strip()
        if parte:
            valores.append(int(parte))
    if not valores:
        raise ValueError("Lista de concorrencia vazia.")
    return valores


def cache_modes_from_arg(valor, default_modes):
    if valor is None:
        return list(default_modes)
    if valor == "both":
        return ["cold", "warm"]
    return [valor]


def build_work_items(queries, rounds, cache_modes, seed, concurrency, round_offset=0):
    items = []
    for round_index in range(round_offset + 1, round_offset + rounds + 1):
        for cache_mode in cache_modes:
            for query in queries:
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


class DockerSampler:
    def __init__(self, enabled, interval_seconds, containers):
        self.enabled = enabled
        self.interval_seconds = interval_seconds
        self.containers = list(containers)
        self.rows = []
        self._stop_event = threading.Event()
        self._thread = None
        self.current_concurrency = None

    def set_concurrency(self, concurrency):
        self.current_concurrency = concurrency

    def start(self):
        if not self.enabled:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.enabled:
            return
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(self.interval_seconds + 1, 2))

    def _run(self):
        while not self._stop_event.is_set():
            self.rows.extend(coletar_docker_stats(self.containers, self.current_concurrency))
            self._stop_event.wait(self.interval_seconds)


def coletar_docker_stats(containers, concurrency=None):
    timestamp = datetime.now().isoformat(timespec="seconds")
    cmd = [
        "docker",
        "stats",
        "--no-stream",
        "--format",
        "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}",
        *containers,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    except Exception as exc:
        return [
            {
                "timestamp": timestamp,
                "concurrency": concurrency,
                "container": "docker",
                "status": "ERRO",
                "erro": str(exc),
            }
        ]

    if result.returncode != 0:
        return [
            {
                "timestamp": timestamp,
                "concurrency": concurrency,
                "container": "docker",
                "status": "ERRO",
                "erro": result.stderr.strip(),
            }
        ]

    rows = []
    for line in result.stdout.splitlines():
        partes = line.split(",", 5)
        if len(partes) != 6:
            continue
        container, cpu, mem_usage, mem_percent, net_io, block_io = partes
        rows.append(
            {
                "timestamp": timestamp,
                "concurrency": concurrency,
                "container": container,
                "status": "OK",
                "cpu_percent": cpu.replace("%", "").strip(),
                "mem_usage": mem_usage.strip(),
                "mem_percent": mem_percent.replace("%", "").strip(),
                "net_io": net_io.strip(),
                "block_io": block_io.strip(),
                "erro": "",
            }
        )
    return rows


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def primeiro_ponto_saturacao(summary_by_concurrency):
    for row in sorted(summary_by_concurrency, key=lambda item: int(item["concurrency"])):
        if row.get("saturado"):
            return row
    return None


RAW_FIELDS = [
    "profile",
    "capacity_scenario",
    "concurrency",
    "round",
    "cache_mode",
    "scenario",
    "query_id",
    "query_name",
    "query_file",
    "status",
    "latencia_ms",
    "linhas_retornadas",
    "bytes_retornados",
    "started_at",
    "ended_at",
    "started_epoch",
    "ended_epoch",
    "erro",
]

SUMMARY_CONCURRENCY_FIELDS = [
    "profile",
    "capacity_scenario",
    "concurrency",
    "requests_total",
    "requests_ok",
    "requests_erro",
    "error_rate_percent",
    "duration_s",
    "qps",
    "lat_min_ms",
    "lat_avg_ms",
    "lat_p50_ms",
    "lat_p90_ms",
    "lat_p95_ms",
    "lat_p99_ms",
    "lat_max_ms",
    "linhas_retornadas_total",
    "bytes_retornados_total",
    "saturado",
]

SUMMARY_QUERY_FIELDS = [
    "profile",
    "capacity_scenario",
    "scenario",
    "query_id",
    "cache_mode",
    "requests_total",
    "requests_ok",
    "requests_erro",
    "error_rate_percent",
    "duration_s",
    "qps",
    "lat_min_ms",
    "lat_avg_ms",
    "lat_p50_ms",
    "lat_p90_ms",
    "lat_p95_ms",
    "lat_p99_ms",
    "lat_max_ms",
    "linhas_retornadas_total",
    "bytes_retornados_total",
    "saturado",
]

DOCKER_FIELDS = [
    "timestamp",
    "concurrency",
    "container",
    "status",
    "cpu_percent",
    "mem_usage",
    "mem_percent",
    "net_io",
    "block_io",
    "erro",
]

DRUID_SEGMENT_FIELDS = [
    "datasource",
    "segmentos",
    "linhas",
    "tamanho_bytes",
]

CACHE_GAIN_FIELDS = [
    "profile",
    "capacity_scenario",
    "scenario",
    "query_id",
    "requests_cold",
    "requests_warm",
    "cold_avg_ms",
    "warm_avg_ms",
    "avg_gain_percent",
    "cold_p95_ms",
    "warm_p95_ms",
    "p95_gain_percent",
    "cold_error_rate_percent",
    "warm_error_rate_percent",
]


def _percent_gain(cold, warm):
    try:
        cold = float(cold)
        warm = float(warm)
    except (TypeError, ValueError):
        return None
    if cold <= 0:
        return None
    return round(((cold - warm) / cold) * 100.0, 3)


def calcular_ganho_cache(summary_by_query):
    grupos = {}
    for row in summary_by_query:
        chave = (
            row.get("profile"),
            row.get("capacity_scenario"),
            row.get("scenario"),
            row.get("query_id"),
        )
        grupos.setdefault(chave, {})[row.get("cache_mode")] = row

    ganhos = []
    for chave, por_cache in sorted(grupos.items(), key=lambda item: item[0]):
        cold = por_cache.get("cold")
        warm = por_cache.get("warm")
        if not cold or not warm:
            continue
        ganhos.append(
            {
                "profile": chave[0],
                "capacity_scenario": chave[1],
                "scenario": chave[2],
                "query_id": chave[3],
                "requests_cold": cold.get("requests_total"),
                "requests_warm": warm.get("requests_total"),
                "cold_avg_ms": cold.get("lat_avg_ms"),
                "warm_avg_ms": warm.get("lat_avg_ms"),
                "avg_gain_percent": _percent_gain(cold.get("lat_avg_ms"), warm.get("lat_avg_ms")),
                "cold_p95_ms": cold.get("lat_p95_ms"),
                "warm_p95_ms": warm.get("lat_p95_ms"),
                "p95_gain_percent": _percent_gain(cold.get("lat_p95_ms"), warm.get("lat_p95_ms")),
                "cold_error_rate_percent": cold.get("error_rate_percent"),
                "warm_error_rate_percent": warm.get("error_rate_percent"),
            }
        )
    return ganhos


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


def salvar_resultados(
    out_dir,
    records,
    docker_rows,
    config,
    max_p95_ms,
    max_error_rate,
    druid_segments=None,
    loadstatus=None,
):
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_by_concurrency = summarizar_registros(
        records,
        ["profile", "capacity_scenario", "concurrency"],
        max_p95_ms,
        max_error_rate,
    )
    summary_by_query = summarizar_registros(
        records,
        ["profile", "capacity_scenario", "scenario", "query_id", "cache_mode"],
        max_p95_ms,
        max_error_rate,
    )
    errors = [record for record in records if record["status"] != "OK"]
    cache_gain_by_query = calcular_ganho_cache(summary_by_query)

    write_csv(out_dir / "raw_requests.csv", records, RAW_FIELDS)
    write_csv(out_dir / "summary_by_concurrency.csv", summary_by_concurrency, SUMMARY_CONCURRENCY_FIELDS)
    write_csv(out_dir / "summary_by_query.csv", summary_by_query, SUMMARY_QUERY_FIELDS)
    for cache_mode in ("cold", "warm"):
        cache_records = [record for record in records if record.get("cache_mode") == cache_mode]
        cache_summary_concurrency = summarizar_registros(
            cache_records,
            ["profile", "capacity_scenario", "concurrency"],
            max_p95_ms,
            max_error_rate,
        )
        cache_summary_query = summarizar_registros(
            cache_records,
            ["profile", "capacity_scenario", "scenario", "query_id", "cache_mode"],
            max_p95_ms,
            max_error_rate,
        )
        write_csv(out_dir / f"raw_requests_{cache_mode}.csv", cache_records, RAW_FIELDS)
        write_csv(
            out_dir / f"summary_by_concurrency_{cache_mode}.csv",
            cache_summary_concurrency,
            SUMMARY_CONCURRENCY_FIELDS,
        )
        write_csv(
            out_dir / f"summary_by_query_{cache_mode}.csv",
            cache_summary_query,
            SUMMARY_QUERY_FIELDS,
        )
    write_csv(out_dir / "cache_gain_by_query.csv", cache_gain_by_query, CACHE_GAIN_FIELDS)
    write_csv(out_dir / "docker_stats.csv", docker_rows, DOCKER_FIELDS)
    write_csv(out_dir / "druid_segments.csv", druid_segments or [], DRUID_SEGMENT_FIELDS)
    write_csv(out_dir / "errors.csv", errors, RAW_FIELDS)

    config_path = out_dir / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=True, indent=2), encoding="utf-8")
    (out_dir / "loadstatus.json").write_text(
        json.dumps(loadstatus or {}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    escrever_readme(out_dir, records, summary_by_concurrency, config, cache_gain_by_query)
    return {
        "summary_by_concurrency": summary_by_concurrency,
        "summary_by_query": summary_by_query,
        "cache_gain_by_query": cache_gain_by_query,
        "errors": errors,
    }


def escrever_readme(out_dir, records, summary_by_concurrency, config, cache_gain_by_query=None):
    total = len(records)
    erros = sum(1 for record in records if record["status"] != "OK")
    saturacao = primeiro_ponto_saturacao(summary_by_concurrency)
    ganhos_validos = [
        float(row["p95_gain_percent"])
        for row in (cache_gain_by_query or [])
        if row.get("p95_gain_percent") is not None
    ]
    linhas = [
        "# Druid Benchmark Results",
        "",
        f"- Profile: `{config['profile']}`",
        f"- Capacity scenario: `{config.get('capacity_scenario', 'manual')}`",
        f"- Broker URL: `{config['broker_url']}`",
        f"- Total requests: `{total}`",
        f"- Errors: `{erros}`",
        f"- Query count: `{len(config['queries'])}`",
        f"- Concurrency levels: `{config['concurrency_levels']}`",
        f"- Cache modes: `{config['cache_modes']}`",
    ]
    if saturacao:
        linhas.append(
            "- First saturation: concurrency `{}` with p95 `{}` ms and error rate `{}%`".format(
                saturacao["concurrency"],
                saturacao["lat_p95_ms"],
                saturacao["error_rate_percent"],
            )
        )
    else:
        linhas.append("- First saturation: not detected")
    if ganhos_validos:
        linhas.append(f"- Average p95 cache gain: `{round(sum(ganhos_validos) / len(ganhos_validos), 3)}%`")

    linhas.extend(
        [
            "",
            "## Files",
            "",
            "- `raw_requests.csv`",
            "- `raw_requests_cold.csv`",
            "- `raw_requests_warm.csv`",
            "- `summary_by_query.csv`",
            "- `summary_by_query_cold.csv`",
            "- `summary_by_query_warm.csv`",
            "- `summary_by_concurrency.csv`",
            "- `summary_by_concurrency_cold.csv`",
            "- `summary_by_concurrency_warm.csv`",
            "- `cache_gain_by_query.csv`",
            "- `docker_stats.csv`",
            "- `druid_segments.csv`",
            "- `loadstatus.json`",
            "- `errors.csv`",
            "- `config.json`",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def healthcheck(broker_url, timeout):
    try:
        executar_sql(broker_url, "SELECT 1 AS ok", "cold", timeout)
    except Exception as exc:
        raise RuntimeError(f"Nao foi possivel consultar o Druid Broker em {broker_url}: {exc}") from exc


def resolver_out_dir(out_root, run_id):
    if run_id:
        return out_root / run_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return out_root / timestamp


def parse_args():
    parser = argparse.ArgumentParser(description="Executa benchmark de carga contra o Druid SQL.")
    parser.add_argument("--profile", choices=sorted(PROFILE_CONFIGS), default="smoke")
    parser.add_argument("--broker-url", default=DEFAULT_BROKER_URL)
    parser.add_argument("--coordinator-url", default=DEFAULT_COORDINATOR_URL)
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--run-id")
    parser.add_argument("--capacity-scenario", default=os.getenv("DRUID_CAPACITY_SCENARIO", "manual"))
    parser.add_argument("--concurrency", help="Lista separada por virgula. Ex: 1,2,4")
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--cache-mode", choices=("cold", "warm", "both"))
    parser.add_argument("--duration-seconds", type=int)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--collect-docker", action="store_true")
    parser.add_argument("--docker-interval", type=float, default=2.0)
    parser.add_argument("--containers", default=",".join(DEFAULT_CONTAINERS))
    parser.add_argument("--max-p95-ms", type=float)
    parser.add_argument("--max-error-rate", type=float)
    parser.add_argument("--no-stop-on-saturation", action="store_true")
    parser.add_argument("--fail-on-query-error", action="store_true")
    parser.add_argument("--confirm-breaker", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    profile_config = dict(PROFILE_CONFIGS[args.profile])
    if args.profile == "breaker" and not args.confirm_breaker:
        print("O perfil breaker exige --confirm-breaker.", file=sys.stderr)
        return 2

    concurrency_levels = (
        parse_int_list(args.concurrency)
        if args.concurrency
        else list(profile_config["concurrency_levels"])
    )
    rounds = args.rounds if args.rounds is not None else int(profile_config["rounds"])
    cache_modes = cache_modes_from_arg(args.cache_mode, profile_config["cache_modes"])
    duration_seconds = (
        args.duration_seconds
        if args.duration_seconds is not None
        else int(profile_config["duration_seconds"])
    )
    max_p95_ms = args.max_p95_ms if args.max_p95_ms is not None else float(profile_config["max_p95_ms"])
    max_error_rate = (
        args.max_error_rate if args.max_error_rate is not None else float(profile_config["max_error_rate"])
    )
    stop_on_saturation = bool(profile_config["stop_on_saturation"]) and not args.no_stop_on_saturation
    containers = [item.strip() for item in args.containers.split(",") if item.strip()]

    queries = carregar_queries(args.sql_dir)
    if not queries:
        print(f"Nenhum SQL encontrado em {args.sql_dir}.", file=sys.stderr)
        return 1

    try:
        healthcheck(args.broker_url, args.timeout)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    out_dir = resolver_out_dir(args.out_root, args.run_id)
    config = {
        "profile": args.profile,
        "capacity_scenario": args.capacity_scenario,
        "broker_url": args.broker_url,
        "coordinator_url": args.coordinator_url,
        "sql_dir": str(args.sql_dir),
        "out_dir": str(out_dir),
        "concurrency_levels": concurrency_levels,
        "rounds": rounds,
        "cache_modes": cache_modes,
        "duration_seconds": duration_seconds,
        "timeout": args.timeout,
        "seed": args.seed,
        "collect_docker": args.collect_docker,
        "docker_interval": args.docker_interval,
        "containers": containers,
        "max_p95_ms": max_p95_ms,
        "max_error_rate": max_error_rate,
        "stop_on_saturation": stop_on_saturation,
        "fail_on_query_error": args.fail_on_query_error,
        "queries": [query.query_id for query in queries],
    }
    druid_segments = coletar_druid_segments(args.broker_url, args.timeout)
    try:
        loadstatus = fetch_json(f"{args.coordinator_url.rstrip('/')}/druid/coordinator/v1/loadstatus", args.timeout)
    except Exception as exc:
        loadstatus = {"erro": str(exc)}

    sampler = DockerSampler(args.collect_docker, args.docker_interval, containers)
    records = []
    sampler.start()
    try:
        for concurrency in concurrency_levels:
            sampler.set_concurrency(concurrency)
            print(f"Executando profile={args.profile} concurrency={concurrency}")
            if duration_seconds > 0:
                deadline = time.perf_counter() + duration_seconds
                round_offset = 0
                level_records = []
                while time.perf_counter() < deadline:
                    items = build_work_items(
                        queries,
                        1,
                        cache_modes,
                        args.seed,
                        concurrency,
                        round_offset=round_offset,
                    )
                    level_records.extend(
                        executar_items_capacity(
                            items,
                            args.profile,
                            args.capacity_scenario,
                            concurrency,
                            args.broker_url,
                            args.timeout,
                        )
                    )
                    round_offset += 1
            else:
                items = build_work_items(queries, rounds, cache_modes, args.seed, concurrency)
                level_records = executar_items_capacity(
                    items,
                    args.profile,
                    args.capacity_scenario,
                    concurrency,
                    args.broker_url,
                    args.timeout,
                )

            records.extend(level_records)
            level_summary = summarizar_registros(
                level_records,
                ["profile", "capacity_scenario", "concurrency"],
                max_p95_ms,
                max_error_rate,
            )
            if level_summary:
                resumo = level_summary[0]
                print(
                    "  requests={requests_total} p95={lat_p95_ms}ms "
                    "qps={qps} errors={requests_erro} saturated={saturado}".format(**resumo)
                )
                if stop_on_saturation and resumo["saturado"]:
                    print("  Saturacao detectada; interrompendo rampa por seguranca.")
                    break
    finally:
        sampler.stop()

    resultado = salvar_resultados(
        out_dir,
        records,
        sampler.rows,
        config,
        max_p95_ms,
        max_error_rate,
        druid_segments=druid_segments,
        loadstatus=loadstatus,
    )
    print(f"Resultados salvos em {out_dir}")
    return 3 if args.fail_on_query_error and resultado["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
