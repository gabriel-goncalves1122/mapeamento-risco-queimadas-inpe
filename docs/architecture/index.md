# 🏛️ Guias de Arquitetura e Engenharia

Estes guias documentam o **porquê** por trás de cada escolha arquitetônica no projeto, focando em performance, escalabilidade e manutenibilidade.

## Tópicos Disponíveis

1. [Streaming e OLAP (Kafka + Druid)](01_streaming_e_olap.md)
   _Como alcançamos latência de ~35ms cruzando milhares de dados geoespaciais e evitamos gargalos de I/O em picos de desastres._

2. [Orquestração e Medallion (Dagster)](02_orquestracao.md)
   _Como os assets fluem da extração bruta (Bronze) até o preparo algorítmico (Ouro) de forma observável e tolerante a falhas._

3. [Data Science e Modelagem Preditiva](03_data_science.md)
   _Como convertemos focos isolados em Eventos Orgânicos (ST-DBSCAN) e calculamos Riscos de Cascata na malha do ONS (Grafos)._
