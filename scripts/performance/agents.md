# Performance Scripts Context

Esta pasta contem ferramentas para medir latencia, carga e robustez do Apache
Druid local. Benchmarks devem gerar evidencias reproduziveis sem alterar dados.

## Regras

- Execute com `uv run python scripts/performance/...`.
- Use somente consultas `SELECT` contra o Broker SQL do Druid.
- Nao referencie `fato_focos_incendio`, `fogo_eventos_stdbscan`, `dim_rel_*` ou
  datasources legados.
- Salve sempre resultados em diretorios timestampados dentro de
  `data/results/performance/`.
- O perfil padrao deve ser progressivo. Modo extremo precisa de flag explicita.
- Colete Docker stats quando possivel, mas nao transforme falta de permissao no
  Docker em falha do benchmark SQL.
- Comentarios devem explicar o motivo do cenario de carga: latencia, agregacao,
  join dimensional, payload espacial ou simulacao de dashboard.
- Metadados de cenarios de capacidade devem viver em
  `scripts/performance/capacity_metadata.py`. Nao replique CPU, memoria,
  threads ou nomes de cenario em scripts Python de relatorio/consolidacao.

## Relatorios cientificos

- Relatorios de performance devem consumir resultados persistidos; nao rerode
  benchmark dentro de scripts de relatorio.
- Toda figura e tabela deve ser derivada de CSV/JSON versionado em
  `data/results/performance/`, com caminho da matriz citado no README do
  relatorio.
- Separe cold-start e warm-start em arquivos/metricas distintos sempre que a
  comparacao de cache fizer parte da tese experimental.
- Trate erros de canal, timeout e reset como evidencia operacional. Nao remova
  essas linhas para "limpar" o resultado.
- Ao escrever LaTeX, explique arquitetura, metodologia, trade-offs e limites do
  hardware local antes de interpretar ganhos de QPS ou latencia.
- Cada grafico no relatorio principal deve ter quatro partes proximas: o que
  mede, por que importa, como interpretar e leitura objetiva do resultado.
- Tabelas largas devem ficar em apendice operacional, preferencialmente em
  `landscape` ou com colunas `p{}`. O relatorio principal deve usar tabelas
  compactas e explicadas no texto.
- Catalogos de queries devem explicar conceito da familia, hipotese testada,
  motivo cientifico, impacto esperado no Druid e SQL completo.
- Compile PDFs com `pdflatex` em chamadas sequenciais e confira a existencia do
  PDF final; avisos de LaTeX nao devem ser confundidos automaticamente com falha.
