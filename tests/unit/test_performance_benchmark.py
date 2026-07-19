from pathlib import Path

from scripts.performance.run_druid_benchmark import (
    FORBIDDEN_REFERENCES,
    DOCKER_FIELDS,
    RAW_FIELDS,
    calcular_ganho_cache,
    carregar_queries,
    coletar_docker_stats,
    percentile,
    salvar_resultados,
    split_sql,
    strip_comments,
    summarizar_registros,
    validar_statement,
)
from scripts.performance.compare_capacity_results import consolidate
from src.config.constants import PROJECT_ROOT


SQL_DIR = PROJECT_ROOT / "scripts" / "sql" / "performance"
PROFILE_DIR = PROJECT_ROOT / "infrastructure" / "druid_profiles"
REQUIRED_METADATA = (
    "-- categoria:",
    "-- objetivo:",
    "-- datasource:",
    "-- padrao_carga:",
    "-- visualizacao:",
)


def _sample_record(status="OK", latency=100.0, start=1.0, end=1.1, concurrency=1):
    return {
        "profile": "unit",
        "capacity_scenario": "unit_capacity",
        "concurrency": concurrency,
        "round": 1,
        "cache_mode": "cold",
        "scenario": "unit_scenario",
        "query_id": "unit_scenario/query",
        "query_name": "query",
        "query_file": "scripts/sql/performance/unit.sql",
        "status": status,
        "latencia_ms": latency,
        "linhas_retornadas": 10 if status == "OK" else 0,
        "bytes_retornados": 100 if status == "OK" else 0,
        "started_at": "2026-01-01T00:00:00",
        "ended_at": "2026-01-01T00:00:01",
        "started_epoch": start,
        "ended_epoch": end,
        "erro": "" if status == "OK" else "falha simulada",
    }


def test_performance_sqls_sao_selects_com_metadados_e_sem_datasources_proibidos():
    sql_files = sorted(SQL_DIR.rglob("*.sql"))

    assert sql_files
    for sql_file in sql_files:
        texto = sql_file.read_text(encoding="utf-8")
        texto_lower = texto.lower()

        for metadata in REQUIRED_METADATA:
            assert metadata in texto_lower, f"{sql_file} sem metadado {metadata}"
        for termo in FORBIDDEN_REFERENCES:
            assert termo not in texto_lower, f"{sql_file} referencia {termo}"

        statements = split_sql(strip_comments(texto))
        assert len(statements) == 1, f"{sql_file} deve ter uma consulta por arquivo"
        validar_statement(statements[0], sql_file)


def test_carregar_queries_monta_ids_por_cenario():
    queries = carregar_queries(SQL_DIR)

    assert queries
    assert all("/" in query.query_id for query in queries)
    assert {"01_latency_simple", "05_dashboard_misto"}.issubset({query.scenario for query in queries})


def test_validar_statement_rejeita_comando_mutante_e_datasource_fora_do_escopo(tmp_path: Path):
    sql_file = tmp_path / "query.sql"

    for statement in (
        "DELETE FROM dim_hospitais_cnes",
        "SELECT COUNT(*) FROM fato_focos_incendio",
        "SELECT COUNT(*) FROM fogo_eventos_stdbscan",
        "SELECT COUNT(*) FROM dim_rel_hospital_municipio",
        "SELECT COUNT(*) FROM queimadas_focos_calor",
    ):
        try:
            validar_statement(statement, sql_file)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Statement deveria ser rejeitado: {statement}")


def test_percentile_calcula_pontos_interpolados():
    valores = [10, 20, 30, 40]

    assert percentile(valores, 50) == 25
    assert percentile(valores, 95) == 38.5
    assert percentile([7], 99) == 7
    assert percentile([], 95) is None


