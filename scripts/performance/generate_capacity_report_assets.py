"""
Gera graficos, tabelas e fontes LaTeX para a matriz de capacidade Druid.

O script nao executa benchmark. Ele transforma evidencias persistidas em quatro
documentos: relatorio principal, guia de metricas, catalogo de queries e
apendice operacional.
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Scripts chamados diretamente por caminho precisam enxergar o pacote do repo.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from scripts.performance.capacity_metadata import (  # noqa: E402
    DEFAULT_DOCS_ROOT,
    DEFAULT_MATRIX_DIR,
    DEFAULT_SQL_DIR,
    PROJECT_ROOT,
    SCENARIO_CPU,
    SCENARIO_LABELS,
    SCENARIO_MEMORY_GB,
    scenario_profile_rows,
)

REPORT_NAMES = (
    "relatorio_capacidade_druid",
    "guia_metricas_benchmark",
    "catalogo_queries_benchmark",
    "apendice_evidencias_operacionais",
)
STALE_REPORT_NAMES = (
    "apendice_queries_benchmark",
    "apendice_metricas_operacionais",
)
STALE_TABLE_FILES = (
    "cache_gain.tex",
    "capacity_summary.tex",
    "docker_peaks.tex",
    "errors_summary.tex",
    "query_catalog.tex",
    "query_hotspots.tex",
)

METRIC_DEFINITIONS = (
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

QUERY_FAMILY_GUIDE = {
    "latency_simple": {
        "titulo": "Latencia simples",
        "conceito": "Consultas pequenas usadas para medir o piso de resposta do Broker e a leitura basica de segmentos.",
        "hipotese": "Se ate essas consultas oscilarem, o problema esta no cluster ou na disponibilidade dos segmentos, nao na complexidade analitica.",
        "motivo": "Funciona como controle experimental para comparar as consultas mais pesadas.",
        "impacto": "Pressiona pouco o Historical; serve para medir overhead de SQL, roteamento e filtros simples.",
    },
    "olap_pesado": {
        "titulo": "OLAP pesado",
        "conceito": "Agregacoes, agrupamentos multidimensionais, soma, media e count distinct sobre dimensoes batch.",
        "hipotese": "Quanto mais cardinalidade e agregacao numerica, maior a pressao sobre processamento e merge de resultados.",
        "motivo": "Representa o uso esperado de um banco OLAP em paineis de resumo e ranking.",
        "impacto": "Exige varredura de colunas, agregacao no Historical e merge no Broker.",
    },
    "joins_dimensionais": {
        "titulo": "Joins dimensionais",
        "conceito": "Cruzamentos entre dimensoes ja enriquecidas pelo ETL para simular visoes analiticas territoriais.",
        "hipotese": "Joins com hospitais, municipios e terras indigenas devem expor gargalos de planejamento, shuffle e merge.",
        "motivo": "Testa o limite pratico de usar Druid SQL para cruzamentos que o Superset pode exigir.",
        "impacto": "Pressiona Broker e Historical ao mesmo tempo, principalmente quando a maior dimensao participa.",
    },
    "payload_espacial": {
        "titulo": "Payload espacial",
        "conceito": "Leituras de `path_json` e campos de geometria serializada usados por mapas no Superset.",
        "hipotese": "Mesmo sem calculo espacial nativo, retornar strings grandes aumenta bytes e latencia de resposta.",
        "motivo": "Mede o custo operacional do contrato visual adotado para Druid/Superset.",
        "impacto": "Pressiona I/O, serializacao e tamanho de resposta ao cliente.",
    },
    "dashboard_misto": {
        "titulo": "Dashboard misto",
        "conceito": "Consultas compostas que combinam padroes de painel real: agregacao, joins, union e regras de qualidade.",
        "hipotese": "A mistura de padroes aproxima melhor a experiencia de uso do que queries isoladas.",
        "motivo": "Valida se o perfil suporta uma sessao analitica mais proxima do Superset.",
        "impacto": "Exercita planejamento SQL, subconsultas, union, filtros e agregacoes em uma mesma carga.",
    },
}


def latex_escape(value):
    text = "" if value is None else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def read_csv(path):
    return pd.read_csv(path) if Path(path).exists() else pd.DataFrame()


def ensure_dirs(report_dir):
    for name in ("tex", "figures", "tables", "pdf"):
        (report_dir / name).mkdir(parents=True, exist_ok=True)


def clean_stale_reports(report_dir):
    for report in STALE_REPORT_NAMES:
        for folder in ("tex", "pdf"):
            for suffix in (".tex", ".pdf", ".aux", ".log", ".out", ".compile.log"):
                path = report_dir / folder / f"{report}{suffix}"
                if path.exists():
                    path.unlink()
    for table_file in STALE_TABLE_FILES:
        path = report_dir / "tables" / table_file
        if path.exists():
            path.unlink()


def format_value(value, decimals=3):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def add_enriched_columns(capacity):
    if capacity.empty:
        return capacity
    capacity = capacity.copy()
    capacity["scenario_label"] = capacity["scenario"].map(SCENARIO_LABELS)
    capacity["allocated_cpu_per_query_node"] = capacity["scenario"].map(SCENARIO_CPU)
    capacity["allocated_memory_gb_per_query_node"] = capacity["scenario"].map(SCENARIO_MEMORY_GB)
    capacity["qps_per_allocated_cpu_pair"] = capacity["qps"] / (capacity["allocated_cpu_per_query_node"] * 2.0)
    capacity["stable"] = (capacity["requests_erro"] == 0) & (~capacity["saturado"].astype(str).str.lower().eq("true"))
    capacity["stability_class"] = capacity.apply(classify_stability, axis=1)

    baseline = capacity[capacity["scenario"] == "scenario_01_baseline"][["concurrency", "qps", "lat_p95_ms"]]
    baseline = baseline.rename(columns={"qps": "baseline_qps", "lat_p95_ms": "baseline_p95_ms"})
    capacity = capacity.merge(baseline, on="concurrency", how="left")
    capacity["speedup_vs_baseline_qps"] = capacity["qps"] / capacity["baseline_qps"]
    capacity["p95_delta_vs_baseline_percent"] = ((capacity["lat_p95_ms"] - capacity["baseline_p95_ms"]) / capacity["baseline_p95_ms"]) * 100
    return capacity


def classify_stability(row):
    saturated = str(row.get("saturado", "")).lower() == "true"
    if float(row.get("requests_erro", 0)) > 0 or saturated:
        return "SATURADO"
    if float(row.get("lat_p95_ms", 0)) >= 8000:
        return "LATENCIA_ALTA"
    return "ESTAVEL"


def to_latex_table(path, dataframe, columns, headers, caption=None, widths=None, font_size=r"\small", landscape=False):
    spec = "".join(widths) if widths else "l" * len(columns)
    lines = []
    if landscape:
        lines.append(r"\begin{landscape}")
    lines.append("{")
    lines.append(font_size)
    lines.append(r"\setlength{\tabcolsep}{4pt}")
    lines.append(r"\renewcommand{\arraystretch}{1.15}")
    lines.append(r"\begin{longtable}{" + spec + "}")
    if caption:
        lines.append(r"\caption{" + latex_escape(caption) + r"}\\")
    lines.append(r"\toprule")
    lines.append(" & ".join(latex_escape(header) for header in headers) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(r"\toprule")
    lines.append(" & ".join(latex_escape(header) for header in headers) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    for _, row in dataframe.iterrows():
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = format_value(value)
            values.append(latex_escape(value))
        lines.append(" & ".join(values) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    lines.append("}")
    if landscape:
        lines.append(r"\end{landscape}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_figures(report_dir, capacity, docker_peaks, cache_gain, query_hotspots):
    figures_dir = report_dir / "figures"
    plt.style.use("seaborn-v0_8-whitegrid")

    pivot_qps = capacity.pivot(index="concurrency", columns="scenario_label", values="qps")
    ax = pivot_qps.plot(marker="o", figsize=(8, 4.8))
    ax.set_title("Throughput por cenário e concorrência")
    ax.set_xlabel("Concorrência")
    ax.set_ylabel("QPS")
    ax.legend(title="")
    plt.tight_layout()
    plt.savefig(figures_dir / "qps_por_concorrencia.png", dpi=160)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for metric, linestyle in (("lat_p95_ms", "-"), ("lat_p99_ms", "--")):
        for scenario, group in capacity.groupby("scenario_label"):
            ax.plot(group["concurrency"], group[metric], marker="o", linestyle=linestyle, label=f"{scenario} {metric}")
    ax.set_title("Latência p95/p99 por cenário")
    ax.set_xlabel("Concorrência")
    ax.set_ylabel("Latência (ms)")
    ax.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(figures_dir / "latencia_p95_p99.png", dpi=160)
    plt.close()

    pivot_errors = capacity.pivot(index="concurrency", columns="scenario_label", values="error_rate_percent")
    ax = pivot_errors.plot(kind="bar", figsize=(8, 4.8))
    ax.set_title("Taxa de erro por cenário")
    ax.set_xlabel("Concorrência")
    ax.set_ylabel("Erro (%)")
    ax.legend(title="")
    plt.tight_layout()
    plt.savefig(figures_dir / "taxa_erro.png", dpi=160)
    plt.close()

    docker = docker_peaks[docker_peaks["container"].isin(["broker", "historical"])].copy()
    docker["scenario_label"] = docker["scenario"].map(SCENARIO_LABELS)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharex=False)
    for metric, ax, title in (
        ("cpu_max_percent", axes[0], "Pico de CPU"),
        ("mem_max_percent", axes[1], "Pico de memória"),
    ):
        pivot = docker.pivot(index="scenario_label", columns="container", values=metric)
        pivot.plot(kind="bar", ax=ax)
        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel("%")
        ax.tick_params(axis="x", rotation=25)
    plt.tight_layout()
    plt.savefig(figures_dir / "docker_cpu_mem_picos.png", dpi=160)
    plt.close()

    top_cache = cache_gain.sort_values("p95_gain_percent", ascending=False).head(10).copy()
    top_cache["label"] = top_cache["capacity_scenario_dir"].str.replace("scenario_", "S", regex=False) + " | " + top_cache["query_id"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(top_cache["label"][::-1], top_cache["p95_gain_percent"][::-1])
    ax.set_title("Maiores ganhos de warm-start por p95")
    ax.set_xlabel("Ganho p95 (%)")
    plt.tight_layout()
    plt.savefig(figures_dir / "ganho_warm_start_top10.png", dpi=160)
    plt.close()

    hotspot = query_hotspots.head(18).copy()
    hotspot["scenario_cache"] = hotspot["scenario"] + " / " + hotspot["cache_mode"]
    pivot = hotspot.pivot_table(index="query_id", columns="scenario_cache", values="lat_p95_ms", aggfunc="max").fillna(0)
    fig, ax = plt.subplots(figsize=(11, 7))
    image = ax.imshow(pivot.values, aspect="auto", cmap="magma")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=7)
    ax.set_title("Hotspots de latência p95 por query")
    fig.colorbar(image, ax=ax, label="p95 (ms)")
    plt.tight_layout()
    plt.savefig(figures_dir / "heatmap_hotspots_queries.png", dpi=160)
    plt.close()


def parse_query_metadata(sql_text):
    metadata = {}
    body_lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") and ":" in stripped:
            key, value = stripped[2:].split(":", 1)
            metadata[key.strip()] = value.strip()
        else:
            body_lines.append(line)
    return metadata, "\n".join(body_lines).strip()


def read_query_catalog(sql_dir):
    rows = []
    for path in sorted(sql_dir.rglob("*.sql")):
        text = path.read_text(encoding="utf-8")
        metadata, body = parse_query_metadata(text)
        categoria = metadata.get("categoria", path.parent.name)
        guide = QUERY_FAMILY_GUIDE.get(categoria, {})
        objetivo = metadata.get("objetivo", "")
        rows.append(
            {
                "query_id": f"{path.parent.name}/{path.stem}",
                "path": str(path.relative_to(PROJECT_ROOT)),
                "categoria": categoria,
                "familia": guide.get("titulo", categoria),
                "conceito": guide.get("conceito", ""),
                "hipotese": guide.get("hipotese", ""),
                "motivo_cientifico": f"{guide.get('motivo', '')} Objetivo local: {objetivo}".strip(),
                "impacto_druid": guide.get("impacto", ""),
                "objetivo": objetivo,
                "datasource": metadata.get("datasource", ""),
                "padrao_carga": metadata.get("padrao_carga", ""),
                "visualizacao": metadata.get("visualizacao", ""),
                "sql": body,
            }
        )
    return rows


def hardware_snapshot():
    cpu_count = os.cpu_count() or 0
    mem_total_gib = ""
    mem_available_gib = ""
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            info[key] = float(raw.strip().split()[0])
        mem_total_gib = round(info.get("MemTotal", 0) / 1024 / 1024, 2)
        mem_available_gib = round(info.get("MemAvailable", 0) / 1024 / 1024, 2)
    except Exception:
        pass
    return {
        "cpu_count": cpu_count,
        "mem_total_gib": mem_total_gib,
        "mem_available_gib": mem_available_gib,
    }


def build_errors_df(matrix_dir):
    error_rows = []
    for scenario_dir in sorted(matrix_dir.glob("scenario_*")):
        errors = read_csv(scenario_dir / "errors.csv")
        if errors.empty:
            continue
        grouped = errors.groupby(["capacity_scenario", "concurrency", "query_id", "cache_mode"]).size().reset_index(name="erros")
        error_rows.extend(grouped.to_dict("records"))
    if error_rows:
        return pd.DataFrame(error_rows)
    return pd.DataFrame(columns=["capacity_scenario", "concurrency", "query_id", "cache_mode", "erros"])


def build_segments_df(matrix_dir):
    rows = []
    for scenario_dir in sorted(matrix_dir.glob("scenario_*")):
        segments = read_csv(scenario_dir / "druid_segments.csv")
        if segments.empty:
            continue
        segments.insert(0, "scenario", scenario_dir.name)
        rows.extend(segments.to_dict("records"))
    return pd.DataFrame(rows)


def build_loadstatus_df(matrix_dir):
    rows = []
    for scenario_dir in sorted(matrix_dir.glob("scenario_*")):
        path = scenario_dir / "loadstatus.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for datasource, status in data.items():
            rows.append({"scenario": scenario_dir.name, "datasource": datasource, "loadstatus_percent": status})
    return pd.DataFrame(rows)


def make_tables(report_dir, capacity, docker_peaks, query_hotspots, cache_gain, query_catalog, matrix_dir):
    tables_dir = report_dir / "tables"
    errors_df = build_errors_df(matrix_dir)
    segments_df = build_segments_df(matrix_dir)
    loadstatus_df = build_loadstatus_df(matrix_dir)
    query_catalog_df = pd.DataFrame(query_catalog)
    metrics_df = pd.DataFrame(METRIC_DEFINITIONS)

    capacity.to_csv(tables_dir / "capacity_enriched.csv", index=False)
    pd.DataFrame(scenario_profile_rows()).to_csv(tables_dir / "scenario_profiles.csv", index=False)
    query_catalog_df.to_csv(tables_dir / "query_catalog.csv", index=False)
    metrics_df.to_csv(tables_dir / "metric_definitions.csv", index=False)
    errors_df.to_csv(tables_dir / "errors_summary.csv", index=False)
    segments_df.to_csv(tables_dir / "segments_summary.csv", index=False)
    loadstatus_df.to_csv(tables_dir / "loadstatus_summary.csv", index=False)

    to_latex_table(
        tables_dir / "scenario_profiles.tex",
        pd.DataFrame(scenario_profile_rows()),
        ["label", "cpu", "memory_gb", "threads", "merge_buffers", "tradeoff"],
        ["Cenario", "CPU", "GB", "Threads", "Merge", "Trade-off"],
        "Perfis de capacidade aplicados ao Broker e ao Historical.",
        widths=[r"p{0.12\textwidth}", r"p{0.08\textwidth}", r"p{0.08\textwidth}", r"p{0.10\textwidth}", r"p{0.10\textwidth}", r"p{0.42\textwidth}"],
    )
    to_latex_table(
        tables_dir / "capacity_main_summary.tex",
        capacity[["scenario_label", "concurrency", "qps", "lat_p95_ms", "requests_erro", "stability_class"]],
        ["scenario_label", "concurrency", "qps", "lat_p95_ms", "requests_erro", "stability_class"],
        ["Cenario", "Conc.", "QPS", "p95 ms", "Erros", "Classe"],
        "Resumo compacto para leitura no relatorio principal.",
        widths=[r"p{0.28\textwidth}", r"p{0.09\textwidth}", r"p{0.11\textwidth}", r"p{0.13\textwidth}", r"p{0.10\textwidth}", r"p{0.16\textwidth}"],
    )
    to_latex_table(
        tables_dir / "metric_definitions.tex",
        metrics_df,
        ["metrica", "definicao", "como_ler", "cuidado"],
        ["Metrica", "Definicao", "Como ler", "Cuidado"],
        "Glossario de metricas usadas na matriz.",
        widths=[r"p{0.14\textwidth}", r"p{0.28\textwidth}", r"p{0.28\textwidth}", r"p{0.22\textwidth}"],
        font_size=r"\footnotesize",
    )
    to_latex_table(
        tables_dir / "capacity_full_landscape.tex",
        capacity[["scenario_label", "concurrency", "requests_total", "requests_erro", "error_rate_percent", "qps", "lat_avg_ms", "lat_p50_ms", "lat_p90_ms", "lat_p95_ms", "lat_p99_ms", "lat_max_ms", "stability_class"]],
        ["scenario_label", "concurrency", "requests_total", "requests_erro", "error_rate_percent", "qps", "lat_avg_ms", "lat_p50_ms", "lat_p90_ms", "lat_p95_ms", "lat_p99_ms", "lat_max_ms", "stability_class"],
        ["Cenario", "Conc.", "Req.", "Erros", "Erro %", "QPS", "Avg", "p50", "p90", "p95", "p99", "Max", "Classe"],
        "Tabela completa de capacidade por cenario e concorrencia.",
        widths=[r"p{0.19\linewidth}", r"p{0.05\linewidth}", r"p{0.05\linewidth}", r"p{0.05\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.06\linewidth}", r"p{0.09\linewidth}"],
        font_size=r"\scriptsize",
        landscape=True,
    )
    to_latex_table(
        tables_dir / "docker_peaks_full.tex",
        docker_peaks,
        ["scenario", "container", "samples", "cpu_avg_percent", "cpu_max_percent", "mem_avg_percent", "mem_max_percent"],
        ["Cenario", "Container", "Amostras", "CPU media %", "CPU max %", "Mem media %", "Mem max %"],
        "Picos e medias observadas nos containers durante a matriz.",
        widths=[r"p{0.20\textwidth}", r"p{0.17\textwidth}", r"p{0.10\textwidth}", r"p{0.12\textwidth}", r"p{0.12\textwidth}", r"p{0.12\textwidth}", r"p{0.12\textwidth}"],
        font_size=r"\footnotesize",
    )
    to_latex_table(
        tables_dir / "query_hotspots_full.tex",
        query_hotspots.head(30),
        ["scenario", "query_id", "cache_mode", "lat_p95_ms", "lat_p99_ms", "requests_erro", "error_rate_percent"],
        ["Cenario", "Query", "Cache", "p95 ms", "p99 ms", "Erros", "Erro %"],
        "Maiores hotspots de latencia p95.",
        widths=[r"p{0.19\textwidth}", r"p{0.36\textwidth}", r"p{0.08\textwidth}", r"p{0.09\textwidth}", r"p{0.09\textwidth}", r"p{0.07\textwidth}", r"p{0.08\textwidth}"],
        font_size=r"\scriptsize",
    )
    to_latex_table(
        tables_dir / "cache_gain_full.tex",
        cache_gain.head(30),
        ["capacity_scenario_dir", "query_id", "p95_gain_percent", "cold_p95_ms", "warm_p95_ms", "cold_error_rate_percent", "warm_error_rate_percent"],
        ["Cenario", "Query", "Ganho p95 %", "Cold p95", "Warm p95", "Erro cold %", "Erro warm %"],
        "Maiores ganhos de warm-start por p95.",
        widths=[r"p{0.19\textwidth}", r"p{0.35\textwidth}", r"p{0.10\textwidth}", r"p{0.09\textwidth}", r"p{0.09\textwidth}", r"p{0.09\textwidth}", r"p{0.09\textwidth}"],
        font_size=r"\scriptsize",
    )
    to_latex_table(
        tables_dir / "errors_full.tex",
        errors_df.head(50),
        ["capacity_scenario", "concurrency", "query_id", "cache_mode", "erros"],
        ["Cenario", "Conc.", "Query", "Cache", "Erros"],
        "Resumo dos erros observados nos cenarios saturados.",
        widths=[r"p{0.22\textwidth}", r"p{0.08\textwidth}", r"p{0.42\textwidth}", r"p{0.10\textwidth}", r"p{0.08\textwidth}"],
        font_size=r"\footnotesize",
    )
    to_latex_table(
        tables_dir / "query_catalog_summary.tex",
        query_catalog_df[["query_id", "familia", "padrao_carga", "datasource", "objetivo"]],
        ["query_id", "familia", "padrao_carga", "datasource", "objetivo"],
        ["Query", "Familia", "Padrao", "Datasource", "Objetivo"],
        "Catalogo resumido das queries executadas.",
        widths=[r"p{0.27\textwidth}", r"p{0.16\textwidth}", r"p{0.14\textwidth}", r"p{0.21\textwidth}", r"p{0.20\textwidth}"],
        font_size=r"\scriptsize",
        landscape=True,
    )
    if not segments_df.empty:
        to_latex_table(
            tables_dir / "segments_summary.tex",
            segments_df.head(60),
            list(segments_df.columns),
            list(segments_df.columns),
            "Segmentos Druid observados por cenario.",
            font_size=r"\scriptsize",
            landscape=True,
        )
    if not loadstatus_df.empty:
        to_latex_table(
            tables_dir / "loadstatus_summary.tex",
            loadstatus_df,
            ["scenario", "datasource", "loadstatus_percent"],
            ["Cenario", "Datasource", "Loadstatus %"],
            "Loadstatus por datasource e cenario.",
            widths=[r"p{0.28\textwidth}", r"p{0.45\textwidth}", r"p{0.16\textwidth}"],
        )


def latex_preamble(title):
    return rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[brazil]{{babel}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{float}}
\usepackage{{xcolor}}
\usepackage{{listings}}
\usepackage{{pdflscape}}
\usepackage{{placeins}}
\usepackage[hidelinks]{{hyperref}}
\geometry{{margin=2.1cm}}
\setlength{{\parskip}}{{0.5em}}
\setlength{{\parindent}}{{0pt}}
\lstset{{
  basicstyle=\ttfamily\footnotesize,
  breaklines=true,
  columns=fullflexible,
  frame=single,
  showstringspaces=false,
  keywordstyle=\color{{blue}},
  commentstyle=\color{{gray}}
}}
\title{{{latex_escape(title)}}}
\author{{CCO DataOps}}
\date{{30 de junho de 2026}}
\begin{{document}}
\maketitle
"""


