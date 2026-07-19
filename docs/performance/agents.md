# Performance Documentation Context

Esta pasta guarda relatorios tecnicos e cientificos derivados dos benchmarks do
Druid local. A documentacao deve favorecer rastreabilidade, reproducibilidade e
interpretacao conservadora dos resultados.

## Regras

- Escreva em portugues tecnico direto, sem introducao generica quando o relatorio
  for analitico.
- Cite explicitamente a matriz analisada, os scripts usados e as restricoes:
  dimensoes apenas, sem fato, sem Kafka, sem Superset e sem reingestao quando for
  o caso.
- Figuras e tabelas devem ser geradas por script a partir de CSV/JSON; evite
  valores digitados manualmente no LaTeX.
- Separe relatorio principal de apendices quando houver catalogo de queries ou
  metricas operacionais extensas.
- O relatorio principal deve ser uma leitura guiada, nao um despejo de tabelas:
  explique cada metrica antes de interpretar o grafico e discuta o resultado logo
  apos a figura.
- Nao extrapole resultados locais como capacidade absoluta do Druid. Explique o
  hardware, os limites de CPU/memoria e o papel de Broker/Historical na leitura.
- Preserve evidencias negativas: erros, timeouts, resets e saturacao fazem parte
  do resultado cientifico.
- Use guias separados para glossario de metricas e catalogo de queries quando o
  texto principal ficaria longo demais.
- Use `path_json`, nomes de datasources e queries exatamente como estao nos
  artefatos de benchmark para manter o vinculo com Superset/Druid.
- Use `scripts/performance/capacity_metadata.py` como fonte de verdade para
  perfis Baseline, Balanced e Query Heavy nos relatorios.
