"""
Consolida resultados da matriz de capacidade do Druid.

Entrada esperada:
data/results/performance/druid_capacity/<timestamp>/<scenario>/*.csv
"""
import argparse
import csv
import json
import sys
from pathlib import Path

# Scripts chamados por caminho precisam enxergar o pacote do projeto.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from scripts.performance.capacity_metadata import DEFAULT_MATRIX_ROOT  # noqa: E402


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default=0):
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def scenario_dirs(matrix_dir):
    return sorted(path for path in matrix_dir.iterdir() if path.is_dir())


def load_config(scenario_dir):
    path = scenario_dir / "config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_capacity_comparison(matrix_dir):
    rows = []
    for scenario_dir in scenario_dirs(matrix_dir):
        config = load_config(scenario_dir)
        for row in read_csv(scenario_dir / "summary_by_concurrency.csv"):
            rows.append(
                {
                    "scenario": scenario_dir.name,
                    "profile": row.get("profile", config.get("profile", "")),
                    "concurrency": row.get("concurrency"),
                    "requests_total": row.get("requests_total"),
                    "requests_erro": row.get("requests_erro"),
                    "error_rate_percent": row.get("error_rate_percent"),
                    "qps": row.get("qps"),
                    "lat_avg_ms": row.get("lat_avg_ms"),
                    "lat_p50_ms": row.get("lat_p50_ms"),
                    "lat_p90_ms": row.get("lat_p90_ms"),
                    "lat_p95_ms": row.get("lat_p95_ms"),
                    "lat_p99_ms": row.get("lat_p99_ms"),
                    "lat_max_ms": row.get("lat_max_ms"),
                    "bytes_retornados_total": row.get("bytes_retornados_total"),
                    "saturado": row.get("saturado"),
                }
            )
    return rows


def build_query_hotspots(matrix_dir, limit=50):
    rows = []
    for scenario_dir in scenario_dirs(matrix_dir):
        for row in read_csv(scenario_dir / "summary_by_query.csv"):
            rows.append(
                {
                    "scenario": scenario_dir.name,
                    "profile": row.get("profile"),
                    "query_id": row.get("query_id"),
                    "cache_mode": row.get("cache_mode"),
                    "requests_total": row.get("requests_total"),
                    "requests_erro": row.get("requests_erro"),
                    "error_rate_percent": row.get("error_rate_percent"),
                    "lat_avg_ms": row.get("lat_avg_ms"),
                    "lat_p95_ms": row.get("lat_p95_ms"),
                    "lat_p99_ms": row.get("lat_p99_ms"),
                    "qps": row.get("qps"),
                }
            )
    rows.sort(key=lambda item: parse_float(item.get("lat_p95_ms")), reverse=True)
    return rows[:limit]


def build_cache_gain(matrix_dir):
    rows = []
    for scenario_dir in scenario_dirs(matrix_dir):
        for row in read_csv(scenario_dir / "cache_gain_by_query.csv"):
            item = {
                "capacity_scenario_dir": scenario_dir.name,
                "profile": row.get("profile"),
                "capacity_scenario": row.get("capacity_scenario"),
                "query_scenario": row.get("scenario"),
                "query_id": row.get("query_id"),
                "requests_cold": row.get("requests_cold"),
                "requests_warm": row.get("requests_warm"),
                "cold_avg_ms": row.get("cold_avg_ms"),
                "warm_avg_ms": row.get("warm_avg_ms"),
                "avg_gain_percent": row.get("avg_gain_percent"),
                "cold_p95_ms": row.get("cold_p95_ms"),
                "warm_p95_ms": row.get("warm_p95_ms"),
                "p95_gain_percent": row.get("p95_gain_percent"),
                "cold_error_rate_percent": row.get("cold_error_rate_percent"),
                "warm_error_rate_percent": row.get("warm_error_rate_percent"),
            }
            rows.append(item)
    rows.sort(key=lambda item: parse_float(item.get("p95_gain_percent")), reverse=True)
    return rows


