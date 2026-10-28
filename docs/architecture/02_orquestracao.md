# Orquestração e a Jornada Medallion via Dagster

O **Dagster** é o sistema nervoso da engenharia de dados deste projeto. Ao invés de *scripts soltos* rodando via Cron, definimos uma linhagem clara de *Assets* declarativos (O quê deve existir e Quando).

## A Arquitetura Medallion
As dependências do pipeline refletem estritamente a arquitetura Medallion de Qualidade de Dados:

1. **Bronze (O Início - *Raw*):** Tarefas de Scraping, Requisições API e coleta FTP (`pipelines/bronze/`). Estes Assets apenas vomitam dados físicos brutos no sistema.
2. **Silver (A Limpeza - *Conformed*):** Assets que declaram a Bronze como dependência paterna. O Dagster dispara cálculos geométricos massivos em Pandas/Shapely para gerar as "Dimensões" fixas e corretas do ecossistema.
3. **Gold (A Entrega - *Serving*):** Assets analíticos pesados. É aqui que entram os scripts de ML e Teoria dos Grafos. Produzem respostas diretas para os Tópicos do Kafka e Druid.

## Orquestração baseada em Partição
Em dados climáticos (Focos de Incêndio), os updates são constantes (Diários ou Horários). O Dagster está configurado para operar em janelas de particionamento (Ex: Rodar ETL para a partição `2024-09-01`). Isso garante que um erro no meio de Setembro não force um reprocessamento dos dados de Janeiro (Idempotência).
