import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scripts.performance.capacity_metadata import SCENARIO_LABELS
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

