# Superset SQL Context

Este diretorio contem consultas de apresentacao para datasets virtuais e charts do
Apache Superset. Elas complementam `scripts/sql/validation`, que continua sendo a
camada de QA tecnico.

## Regras

- Use somente `SELECT` ou `WITH ... SELECT`.
- Use dimensoes ativas no Druid e a fato agregada `fato_eventos_incendio`.
- Nao referencie `fato_focos_incendio`, `fogo_eventos_stdbscan`, `dim_rel_*` ou
  datasources antigos de benchmark.
- JOINs sao permitidos quando ajudam a apresentar cruzamentos dimensionais no
  Superset; prefira chaves nativas ja resolvidas no ETL.
- Para saude com a fato de eventos, nunca faca join amplo
  `fato_eventos_incendio -> dim_hospitais_cnes`: primeiro agregue por
  `fk_hospital`, depois faca lookup limitado ou use a dimensao como tabela base.
- Para mapas Deck.gl, exponha `path_json`, `latitude` e `longitude` quando
  existirem.
- Cada SQL deve ter comentarios de metadados no topo com setor, objetivo,
  datasource, granularidade e visualizacao sugerida.
