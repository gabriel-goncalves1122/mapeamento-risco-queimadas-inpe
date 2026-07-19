"""
Executa os SQLs versionados de validacao contra o Broker do Apache Druid.

Cada consulta critica deve retornar as colunas severity, check_name e failures.
Resultados sao salvos em CSV para auditoria em data/results/druid_validation.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from src.config.constants import PROJECT_ROOT


DEFAULT_SQL_DIR = PROJECT_ROOT / "scripts" / "sql" / "validation"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "results" / "druid_validation"
DEFAULT_BROKER_URL = "http://localhost:8082/druid/v2/sql"


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


def strip_comments(texto):
    linhas = []
    for linha in texto.splitlines():
        if linha.strip().startswith("--"):
            continue
        linhas.append(linha)
    return "\n".join(linhas)


def executar_sql(url, query):
    payload = json.dumps({"query": query}).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Erro HTTP {exc.code} ao executar SQL: {detalhe}") from exc
    except URLError as exc:
        raise RuntimeError(f"Nao foi possivel conectar ao Druid Broker em {url}: {exc}") from exc


def salvar_resultado(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not linhas:
        caminho.write_text("", encoding="utf-8")
        return

    campos = sorted({campo for linha in linhas for campo in linha.keys()})
    with caminho.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def falhas_criticas(linhas):
    falhas = []
    for linha in linhas:
        severity = str(linha.get("severity", "")).upper()
        failures = linha.get("failures", 0)
        try:
            failures = float(failures or 0)
        except (TypeError, ValueError):
            failures = 0
        if severity == "CRITICAL" and failures > 0:
            falhas.append(linha)
    return falhas


def nome_saida(sql_file, indice):
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", sql_file.stem)
    return f"{base}_{indice:02d}.csv"


def main():
    parser = argparse.ArgumentParser(description="Executa validacoes SQL no Druid.")
    parser.add_argument("--broker-url", default=DEFAULT_BROKER_URL)
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--include-events",
        action="store_true",
        help="Inclui validacoes da fato_eventos_incendio, que exigem supervisor e dados ja ingeridos.",
    )
    args = parser.parse_args()

    sql_files = sorted(args.sql_dir.glob("*.sql"))
    if not args.include_events:
        sql_files = [path for path in sql_files if "fato_eventos_incendio" not in path.name]
    if not sql_files:
        print(f"Nenhum SQL encontrado em {args.sql_dir}", file=sys.stderr)
        return 1

    criticas = []
    for sql_file in sql_files:
        statements = split_sql(strip_comments(sql_file.read_text(encoding="utf-8")))
        print(f"Executando {sql_file.name}: {len(statements)} consulta(s)")
        for indice, statement in enumerate(statements, start=1):
            linhas = executar_sql(args.broker_url, statement)
            salvar_resultado(args.out_dir / nome_saida(sql_file, indice), linhas)
            criticas.extend(falhas_criticas(linhas))

    if criticas:
        print("Falhas criticas encontradas:")
        for falha in criticas:
            print(f"- {falha.get('check_name')}: {falha.get('failures')}")
        return 2

    print(f"Validacoes concluidas. Resultados em {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
