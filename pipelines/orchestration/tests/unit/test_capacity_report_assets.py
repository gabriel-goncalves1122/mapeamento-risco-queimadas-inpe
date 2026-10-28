from pathlib import Path

import pandas as pd

from scripts.performance.capacity_metadata import (
    DEFAULT_MATRIX_DIR,
    DEFAULT_SQL_DIR,
    SCENARIO_PROFILES,
    scenario_profile_rows
)
from scripts.performance.report_generator.main import generate
from scripts.performance.report_generator.metadata_parser import read_query_catalog
from scripts.performance.report_generator.latex_writer import latex_escape, to_latex_table
from scripts.performance.report_generator.tables import METRIC_DEFINITIONS, add_enriched_columns, classify_stability


def test_latex_escape_protege_caracteres_especiais():
    texto = latex_escape("dim_hospitais_cnes & erro 10%")

    assert r"dim\_hospitais\_cnes" in texto
    assert r"\&" in texto
    assert r"10\%" in texto


def test_classify_stability_diferencia_estavel_saturado_e_latencia_alta():
    assert classify_stability({"requests_erro": 0, "saturado": "False", "lat_p95_ms": 300}) == "ESTAVEL"
    assert classify_stability({"requests_erro": 1, "saturado": "False", "lat_p95_ms": 300}) == "SATURADO"
    assert classify_stability({"requests_erro": 0, "saturado": "True", "lat_p95_ms": 300}) == "SATURADO"
    assert classify_stability({"requests_erro": 0, "saturado": "False", "lat_p95_ms": 9000}) == "LATENCIA_ALTA"


def test_add_enriched_columns_calcula_speedup_eficiencia_e_classe():
    capacity = pd.DataFrame(
        [
            {
                "scenario": "scenario_01_baseline",
                "concurrency": 1,
                "requests_erro": 0,
                "saturado": False,
                "qps": 2.0,
                "lat_p95_ms": 100.0,
            },
            {
                "scenario": "scenario_03_query_heavy",
                "concurrency": 1,
                "requests_erro": 0,
                "saturado": False,
                "qps": 6.0,
                "lat_p95_ms": 80.0,
            },
        ]
    )

    enriched = add_enriched_columns(capacity)
    query_heavy = enriched[enriched["scenario"] == "scenario_03_query_heavy"].iloc[0]

    assert query_heavy["speedup_vs_baseline_qps"] == 3.0
    assert query_heavy["qps_per_allocated_cpu_pair"] == 1.5
    assert query_heavy["stability_class"] == "ESTAVEL"


def test_capacity_metadata_concentra_perfis_de_cenario():
    rows = scenario_profile_rows()

    assert [scenario.name for scenario in SCENARIO_PROFILES] == [
        "scenario_01_baseline",
        "scenario_02_balanced",
        "scenario_03_query_heavy",
    ]
    assert [row["label"] for row in rows] == ["Baseline", "Balanced", "Query Heavy"]
    assert rows[2]["cpu"] == 2.0


def test_to_latex_table_escapa_valores(tmp_path: Path):
    path = tmp_path / "tabela.tex"
    dataframe = pd.DataFrame([{"nome": "scenario_01_baseline", "valor": 12.34567}])

    to_latex_table(path, dataframe, ["nome", "valor"], ["Nome", "Valor"], "Resumo 10%")

    text = path.read_text(encoding="utf-8")
    assert r"Resumo 10\%" in text
    assert r"scenario\_01\_baseline" in text
    assert "12.346" in text


def test_read_query_catalog_extrai_metadados_e_sqls():
    catalog = read_query_catalog(DEFAULT_SQL_DIR)

    assert len(catalog) == 29
    assert all(row["objetivo"] for row in catalog)
    assert all(row["conceito"] for row in catalog)
    assert all(row["hipotese"] for row in catalog)
    assert all(row["motivo_cientifico"] for row in catalog)
    assert all(row["sql"].lower().lstrip().startswith(("select", "with")) for row in catalog)


def test_metricas_obrigatorias_estao_definidas():
    nomes = {row["metrica"] for row in METRIC_DEFINITIONS}

    assert {"QPS", "p50", "p95", "p99", "Taxa de erro", "Saturacao", "Cold-start", "Warm-start"}.issubset(nomes)
    assert all(row["como_ler"] for row in METRIC_DEFINITIONS)
    assert all(row["cuidado"] for row in METRIC_DEFINITIONS)


import pytest

@pytest.mark.skipif(not (DEFAULT_MATRIX_DIR / "capacity_comparison.csv").exists(), reason="Falta CSV base de benchmark")
def test_generate_cria_artefatos_esperados_em_diretorio_temporario(tmp_path: Path):
    report_dir = generate(DEFAULT_MATRIX_DIR, output_dir=tmp_path / "report", sql_dir=DEFAULT_SQL_DIR)

    for relative_path in (
        "README.md",
        "figures/qps_por_concorrencia.png",
        "figures/latencia_p95_p99.png",
        "tables/capacity_enriched.csv",
        "tables/query_catalog.csv",
        "tables/metric_definitions.csv",
        "tables/capacity_main_summary.tex",
        "tex/relatorio_capacidade_druid.tex",
        "tex/guia_metricas_benchmark.tex",
        "tex/catalogo_queries_benchmark.tex",
        "tex/apendice_evidencias_operacionais.tex",
    ):
        assert (report_dir / relative_path).exists()

    for stale_path in (
        "tex/apendice_queries_benchmark.tex",
        "tex/apendice_metricas_operacionais.tex",
        "pdf/apendice_queries_benchmark.pdf",
        "pdf/apendice_metricas_operacionais.pdf",
        "tables/capacity_summary.tex",
        "tables/query_catalog.tex",
    ):
        assert not (report_dir / stale_path).exists()

    main_tex = (report_dir / "tex/relatorio_capacidade_druid.tex").read_text(encoding="utf-8")
    assert "Historical" in main_tex
    assert "\textit" not in main_tex
    assert "O que mede" in main_tex
    assert "Por que importa" in main_tex
    assert "Como interpretar" in main_tex
    assert r"\textbf{Leitura dos dados.}" in main_tex
    assert "\t" not in main_tex
    assert "run_druid_benchmark.py" not in main_tex

    query_tex = (report_dir / "tex/catalogo_queries_benchmark.tex").read_text(encoding="utf-8")
    assert "Conceito base" in query_tex
    assert "Hipótese testada" in query_tex
    assert query_tex.count(r"\begin{lstlisting}[language=SQL]") == 19

    metrics_tex = (report_dir / "tex/guia_metricas_benchmark.tex").read_text(encoding="utf-8")
    assert "QPS não deve ser lido sozinho" in metrics_tex

    table_tex = (report_dir / "tables/capacity_main_summary.tex").read_text(encoding="utf-8")
    assert "longtable" in table_tex
    assert "requests_total" not in table_tex