def latex_end():
    return "\n\\end{document}\n"


def figure_block(filename, caption, label):
    return (
        rf"\begin{{figure}}[H]\centering"
        rf"\includegraphics[width=0.92\textwidth,height=0.42\textheight,keepaspectratio]{{../figures/{filename}}}"
        rf"\caption{{{latex_escape(caption)}}}\label{{fig:{label}}}\end{{figure}}"
    )


def capacity_row(capacity, scenario, concurrency):
    row = capacity[(capacity["scenario"] == scenario) & (capacity["concurrency"] == concurrency)]
    return row.iloc[0] if not row.empty else {}


def write_main_report(report_dir, capacity, matrix_dir, hardware):
    tex = report_dir / "tex" / "relatorio_capacidade_druid.tex"
    baseline_c4 = capacity_row(capacity, "scenario_01_baseline", 4)
    balanced_c2 = capacity_row(capacity, "scenario_02_balanced", 2)
    balanced_c4 = capacity_row(capacity, "scenario_02_balanced", 4)
    heavy_c4 = capacity_row(capacity, "scenario_03_query_heavy", 4)

    lines = [latex_preamble("Relatório científico da matriz de capacidade do Apache Druid")]
    lines.extend(
        [
            r"\section{Como ler este documento}",
            "Este relatório foi reorganizado para acompanhar o raciocínio experimental. Primeiro são descritos arquitetura e metodologia. Em seguida, cada métrica e cada gráfico são lidos explicitamente: o que medem, por que importam, como interpretar e o que os dados mostram nesta matriz. As tabelas extensas foram movidas para o apêndice operacional para não interromper a análise.",
            r"\section{Arquitetura experimental}",
            r"A avaliação considera apenas a camada OLAP de consulta do Apache Druid. O teste não executa Kafka, Superset, ingestão nem tabela fato. A pergunta experimental é: com as dimensões já carregadas, qual perfil de Broker/Historical sustenta consultas analíticas sem erro?",
            f"O hardware local observado possui {hardware['cpu_count']} CPUs lógicas e aproximadamente {hardware['mem_total_gib']} GiB de RAM. A disponibilidade instantânea durante a geração do relatório foi de {hardware['mem_available_gib']} GiB. Esse contexto importa porque Druid usa memoria direta, heap e threads de processamento; em ambiente local, aumentar o perfil dos containers compete com o restante do sistema.",
            r"\begin{itemize}",
            r"\item \textbf{Broker}: planeja SQL, coordena fan-out e junta resultados. Ele sofre quando a consulta exige merge grande ou muitos joins.",
            r"\item \textbf{Historical}: varre segmentos persistidos e executa parte pesada das agregações. Foi o ponto de saturação nos cenários menores.",
            r"\item \textbf{Coordinator}: garante disponibilidade dos segmentos. Na matriz, seu papel foi validar loadstatus, não executar consulta.",
            r"\item \textbf{MiddleManager}: quase irrelevante neste experimento porque não houve ingestão.",
            r"\item \textbf{Router, Postgres, Zookeeper e Kafka}: dão suporte operacional, mas não aparecem como gargalo nos dados coletados.",
            r"\end{itemize}",
            r"\subsection{Perfis comparados}",
            r"\input{../tables/scenario_profiles.tex}",
            "Os três cenários alteram apenas os recursos dos nós de consulta, Broker e Historical. Isso preserva comparabilidade: os dados, queries, concorrências e modos cold/warm são os mesmos.",
            r"\clearpage",
            r"\section{Metodologia e métricas de leitura}",
            "A matriz usa 19 queries, concorrências 1, 2 e 4, e duas condições de cache: cold-start e warm-start. Cada resultado deve ser lido combinando vazão, latência de cauda e erro. O erro tem prioridade interpretativa: um cenário com QPS alto e erro alto não é estável.",
            r"\input{../tables/capacity_main_summary.tex}",
            "A tabela compacta acima é a âncora numérica do relatório. Ela mostra que o Baseline e o Balanced passam a falhar em concorrência 4, enquanto o Query Heavy mantém erro zero, ainda que com p95 maior.",
            r"\subsection{Resumo das métricas usadas}",
            r"\begin{itemize}",
            r"\item \textbf{QPS}: vazão de consultas finalizadas por segundo.",
            r"\item \textbf{p95/p99}: latência de cauda; mostram como o sistema se comporta para usuários menos favorecidos pela distribuição.",
            r"\item \textbf{Taxa de erro}: falhas HTTP, timeouts ou desconexões. Erro invalida comparação puramente por latência.",
            r"\item \textbf{Cold/warm}: aproxima diferença entre consulta fria e consulta repetida com cache.",
            r"\item \textbf{CPU/memória Docker}: evidência operacional do gargalo em Broker/Historical.",
            r"\end{itemize}",
            r"Definições completas estão no PDF \texttt{guia\_metricas\_benchmark.pdf}.",
            r"\section{Throughput: QPS por cenário}",
            r"\textbf{O que mede.} QPS mede quantas consultas completas o sistema entrega por segundo dentro de cada nível de concorrência.",
            r"\textbf{Por que importa.} Em painéis Superset, vários cards podem disparar consultas simultâneas. Um perfil útil precisa aumentar vazão sem perder confiabilidade.",
            r"\textbf{Como interpretar.} A curva ideal cresce com concorrência até o ponto de saturação. Queda de QPS com aumento de concorrência indica contenção, erro ou reset de conexão.",
            figure_block("qps_por_concorrencia.png", "Throughput por cenário e concorrência.", "qps"),
            rf"\textbf{{Leitura dos dados.}} O Balanced atinge {format_value(balanced_c2.get('qps'))} QPS em concorrência 2, melhor que o Baseline no mesmo ponto. Em concorrência 4, porém, o Query Heavy chega a {format_value(heavy_c4.get('qps'))} QPS com erro zero, enquanto Baseline e Balanced caem para {format_value(baseline_c4.get('qps'))} e {format_value(balanced_c4.get('qps'))} QPS com falhas.",
            r"\FloatBarrier",
            r"\section{Latência de cauda: p95 e p99}",
            r"\textbf{O que mede.} p95 e p99 mostram a cauda de resposta. Eles respondem: quão ruim fica para as consultas mais lentas que ainda completam?",
            r"\textbf{Por que importa.} Dashboards operacionais sofrem mais com cauda longa do que com média. Uma tela pode ficar bloqueada esperando a consulta mais lenta.",
            r"\textbf{Como interpretar.} Latência alta sem erro indica custo real de processamento. Latência baixa com erro alto pode ser enganosa, pois parte das consultas nem terminou.",
            figure_block("latencia_p95_p99.png", "Latência p95/p99 por cenário.", "latencia"),
            rf"\textbf{{Leitura dos dados.}} O Query Heavy em concorrência 4 tem p95 de {format_value(heavy_c4.get('lat_p95_ms'))} ms e p99 de {format_value(heavy_c4.get('lat_p99_ms'))} ms. Esse valor é alto, mas representa consultas concluídas. No Baseline e Balanced, a leitura de p95 em concorrência 4 deve ser subordinada à taxa de erro, pois houve perda de requisições.",
            r"\FloatBarrier",
            r"\section{Erro e saturação}",
            r"\textbf{O que mede.} A taxa de erro mede falhas reais observadas pelo cliente SQL. A classe SATURADO marca cenários em que erro ou limites operacionais invalidam estabilidade.",
            r"\textbf{Por que importa.} Em banco OLAP, falha intermitente é pior do que latência previsível: o usuário não recebe resultado e o painel pode quebrar.",
            r"\textbf{Como interpretar.} Qualquer barra acima de zero em benchmark pequeno deve ser tratada como evidência de limite operacional.",
            figure_block("taxa_erro.png", "Taxa de erro por cenário.", "erro"),
            rf"\textbf{{Leitura dos dados.}} Baseline em concorrência 4 registrou {int(baseline_c4.get('requests_erro', 0))} erros ({format_value(baseline_c4.get('error_rate_percent'))}\%). Balanced registrou {int(balanced_c4.get('requests_erro', 0))} erros ({format_value(balanced_c4.get('error_rate_percent'))}\%). Query Heavy manteve 0 erro.",
            r"\FloatBarrier",
            r"\section{Evidência operacional: CPU e memória}",
            r"\textbf{O que mede.} O gráfico compara picos de CPU e memória nos containers Broker e Historical.",
            r"\textbf{Por que importa.} Se a falha vem do Historical, aumentar apenas Broker não resolveria. A evidência operacional indica onde a carga encosta.",
            r"\textbf{Como interpretar.} CPU acima de 100\% indica uso de mais de um core lógico. Memória percentual menor em cenários maiores pode refletir limite maior, não menor consumo absoluto.",
            figure_block("docker_cpu_mem_picos.png", "Picos de CPU e memória em Broker e Historical.", "docker"),
            "A leitura operacional sustenta a interpretação: Query Heavy usa mais CPU em Broker e Historical, mas transforma recurso adicional em estabilidade. Baseline e Balanced falham antes de sustentar concorrência 4.",
            r"\FloatBarrier",
            r"\section{Cold-start, warm-start e hotspots}",
            r"\textbf{O que mede.} O ganho warm-start compara consultas frias e consultas repetidas com cache. O heatmap mostra quais queries concentram p95 alto.",
            r"\textbf{Por que importa.} Superset costuma repetir consultas parecidas quando filtros e painéis são usados. Cache ajuda, mas não substitui capacidade quando há joins pesados.",
            r"\textbf{Como interpretar.} Ganho de cache deve ser lido por query. Joins dimensionais podem continuar caros mesmo com cache, porque o custo de planejamento, merge e cardinalidade permanece.",
            figure_block("ganho_warm_start_top10.png", "Maiores ganhos de warm-start por p95.", "warm"),
            figure_block("heatmap_hotspots_queries.png", "Hotspots de latência p95 por query, cenário e cache.", "hotspots"),
            "Os hotspots se concentram nos joins dimensionais com hospitais, municípios e terras indígenas. Isso confirma que o gargalo não é apenas o volume de `path_json`, mas o cruzamento analítico sobre a maior dimensão.",
            r"\FloatBarrier",
            r"\section{Interpretação técnica}",
            "A comparação mostra que o perfil Query Heavy e o primeiro perfil estável para a carga avaliada. O Balanced é melhor para uso diário moderado, especialmente em concorrência 2, mas ainda não sustenta concorrência 4. O Baseline é útil como configuração econômica e controle experimental, não como perfil robusto para dashboards concorrentes.",
            "A conclusão não é que Druid seja lento; é que o par Broker/Historical precisa ser dimensionado de acordo com o tipo de consulta. Para dimensões batch e queries OLAP com joins, o Historical precisa de CPU e memória direta suficientes para varrer segmentos e manter canais estáveis.",
            r"\section{Rastreabilidade}",
            f"A matriz analisada está em \\texttt{{{latex_escape(str(matrix_dir.relative_to(PROJECT_ROOT)))}}}. Este relatório foi gerado a partir dos CSVs e JSONs ja consolidados, sem executar novo benchmark.",
        ]
    )
    lines.append(latex_end())
    tex.write_text("\n\n".join(lines), encoding="utf-8")


