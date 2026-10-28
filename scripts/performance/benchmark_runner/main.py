import argparse
import csv
import json
import os
from pathlib import Path
from config.constants import PROJECT_ROOT

from .docker_sampler import DockerSampler, coletar_docker_stats
from .stats import summarizar_registros, primeiro_ponto_saturacao, calcular_ganho_cache
from .executor import carregar_queries, build_work_items, executar_items, executar_items_capacity, coletar_druid_segments, healthcheck

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

def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

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
