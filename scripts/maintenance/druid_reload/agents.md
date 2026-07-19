# Druid Operational Scripts Context

Este diretorio contem scripts que alteram estado operacional do Druid/Kafka.

## Regras

- Scripts destrutivos devem ter `--dry-run`, `--yes` e uma confirmacao clara.
- Scripts focados na fato de eventos nao podem apagar nem reingerir dimensoes.
- Sempre resete metadados/offsets do supervisor e termine o supervisor antes de
  apagar topico Kafka ou datasource Druid.
- Ao recriar topico Kafka em offset zero, confirme que o supervisor novo inicia
  com `startingOffsets` em zero; lag negativo indica offset herdado.
- Ao reiniciar a fato `fato_eventos_incendio`, salve evidencias em
  `data/results/ingestion/fato_eventos/<timestamp>/`.
- Valide `lag = 0`, offsets Kafka, `COUNT(*)` e `SUM(total_focos)` antes de
  considerar a ingestao concluida.
- Comentarios devem explicar decisoes de seguranca operacional, como reset de
  topico, kill task e granularidade de segmentos.