def write_metrics_guide(report_dir):
    tex = report_dir / "tex" / "guia_metricas_benchmark.tex"
    lines = [latex_preamble("Guia de métricas do benchmark Druid")]
    lines.extend(
        [
            r"\section{Objetivo do guia}",
            "Este guia define as métricas usadas nos relatórios de capacidade. Ele existe para evitar leituras equivocadas, como comparar QPS ignorando erro ou interpretar p95 baixo em um cenário que perdeu conexões.",
            r"\section{Glossário operacional}",
            r"\input{../tables/metric_definitions.tex}",
            r"\section{Como combinar métricas}",
            r"\subsection{QPS não deve ser lido sozinho}",
            "QPS mede vazão, mas não qualidade. Se duas configurações entregam QPS parecido, a melhor é a que mantém menor erro e menor p95. Se uma configuração aumenta QPS mas passa a falhar, ela atingiu saturação operacional.",
            r"\subsection{p95 e p99 explicam experiência de painel}",
            "A média pode parecer confortável quando poucas consultas são muito lentas. p95 e p99 mostram a cauda, que é o que bloqueia dashboards compostos: a tela espera o card mais lento.",
            r"\subsection{Erro tem prioridade interpretativa}",
            "Quando há erro, a latência dos sucessos não representa a carga inteira. Por isso Baseline e Balanced em concorrência 4 devem ser classificados como saturados mesmo quando algumas consultas retornaram rápido.",
            r"\subsection{Cold e warm start respondem perguntas diferentes}",
            "Cold-start aproxima o custo de leitura sem reaproveitamento. Warm-start aproxima repetição de painéis e filtros. Um bom perfil deve se beneficiar de warm-start, mas continuar confiável quando a consulta fria aparecer.",
            r"\subsection{CPU e memória mostram o mecanismo da falha}",
            "As métricas Docker não substituem as métricas SQL; elas explicam por que a curva se comportou daquele modo. Na matriz, Broker e Historical sobem CPU no Query Heavy e deixam de apresentar reset de canal.",
            r"\section{Critério de leitura adotado}",
            r"\begin{enumerate}",
            r"\item Verificar se loadstatus estava completo.",
            r"\item Verificar taxa de erro.",
            r"\item Comparar QPS apenas entre cenários sem erro equivalente.",
            r"\item Comparar p95/p99 para entender cauda operacional.",
            r"\item Usar Docker stats para explicar saturação.",
            r"\end{enumerate}",
        ]
    )
    lines.append(latex_end())
    tex.write_text("\n\n".join(lines), encoding="utf-8")


