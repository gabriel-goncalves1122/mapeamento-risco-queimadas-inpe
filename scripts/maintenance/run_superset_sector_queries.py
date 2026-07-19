"""
Executa as consultas setoriais de Superset contra o Broker do Apache Druid.

O objetivo e validar rapidamente os datasets virtuais antes da apresentacao e
salvar previas em CSV. A fato agregada de eventos e permitida; fatos antigas e
eventos batch legados continuam bloqueados.
"""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from src.config.constants import PROJECT_ROOT


DEFAULT_SQL_DIR = PROJECT_ROOT / "scripts" / "sql" / "superset"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "results" / "superset_sectors"
DEFAULT_BROKER_URL = "http://localhost:8082/druid/v2/sql"
FORBIDDEN_REFERENCES = (
    "fato_focos_incendio",
    "fogo_eventos_stdbscan",
    "dim_rel_",
    "queimadas_focos_calor",
)


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

    join_hospital_amplo = (
        "from fato_eventos_incendio" in normalizado
        and "join dim_hospitais_cnes" in normalizado
    )
    if join_hospital_amplo:
        raise ValueError(
            f"{caminho} faz join amplo fato_eventos_incendio -> dim_hospitais_cnes; "
            "agregue por fk_hospital primeiro ou use lookup limitado."
        )


def aplicar_limite_previa(statement, limite):
    if limite is None or limite <= 0:
        return statement
    return f"{statement.rstrip(';')} LIMIT {int(limite)}"


def executar_sql(url, query):
    payload = json.dumps({"query": query}).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Erro HTTP {exc.code} ao executar SQL: {detalhe}") from exc


def salvar_csv(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not linhas:
        caminho.write_text("", encoding="utf-8")
        return

    campos = list(linhas[0].keys())
    for linha in linhas[1:]:
        for campo in linha:
            if campo not in campos:
                campos.append(campo)

    with caminho.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def nome_saida(sql_file, statement_index):
    nome = re.sub(r"[^A-Za-z0-9_.-]", "_", sql_file.stem)
    if statement_index == 1:
        return f"{nome}.csv"
    return f"{nome}_{statement_index:02d}.csv"


def healthcheck(url):
    try:
        executar_sql(url, "SELECT 1 AS ok")
    except HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Druid Broker respondeu HTTP {exc.code}: {detalhe}") from exc
    except URLError as exc:
        raise RuntimeError(f"Nao foi possivel conectar ao Druid Broker em {url}: {exc}") from exc


def salvar_resumos(out_dir, resultados):
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "summary.json"
    md_path = out_dir / "README.md"

    json_path.write_text(
        json.dumps(resultados, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    linhas = [
        "# Superset Sector Query Results",
        "",
        "| status | setor | consulta | linhas | tempo_ms | saida |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for item in resultados:
        linhas.append(
            "| {status} | {setor} | {consulta} | {linhas} | {tempo_ms} | {saida} |".format(
                status=item["status"],
                setor=item["setor"],
                consulta=item["consulta"],
                linhas=item.get("linhas", 0),
                tempo_ms=item.get("tempo_ms", 0),
                saida=item.get("saida", ""),
            )
        )
    md_path.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def descobrir_sqls(sql_dir):
    return [
        path
        for path in sorted(sql_dir.rglob("*.sql"))
        if "agents.md" not in path.parts
    ]


def main():
    parser = argparse.ArgumentParser(description="Executa SQLs setoriais do Superset no Druid.")
    parser.add_argument("--broker-url", default=DEFAULT_BROKER_URL)
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--preview-limit", type=int, default=500)
    parser.add_argument("--full", action="store_true", help="Executa as consultas sem wrapper de LIMIT.")
    args = parser.parse_args()

    sql_files = descobrir_sqls(args.sql_dir)
    if not sql_files:
        print(f"Nenhum SQL encontrado em {args.sql_dir}", file=sys.stderr)
        return 1

    try:
        healthcheck(args.broker_url)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    resultados = []
    houve_erro = False
    limite = None if args.full else args.preview_limit

    for sql_file in sql_files:
        texto = sql_file.read_text(encoding="utf-8")
        statements = split_sql(strip_comments(texto))
        setor = sql_file.parent.name
        print(f"Executando {sql_file.relative_to(args.sql_dir)}: {len(statements)} consulta(s)")

        for indice, statement in enumerate(statements, start=1):
            saida = args.out_dir / setor / nome_saida(sql_file, indice)
            inicio = time.time()
            try:
                validar_statement(statement, sql_file)
                linhas = executar_sql(args.broker_url, aplicar_limite_previa(statement, limite))
                tempo_ms = round((time.time() - inicio) * 1000, 2)
                salvar_csv(saida, linhas)
                resultados.append(
                    {
                        "status": "OK",
                        "setor": setor,
                        "consulta": sql_file.stem,
                        "linhas": len(linhas),
                        "tempo_ms": tempo_ms,
                        "saida": str(saida.relative_to(PROJECT_ROOT)),
                    }
                )
            except Exception as exc:
                houve_erro = True
                tempo_ms = round((time.time() - inicio) * 1000, 2)
                resultados.append(
                    {
                        "status": "ERRO",
                        "setor": setor,
                        "consulta": sql_file.stem,
                        "linhas": 0,
                        "tempo_ms": tempo_ms,
                        "saida": str(saida.relative_to(PROJECT_ROOT)),
                        "erro": str(exc),
                    }
                )
                print(f"Erro em {sql_file}: {exc}", file=sys.stderr)

    salvar_resumos(args.out_dir, resultados)
    print(f"Resultados salvos em {args.out_dir}")
    return 3 if houve_erro else 0


if __name__ == "__main__":
    raise SystemExit(main())