def test_summarizar_registros_calcula_qps_percentis_e_saturacao():
    records = [
        _sample_record(latency=100, start=1.0, end=1.1),
        _sample_record(latency=200, start=1.1, end=1.3),
        _sample_record(status="ERRO", latency=50, start=1.3, end=1.4),
    ]

    [summary] = summarizar_registros(records, ["profile", "concurrency"], 180, 20)

    assert summary["requests_total"] == 3
    assert summary["requests_ok"] == 2
    assert summary["requests_erro"] == 1
    assert summary["lat_p50_ms"] == 150
    assert summary["lat_p95_ms"] == 195
    assert summary["error_rate_percent"] == 33.333
    assert summary["qps"] > 0
    assert summary["saturado"] is True


def test_calcular_ganho_cache_compara_cold_e_warm_por_query():
    summary_rows = [
        {
            "profile": "unit",
            "capacity_scenario": "scenario_01",
            "scenario": "joins",
            "query_id": "joins/q1",
            "cache_mode": "cold",
            "requests_total": 3,
            "lat_avg_ms": 200,
            "lat_p95_ms": 400,
            "error_rate_percent": 0,
        },
        {
            "profile": "unit",
            "capacity_scenario": "scenario_01",
            "scenario": "joins",
            "query_id": "joins/q1",
            "cache_mode": "warm",
            "requests_total": 3,
            "lat_avg_ms": 100,
            "lat_p95_ms": 250,
            "error_rate_percent": 0,
        },
    ]

    [ganho] = calcular_ganho_cache(summary_rows)

    assert ganho["avg_gain_percent"] == 50
    assert ganho["p95_gain_percent"] == 37.5


def test_salvar_resultados_gera_artefatos_esperados_e_separa_cache(tmp_path: Path):
    records = [
        _sample_record(latency=100, start=1.0, end=1.1),
        {**_sample_record(latency=50, start=1.1, end=1.2), "cache_mode": "warm"},
        _sample_record(status="ERRO", latency=50, start=1.2, end=1.3),
    ]
    docker_rows = [
        {
            "timestamp": "2026-01-01T00:00:00",
            "concurrency": 1,
            "container": "broker",
            "status": "OK",
            "cpu_percent": "10.0",
            "mem_usage": "100MiB / 1GiB",
            "mem_percent": "10.0",
            "net_io": "1kB / 2kB",
            "block_io": "0B / 0B",
            "erro": "",
        }
    ]
    config = {
        "profile": "unit",
        "capacity_scenario": "unit_capacity",
        "broker_url": "http://localhost:8082/druid/v2/sql",
        "queries": ["unit_scenario/query"],
        "concurrency_levels": [1],
        "cache_modes": ["cold", "warm"],
    }

    resultado = salvar_resultados(
        tmp_path,
        records,
        docker_rows,
        config,
        1000,
        50,
        druid_segments=[{"datasource": "dim_hospitais_cnes", "segmentos": 1, "linhas": 10, "tamanho_bytes": 100}],
        loadstatus={"dim_hospitais_cnes": 100.0},
    )

    assert (tmp_path / "raw_requests.csv").exists()
    assert (tmp_path / "raw_requests_cold.csv").exists()
    assert (tmp_path / "raw_requests_warm.csv").exists()
    assert (tmp_path / "summary_by_query.csv").exists()
    assert (tmp_path / "summary_by_query_cold.csv").exists()
    assert (tmp_path / "summary_by_query_warm.csv").exists()
    assert (tmp_path / "summary_by_concurrency.csv").exists()
    assert (tmp_path / "summary_by_concurrency_cold.csv").exists()
    assert (tmp_path / "summary_by_concurrency_warm.csv").exists()
    assert (tmp_path / "cache_gain_by_query.csv").exists()
    assert (tmp_path / "docker_stats.csv").exists()
    assert (tmp_path / "druid_segments.csv").exists()
    assert (tmp_path / "loadstatus.json").exists()
    assert (tmp_path / "errors.csv").exists()
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "config.json").exists()
    assert len(resultado["errors"]) == 1
    assert set(RAW_FIELDS)
    assert set(DOCKER_FIELDS)


