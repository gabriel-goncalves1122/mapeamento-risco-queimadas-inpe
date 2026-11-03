"""
Construtor de tabelas analíticas e glossário de métricas de capacidade (`CapacityTableBuilder`).

Calcula speedup relativo ao Baseline, eficiência de QPS por par de CPUs alocadas,
classificação de estabilidade operacional (`ESTAVEL`, `LATENCIA_ALTA`, `SATURADO`)
e exporta CSVs e tabelas LaTeX (SRP).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from scripts.benchmarks.capacity_metadata import (
    SCENARIO_CPU,
    SCENARIO_LABELS,
    SCENARIO_MEMORY_GB,
    scenario_profile_rows,
)
from .latex_writer import LatexReportWriter


class CapacityTableBuilder:
    """Enriquece os DataFrames da matriz de capacidade e gera artefatos CSV/LaTeX."""

    METRIC_DEFINITIONS: tuple[dict[str, str], ...] = (
        {
            "metrica": "QPS",
            "definicao": "Consultas finalizadas por segundo dentro do bloco medido.",
            "como_ler": "Maior QPS indica maior vazao, mas so e ganho real se erro e p95 continuarem aceitaveis.",
            "cuidado": "QPS pode parecer bom quando muitas consultas falham rapidamente.",
        },
        {
            "metrica": "p50",
            "definicao": "Mediana da latencia: metade das requisicoes foi mais rapida que esse valor.",
            "como_ler": "Mostra a experiencia tipica de consulta.",
            "cuidado": "Nao revela cauda longa nem saturacao.",
        },
        {
            "metrica": "p95",
            "definicao": "Latencia abaixo da qual 95% das requisicoes ficaram.",
            "como_ler": "E a principal metrica de estabilidade percebida em dashboards.",
            "cuidado": "Deve ser lida junto com taxa de erro.",
        },
        {
            "metrica": "p99",
            "definicao": "Latencia de cauda extrema: 99% das requisicoes ficaram abaixo dela.",
            "como_ler": "Indica o custo dos piores casos ainda bem-sucedidos.",
            "cuidado": "Com poucas amostras, oscila bastante; ainda assim revela risco operacional.",
        },
        {
            "metrica": "Taxa de erro",
            "definicao": "Percentual de requisicoes que terminaram com excecao, timeout ou erro HTTP.",
            "como_ler": "Qualquer valor acima de zero em benchmark pequeno merece investigacao.",
            "cuidado": "Nao compare latencia entre cenarios ignorando erros.",
        },
        {
            "metrica": "Saturacao",
            "definicao": "Classificacao derivada de erro ou estouro dos limites configurados no runner.",
            "como_ler": "Marca quando o cenario deixou de sustentar a carga de forma confiavel.",
            "cuidado": "Uma rodada saturada nao deve ser vendida como ganho de performance.",
        },
        {
            "metrica": "Cold-start",
            "definicao": "Execucao com cache de consulta desabilitado para aproximar leitura fria.",
            "como_ler": "Mostra o custo de buscar e processar dados sem reaproveitamento.",
            "cuidado": "Nao representa exatamente reinicio fisico de containers.",
        },
        {
            "metrica": "Warm-start",
            "definicao": "Execucao com cache habilitado e populado para medir reaproveitamento.",
            "como_ler": "Mostra ganho quando dashboards repetem padroes de consulta.",
            "cuidado": "Cache nao corrige falta de CPU/memoria sob alta concorrencia.",
        },
        {
            "metrica": "CPU Docker",
            "definicao": "Percentual de CPU usado pelo container durante a matriz.",
            "como_ler": "Picos acima de 100% indicam uso de mais de um core logico.",
            "cuidado": "Compare com limites de CPU do perfil, nao com a maquina inteira apenas.",
        },
        {
            "metrica": "Memoria Docker",
            "definicao": "Percentual de memoria usada dentro do limite do container.",
            "como_ler": "Queda percentual pode ocorrer porque o limite aumentou, nao porque a carga diminuiu.",
            "cuidado": "Leia junto com CPU e erros do Historical.",
        },
        {
            "metrica": "Loadstatus",
            "definicao": "Percentual de segmentos carregados e disponiveis no Druid.",
            "como_ler": "100% indica que os dados estavam disponiveis para consulta.",
            "cuidado": "Loadstatus bom nao garante performance; apenas disponibilidade.",
        },
    )

    @staticmethod
    def read_csv(path: str | Path) -> pd.DataFrame:
        target = Path(path)
        return pd.read_csv(target) if target.exists() else pd.DataFrame()

    @staticmethod
    def classify_stability(row: Mapping[str, Any] | pd.Series) -> str:
        """Classifica a estabilidade priorizando falhas HTTP/timeouts sobre latência."""
        saturated = str(row.get("saturado", "")).lower() == "true"
        if float(row.get("requests_erro", 0)) > 0 or saturated:
            return "SATURADO"
        if float(row.get("lat_p95_ms", 0)) >= 8000:
            return "LATENCIA_ALTA"
        return "ESTAVEL"

    @classmethod
    def add_enriched_columns(cls, capacity: pd.DataFrame) -> pd.DataFrame:
        """Adiciona colunas derivadas de speedup, QPS/CPU e classe de estabilidade."""
        if capacity.empty:
            return capacity
        capacity = capacity.copy()
        capacity["scenario_label"] = capacity["scenario"].map(SCENARIO_LABELS)
        capacity["allocated_cpu_per_query_node"] = capacity["scenario"].map(SCENARIO_CPU)
        capacity["allocated_memory_gb_per_query_node"] = capacity["scenario"].map(SCENARIO_MEMORY_GB)
        capacity["qps_per_allocated_cpu_pair"] = capacity["qps"] / (
            capacity["allocated_cpu_per_query_node"] * 2.0
        )
        capacity["stable"] = (capacity["requests_erro"] == 0) & (
            ~capacity["saturado"].astype(str).str.lower().eq("true")
        )
        capacity["stability_class"] = capacity.apply(cls.classify_stability, axis=1)

        baseline = capacity[capacity["scenario"] == "scenario_01_baseline"][
            ["concurrency", "qps", "lat_p95_ms"]
        ].rename(columns={"qps": "baseline_qps", "lat_p95_ms": "baseline_p95_ms"})
        capacity = capacity.merge(baseline, on="concurrency", how="left")
        capacity["speedup_vs_baseline_qps"] = capacity["qps"] / capacity["baseline_qps"]
        capacity["p95_delta_vs_baseline_percent"] = (
            (capacity["lat_p95_ms"] - capacity["baseline_p95_ms"]) / capacity["baseline_p95_ms"]
        ) * 100
        return capacity

    @classmethod
    def build_errors_df(cls, matrix_dir: Path) -> pd.DataFrame:
        error_rows: list[dict[str, Any]] = []
        for scenario_dir in sorted(matrix_dir.glob("scenario_*")):
            errors = cls.read_csv(scenario_dir / "errors.csv")
            if errors.empty:
                continue
            grouped = (
                errors.groupby(["capacity_scenario", "concurrency", "query_id", "cache_mode"])
                .size()
                .reset_index(name="erros")
            )
            error_rows.extend(grouped.to_dict("records"))
        if error_rows:
            return pd.DataFrame(error_rows)
        return pd.DataFrame(columns=["capacity_scenario", "concurrency", "query_id", "cache_mode", "erros"])

    @classmethod
    def build_segments_df(cls, matrix_dir: Path) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for scenario_dir in sorted(matrix_dir.glob("scenario_*")):
            segments = cls.read_csv(scenario_dir / "druid_segments.csv")
            if segments.empty:
                continue
            segments.insert(0, "scenario", scenario_dir.name)
            rows.extend(segments.to_dict("records"))
        return pd.DataFrame(rows)

    @staticmethod
    def build_loadstatus_df(matrix_dir: Path) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for scenario_dir in sorted(matrix_dir.glob("scenario_*")):
            path = scenario_dir / "loadstatus.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for datasource, status in data.items():
                rows.append(
                    {
                        "scenario": scenario_dir.name,
                        "datasource": datasource,
                        "loadstatus_percent": status,
                    }
                )
        return pd.DataFrame(rows)

    @classmethod
    def make_tables(
        cls,
        report_dir: Path,
        capacity: pd.DataFrame,
        docker_peaks: pd.DataFrame,
        query_hotspots: pd.DataFrame,
        cache_gain: pd.DataFrame,
        query_catalog: Sequence[Mapping[str, Any]],
        matrix_dir: Path,
    ) -> None:
        tables_dir = report_dir / "tables"
        errors_df = cls.build_errors_df(matrix_dir)
        segments_df = cls.build_segments_df(matrix_dir)
        loadstatus_df = cls.build_loadstatus_df(matrix_dir)
        query_catalog_df = pd.DataFrame(query_catalog)
        metrics_df = pd.DataFrame(cls.METRIC_DEFINITIONS)

        capacity.to_csv(tables_dir / "capacity_enriched.csv", index=False)
        pd.DataFrame(scenario_profile_rows()).to_csv(tables_dir / "scenario_profiles.csv", index=False)
        query_catalog_df.to_csv(tables_dir / "query_catalog.csv", index=False)
        metrics_df.to_csv(tables_dir / "metric_definitions.csv", index=False)
        errors_df.to_csv(tables_dir / "errors_summary.csv", index=False)
        segments_df.to_csv(tables_dir / "segments_summary.csv", index=False)
        loadstatus_df.to_csv(tables_dir / "loadstatus_summary.csv", index=False)

        LatexReportWriter.to_latex_table(
            tables_dir / "scenario_profiles.tex",
            pd.DataFrame(scenario_profile_rows()),
            ["label", "cpu", "memory_gb", "threads", "merge_buffers", "tradeoff"],
            ["Cenario", "CPU", "GB", "Threads", "Merge", "Trade-off"],
            "Perfis de capacidade aplicados ao Broker e ao Historical.",
            widths=[
                r"p{0.12\textwidth}",
                r"p{0.08\textwidth}",
                r"p{0.08\textwidth}",
                r"p{0.10\textwidth}",
                r"p{0.10\textwidth}",
                r"p{0.42\textwidth}",
            ],
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "capacity_main_summary.tex",
            capacity[["scenario_label", "concurrency", "qps", "lat_p95_ms", "requests_erro", "stability_class"]],
            ["scenario_label", "concurrency", "qps", "lat_p95_ms", "requests_erro", "stability_class"],
            ["Cenario", "Conc.", "QPS", "p95 ms", "Erros", "Classe"],
            "Resumo compacto para leitura no relatorio principal.",
            widths=[
                r"p{0.28\textwidth}",
                r"p{0.09\textwidth}",
                r"p{0.11\textwidth}",
                r"p{0.13\textwidth}",
                r"p{0.10\textwidth}",
                r"p{0.16\textwidth}",
            ],
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "metric_definitions.tex",
            metrics_df,
            ["metrica", "definicao", "como_ler", "cuidado"],
            ["Metrica", "Definicao", "Como ler", "Cuidado"],
            "Glossario de metricas usadas na matriz.",
            widths=[r"p{0.14\textwidth}", r"p{0.28\textwidth}", r"p{0.28\textwidth}", r"p{0.22\textwidth}"],
            font_size=r"\footnotesize",
        )
        full_cols = [
            "scenario_label",
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
            "stability_class",
        ]
        LatexReportWriter.to_latex_table(
            tables_dir / "capacity_full_landscape.tex",
            capacity[full_cols],
            full_cols,
            ["Cenario", "Conc.", "Req.", "Erros", "Erro %", "QPS", "Avg", "p50", "p90", "p95", "p99", "Max", "Classe"],
            "Tabela completa de capacidade por cenario e concorrencia.",
            widths=[
                r"p{0.19\linewidth}",
                r"p{0.05\linewidth}",
                r"p{0.05\linewidth}",
                r"p{0.05\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.06\linewidth}",
                r"p{0.09\linewidth}",
            ],
            font_size=r"\scriptsize",
            landscape=True,
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "docker_peaks_full.tex",
            docker_peaks,
            ["scenario", "container", "samples", "cpu_avg_percent", "cpu_max_percent", "mem_avg_percent", "mem_max_percent"],
            ["Cenario", "Container", "Amostras", "CPU media %", "CPU max %", "Mem media %", "Mem max %"],
            "Picos e medias observadas nos containers durante a matriz.",
            widths=[
                r"p{0.20\textwidth}",
                r"p{0.17\textwidth}",
                r"p{0.10\textwidth}",
                r"p{0.12\textwidth}",
                r"p{0.12\textwidth}",
                r"p{0.12\textwidth}",
                r"p{0.12\textwidth}",
            ],
            font_size=r"\footnotesize",
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "query_hotspots_full.tex",
            query_hotspots.head(30),
            ["scenario", "query_id", "cache_mode", "lat_p95_ms", "lat_p99_ms", "requests_erro", "error_rate_percent"],
            ["Cenario", "Query", "Cache", "p95 ms", "p99 ms", "Erros", "Erro %"],
            "Maiores hotspots de latencia p95.",
            widths=[
                r"p{0.19\textwidth}",
                r"p{0.36\textwidth}",
                r"p{0.08\textwidth}",
                r"p{0.09\textwidth}",
                r"p{0.09\textwidth}",
                r"p{0.07\textwidth}",
                r"p{0.08\textwidth}",
            ],
            font_size=r"\scriptsize",
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "cache_gain_full.tex",
            cache_gain.head(30),
            [
                "capacity_scenario_dir",
                "query_id",
                "p95_gain_percent",
                "cold_p95_ms",
                "warm_p95_ms",
                "cold_error_rate_percent",
                "warm_error_rate_percent",
            ],
            ["Cenario", "Query", "Ganho p95 %", "Cold p95", "Warm p95", "Erro cold %", "Erro warm %"],
            "Maiores ganhos de warm-start por p95.",
            widths=[
                r"p{0.19\textwidth}",
                r"p{0.35\textwidth}",
                r"p{0.10\textwidth}",
                r"p{0.09\textwidth}",
                r"p{0.09\textwidth}",
                r"p{0.09\textwidth}",
                r"p{0.09\textwidth}",
            ],
            font_size=r"\scriptsize",
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "errors_full.tex",
            errors_df.head(50),
            ["capacity_scenario", "concurrency", "query_id", "cache_mode", "erros"],
            ["Cenario", "Conc.", "Query", "Cache", "Erros"],
            "Resumo dos erros observados nos cenarios saturados.",
            widths=[
                r"p{0.22\textwidth}",
                r"p{0.08\textwidth}",
                r"p{0.42\textwidth}",
                r"p{0.10\textwidth}",
                r"p{0.08\textwidth}",
            ],
            font_size=r"\footnotesize",
        )
        LatexReportWriter.to_latex_table(
            tables_dir / "query_catalog_summary.tex",
            query_catalog_df[["query_id", "familia", "padrao_carga", "datasource", "objetivo"]],
            ["query_id", "familia", "padrao_carga", "datasource", "objetivo"],
            ["Query", "Familia", "Padrao", "Datasource", "Objetivo"],
            "Catalogo resumido das queries executadas.",
            widths=[
                r"p{0.27\textwidth}",
                r"p{0.16\textwidth}",
                r"p{0.14\textwidth}",
                r"p{0.21\textwidth}",
                r"p{0.20\textwidth}",
            ],
            font_size=r"\scriptsize",
            landscape=True,
        )
        if not segments_df.empty:
            LatexReportWriter.to_latex_table(
                tables_dir / "segments_summary.tex",
                segments_df.head(60),
                list(segments_df.columns),
                list(segments_df.columns),
                "Segmentos Druid observados por cenario.",
                font_size=r"\scriptsize",
                landscape=True,
            )
        if not loadstatus_df.empty:
            LatexReportWriter.to_latex_table(
                tables_dir / "loadstatus_summary.tex",
                loadstatus_df,
                ["scenario", "datasource", "loadstatus_percent"],
                ["Cenario", "Datasource", "Loadstatus %"],
                "Loadstatus por datasource e cenario.",
                widths=[r"p{0.28\textwidth}", r"p{0.45\textwidth}", r"p{0.16\textwidth}"],
            )


METRIC_DEFINITIONS = CapacityTableBuilder.METRIC_DEFINITIONS
read_csv = CapacityTableBuilder.read_csv
classify_stability = CapacityTableBuilder.classify_stability
add_enriched_columns = CapacityTableBuilder.add_enriched_columns
build_errors_df = CapacityTableBuilder.build_errors_df
build_segments_df = CapacityTableBuilder.build_segments_df
build_loadstatus_df = CapacityTableBuilder.build_loadstatus_df
make_tables = CapacityTableBuilder.make_tables
