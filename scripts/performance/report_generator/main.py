import argparse
import sys
import os
from pathlib import Path
from scripts.performance.capacity_metadata import DEFAULT_DOCS_ROOT, DEFAULT_MATRIX_DIR, DEFAULT_SQL_DIR, PROJECT_ROOT
from .metadata_parser import read_query_catalog, QUERY_FAMILY_GUIDE
from .figures import make_figures
from .latex_writer import latex_escape, latex_preamble, latex_end, figure_block, format_value
from .tables import make_tables, add_enriched_columns, read_csv
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
  --matrix-dir {matrix_dir.relative_to(PROJECT_ROOT)} \\
  --sql-dir infrastructure/superset/queries/performance
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