def write_query_catalog_report(report_dir, query_catalog):
    tex = report_dir / "tex" / "catalogo_queries_benchmark.tex"
    lines = [latex_preamble("Catálogo explicado das queries de benchmark Druid")]
    lines.extend(
        [
            r"\section{Como o catálogo está organizado}",
            "Cada query é documentada por família de carga. A família explica o conceito experimental; a query explica como esse conceito foi materializado em SQL. O objetivo não é só listar SQL, mas justificar por que a consulta mede uma propriedade relevante do Druid.",
            r"\section{Resumo das queries}",
            r"\input{../tables/query_catalog_summary.tex}",
        ]
    )

    catalog_df = pd.DataFrame(query_catalog)
    for categoria, guide in QUERY_FAMILY_GUIDE.items():
        group = catalog_df[catalog_df["categoria"] == categoria]
        if group.empty:
            continue
        lines.extend(
            [
                r"\clearpage",
                r"\section{" + latex_escape(guide["titulo"]) + "}",
                r"\textbf{Conceito base.} " + latex_escape(guide["conceito"]),
                r"\textbf{Hipótese testada.} " + latex_escape(guide["hipotese"]),
                r"\textbf{Por que existe.} " + latex_escape(guide["motivo"]),
                r"\textbf{Impacto esperado no Druid.} " + latex_escape(guide["impacto"]),
            ]
        )
        for _, query in group.iterrows():
            lines.extend(
                [
                    r"\subsection{" + latex_escape(query["query_id"]) + "}",
                    r"\textbf{Objetivo local.} " + latex_escape(query["objetivo"]) + r"\\",
                    r"\textbf{Datasource(s).} " + latex_escape(query["datasource"]) + r"\\",
                    r"\textbf{Padrão de carga.} " + latex_escape(query["padrao_carga"]) + r"\\",
                    r"\textbf{Visualização Superset simulada.} " + latex_escape(query["visualizacao"]) + r"\\",
                    r"\textbf{Motivo científico.} " + latex_escape(query["motivo_cientifico"]) + r"\\",
                    r"\textbf{Impacto esperado.} " + latex_escape(query["impacto_druid"]),
                    r"\begin{lstlisting}[language=SQL]",
                    query["sql"],
                    r"\end{lstlisting}",
                ]
            )
    lines.append(latex_end())
    tex.write_text("\n\n".join(lines), encoding="utf-8")


