# Relatórios de Capacidade Druid

Base de dados analisada: `data/results/performance/druid_capacity/20260630_000802`

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
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/performance/generate_capacity_report_assets.py \
  --matrix-dir data/results/performance/druid_capacity/20260630_000802
scripts/performance/compile_capacity_reports.sh docs/performance/druid_capacity/20260630_000802
```

Nenhum comando acima executa benchmark; eles apenas transformam evidências já
coletadas em documentação.