def build_docker_peaks(matrix_dir):
    groups = {}
    for scenario_dir in scenario_dirs(matrix_dir):
        for row in read_csv(scenario_dir / "docker_stats.csv"):
            if row.get("status") != "OK":
                continue
            key = (scenario_dir.name, row.get("container"))
            groups.setdefault(key, {"cpu": [], "mem": []})
            groups[key]["cpu"].append(parse_float(row.get("cpu_percent")))
            groups[key]["mem"].append(parse_float(row.get("mem_percent")))

    output = []
    for (scenario, container), values in sorted(groups.items()):
        cpu_values = values["cpu"]
        mem_values = values["mem"]
        output.append(
            {
                "scenario": scenario,
                "container": container,
                "samples": len(cpu_values),
                "cpu_avg_percent": round(sum(cpu_values) / len(cpu_values), 3) if cpu_values else "",
                "cpu_max_percent": round(max(cpu_values), 3) if cpu_values else "",
                "mem_avg_percent": round(sum(mem_values) / len(mem_values), 3) if mem_values else "",
                "mem_max_percent": round(max(mem_values), 3) if mem_values else "",
            }
        )
    return output


def write_markdown(matrix_dir, capacity_rows, docker_rows, cache_rows):
    lines = [
        "# Comparacao de Capacidade Druid",
        "",
        f"- Matrix dir: `{matrix_dir}`",
        f"- Cenários: `{len(scenario_dirs(matrix_dir))}`",
        "",
        "## Capacidade por concorrencia",
        "",
        "| scenario | concurrency | qps | p95 ms | p99 ms | errors | saturated |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in capacity_rows:
        lines.append(
            "| {scenario} | {concurrency} | {qps} | {lat_p95_ms} | {lat_p99_ms} | {requests_erro} | {saturado} |".format(
                **row
            )
        )

    lines.extend(["", "## Picos Docker", "", "| scenario | container | cpu max % | mem max % |", "| --- | --- | ---: | ---: |"])
    for row in docker_rows:
        lines.append(
            "| {scenario} | {container} | {cpu_max_percent} | {mem_max_percent} |".format(**row)
        )

    top_cache = cache_rows[:10]
    lines.extend(["", "## Maiores ganhos warm-start por p95", "", "| scenario | query | ganho p95 % | cold p95 | warm p95 |", "| --- | --- | ---: | ---: | ---: |"])
    for row in top_cache:
        lines.append(
            "| {capacity_scenario_dir} | {query_id} | {p95_gain_percent} | {cold_p95_ms} | {warm_p95_ms} |".format(
                **row
            )
        )

    (matrix_dir / "capacity_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def consolidate(matrix_dir):
    capacity_rows = build_capacity_comparison(matrix_dir)
    hotspot_rows = build_query_hotspots(matrix_dir)
    docker_rows = build_docker_peaks(matrix_dir)
    cache_rows = build_cache_gain(matrix_dir)

    write_csv(
        matrix_dir / "capacity_comparison.csv",
        capacity_rows,
        [
            "scenario",
            "profile",
            "concurrency",
            "requests_total",
            "requests_erro",
            "error_rate_percent",
            "qps",
            "lat_avg_ms",
            "lat_p50_ms",
            "lat_p90_ms",
            "lat_p95_ms",
            "lat_p99_ms",
            "lat_max_ms",
            "bytes_retornados_total",
            "saturado",
        ],
    )
    write_csv(
        matrix_dir / "query_hotspots.csv",
        hotspot_rows,
        [
            "scenario",
            "profile",
            "query_id",
            "cache_mode",
            "requests_total",
            "requests_erro",
            "error_rate_percent",
            "lat_avg_ms",
            "lat_p95_ms",
            "lat_p99_ms",
            "qps",
        ],
    )
    write_csv(
        matrix_dir / "docker_peaks.csv",
        docker_rows,
        [
            "scenario",
            "container",
            "samples",
            "cpu_avg_percent",
            "cpu_max_percent",
            "mem_avg_percent",
            "mem_max_percent",
        ],
    )
    write_csv(
        matrix_dir / "cache_gain_by_query.csv",
        cache_rows,
        [
            "capacity_scenario_dir",
            "profile",
            "capacity_scenario",
            "query_scenario",
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
        ],
    )
    write_markdown(matrix_dir, capacity_rows, docker_rows, cache_rows)
    return {
        "capacity": capacity_rows,
        "hotspots": hotspot_rows,
        "docker": docker_rows,
        "cache": cache_rows,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Consolida benchmarks de cenarios de capacidade.")
    parser.add_argument("--matrix-dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.matrix_dir.exists():
        print(f"Diretorio nao encontrado: {args.matrix_dir}")
        return 1
    result = consolidate(args.matrix_dir)
    print(
        "Comparacao consolidada: "
        f"{len(result['capacity'])} linhas de capacidade, "
        f"{len(result['hotspots'])} hotspots, "
        f"{len(result['docker'])} picos docker."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