def write_operational_appendix(report_dir):
    tex = report_dir / "tex" / "apendice_evidencias_operacionais.tex"
    lines = [latex_preamble("Apêndice de evidências operacionais da matriz Druid")]
    lines.extend(
        [
            r"\section{Finalidade do apêndice}",
            "Este documento concentra as tabelas extensas. Ele serve para auditoria dos resultados sem poluir o relatório principal com tabelas largas.",
            r"\section{Capacidade por cenário e concorrência}",
            "Tabela completa com média, percentis, erros, QPS e classe de estabilidade.",
            r"\input{../tables/capacity_full_landscape.tex}",
            r"\clearpage",
            r"\section{Docker stats}",
            "Picos e médias de CPU/memória por container. Broker e Historical são os containers mais relevantes para consulta.",
            r"\input{../tables/docker_peaks_full.tex}",
            r"\section{Hotspots de query}",
            "Consultas ordenadas por p95. Esta tabela identifica onde investigar otimização de SQL, modelagem ou recursos.",
            r"\input{../tables/query_hotspots_full.tex}",
            r"\section{Ganho cold/warm}",
            "Comparação entre execução fria e aquecida por query. Ganho alto indica benefício de repetição/cache, não necessariamente estabilidade sob carga.",
            r"\input{../tables/cache_gain_full.tex}",
            r"\section{Erros}",
            "Resumo dos erros agregados por cenário, concorrência, query e cache.",
            r"\input{../tables/errors_full.tex}",
            r"\section{Segmentos e loadstatus}",
            "Segmentos e loadstatus comprovam que os datasources estavam disponíveis durante a comparação.",
            r"\input{../tables/loadstatus_summary.tex}",
        ]
    )
    if (report_dir / "tables" / "segments_summary.tex").exists():
        lines.append(r"\input{../tables/segments_summary.tex}")
    lines.extend(
        [
            r"\section{Arquivos de origem}",
            r"\begin{itemize}",
            r"\item \texttt{capacity\_comparison.csv}: consolidado por cenário e concorrência.",
            r"\item \texttt{query\_hotspots.csv}: maiores p95 por query, cache e cenário.",
            r"\item \texttt{cache\_gain\_by\_query.csv}: comparação cold/warm.",
            r"\item \texttt{docker\_peaks.csv}: picos e médias por container.",
            r"\item \texttt{scenario\_*/raw\_requests.csv}: evidência bruta por requisição.",
            r"\end{itemize}",
        ]
    )
    lines.append(latex_end())
    tex.write_text("\n\n".join(lines), encoding="utf-8")


