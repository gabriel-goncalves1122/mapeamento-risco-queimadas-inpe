# Performance SQL Context

Consultas neste diretorio existem para forcar cenarios OLAP no Druid e medir
comportamento sob carga. Elas nao sao datasets finais do Superset.

## Regras

- Cada arquivo deve conter uma unica consulta `SELECT` ou `WITH ... SELECT`.
- Nao use comandos mutantes, ingestion specs, Kafka ou tabelas de fato.
- Inclua metadados no topo: `categoria`, `objetivo`, `datasource`,
  `padrao_carga` e `visualizacao`.
- JOINs dimensionais sao permitidos quando simulam exploracao real de painel.
- Evite `ORDER BY` em scans puros por coluna nao temporal; prefira agregacoes
  ordenadas ou deixe a ordenacao para o consumidor.