def test_coletar_docker_stats_parseia_saida(monkeypatch):
    class FakeResult:
        returncode = 0
        stdout = "broker,12.5%,585MiB / 1GiB,57.1%,10MB / 20MB,1GB / 2GB\n"
        stderr = ""

    def fake_run(*args, **kwargs):
        return FakeResult()

    monkeypatch.setattr("scripts.performance.run_druid_benchmark.subprocess.run", fake_run)

    [row] = coletar_docker_stats(["broker"], concurrency=4)

    assert row["container"] == "broker"
    assert row["concurrency"] == 4
    assert row["cpu_percent"] == "12.5"
    assert row["mem_percent"] == "57.1"


def test_perfis_de_capacidade_existem_e_declaram_variaveis_criticas():
    profiles = sorted(PROFILE_DIR.glob("scenario_*.env"))

    assert {path.name for path in profiles} == {
        "scenario_01_baseline.env",
        "scenario_02_balanced.env",
        "scenario_03_query_heavy.env",
    }
    for profile in profiles:
        text = profile.read_text(encoding="utf-8")
        for key in (
            "DRUID_BROKER_CPUS=",
            "DRUID_BROKER_MEMORY=",
            "DRUID_BROKER_PROCESSING_THREADS=",
            "DRUID_HISTORICAL_CPUS=",
            "DRUID_HISTORICAL_MEMORY=",
            "DRUID_HISTORICAL_PROCESSING_THREADS=",
        ):
            assert key in text


def test_compare_capacity_results_consolida_cenarios(tmp_path: Path):
    for scenario in ("scenario_01_baseline", "scenario_02_balanced"):
        scenario_dir = tmp_path / scenario
        scenario_dir.mkdir()
        (scenario_dir / "config.json").write_text('{"profile":"baseline"}', encoding="utf-8")
        (scenario_dir / "summary_by_concurrency.csv").write_text(
            "profile,capacity_scenario,concurrency,requests_total,requests_erro,error_rate_percent,qps,lat_avg_ms,lat_p50_ms,lat_p90_ms,lat_p95_ms,lat_p99_ms,lat_max_ms,bytes_retornados_total,saturado\n"
            f"baseline,{scenario},1,10,0,0,2.0,100,90,120,150,180,200,1000,False\n",
            encoding="utf-8",
        )
        (scenario_dir / "summary_by_query.csv").write_text(
            "profile,capacity_scenario,scenario,query_id,cache_mode,requests_total,requests_erro,error_rate_percent,lat_avg_ms,lat_p95_ms,lat_p99_ms,qps\n"
            f"baseline,{scenario},joins,joins/q1,cold,2,0,0,200,300,350,1.0\n",
            encoding="utf-8",
        )
        (scenario_dir / "cache_gain_by_query.csv").write_text(
            "profile,capacity_scenario,scenario,query_id,requests_cold,requests_warm,cold_avg_ms,warm_avg_ms,avg_gain_percent,cold_p95_ms,warm_p95_ms,p95_gain_percent,cold_error_rate_percent,warm_error_rate_percent\n"
            f"baseline,{scenario},joins,joins/q1,2,2,200,100,50,300,150,50,0,0\n",
            encoding="utf-8",
        )
        (scenario_dir / "docker_stats.csv").write_text(
            "timestamp,concurrency,container,status,cpu_percent,mem_usage,mem_percent,net_io,block_io,erro\n"
            "2026-01-01T00:00:00,1,broker,OK,10,100MiB / 1GiB,20,1kB / 1kB,0B / 0B,\n",
            encoding="utf-8",
        )

    result = consolidate(tmp_path)

    assert len(result["capacity"]) == 2
    assert (tmp_path / "capacity_comparison.csv").exists()
    assert (tmp_path / "capacity_comparison.md").exists()
    assert (tmp_path / "query_hotspots.csv").exists()
    assert (tmp_path / "docker_peaks.csv").exists()