def write_readme(report_dir, matrix_dir):
    try:
        report_ref = report_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        report_ref = report_dir

    readme = f"""# Relatórios de Capacidade Druid

Base de dados analisada: `{matrix_dir.relative_to(PROJECT_ROOT)}`

## Ordem recomendada de leitura

1. `pdf/relatorio_capacidade_druid.pdf`
2. `pdf/guia_metricas_benchmark.pdf`
3. `pdf/catalogo_queries_benchmark.pdf`
4. `pdf/apendice_evidencias_operacionais.pdf`

## Fontes

- `tex/`: fontes LaTeX dos quatro PDFs.
- `figures/`: gráficos gerados por `matplotlib`.
- `tables/`: CSVs e tabelas LaTeX derivadas da matriz.

## Reprodução

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/performance/generate_capacity_report_assets.py \\
  --matrix-dir {matrix_dir.relative_to(PROJECT_ROOT)}
scripts/performance/compile_capacity_reports.sh {report_ref}
```

Nenhum comando acima executa benchmark; eles apenas transformam evidências já
coletadas em documentação.
"""
    (report_dir / "README.md").write_text(readme, encoding="utf-8")


def generate(matrix_dir, output_dir=None, sql_dir=DEFAULT_SQL_DIR):
    matrix_dir = Path(matrix_dir).resolve()
    report_dir = Path(output_dir).resolve() if output_dir else DEFAULT_DOCS_ROOT / matrix_dir.name
    ensure_dirs(report_dir)
    clean_stale_reports(report_dir)

    capacity = read_csv(matrix_dir / "capacity_comparison.csv")
    docker_peaks = read_csv(matrix_dir / "docker_peaks.csv")
    query_hotspots = read_csv(matrix_dir / "query_hotspots.csv")
    cache_gain = read_csv(matrix_dir / "cache_gain_by_query.csv")

    capacity = add_enriched_columns(capacity)
    query_catalog = read_query_catalog(sql_dir)

    make_figures(report_dir, capacity, docker_peaks, cache_gain, query_hotspots)
    make_tables(report_dir, capacity, docker_peaks, query_hotspots, cache_gain, query_catalog, matrix_dir)
    write_main_report(report_dir, capacity, matrix_dir, hardware_snapshot())
    write_metrics_guide(report_dir)
    write_query_catalog_report(report_dir, query_catalog)
    write_operational_appendix(report_dir)
    write_readme(report_dir, matrix_dir)
    return report_dir


def parse_args():
    parser = argparse.ArgumentParser(description="Gera relatorios cientificos da matriz Druid.")
    parser.add_argument("--matrix-dir", type=Path, default=DEFAULT_MATRIX_DIR)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    report_dir = generate(args.matrix_dir, args.output_dir, args.sql_dir)
    print(f"Relatorios gerados em {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
