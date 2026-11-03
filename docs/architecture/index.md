# 🏛️ Guias de Arquitetura e Engenharia

Estes guias documentam o **porquê** por trás de cada escolha arquitetônica no projeto, focando em performance, escalabilidade, manutenibilidade e confiabilidade analítica.

## Tópicos Disponíveis

1. [Streaming e OLAP (Kafka + Druid)](01_streaming_e_olap.md)
   _Como alcançamos latência reduzida cruzando milhares de dados geoespaciais e evitamos gargalos de I/O em picos de desastres._

2. [Orquestração e Medallion (Dagster)](02_orquestracao.md)
   _Como os assets fluem da extração bruta (Bronze) até o preparo algorítmico (Ouro) de forma observável e tolerante a falhas._

3. [Data Science e Modelagem Preditiva](03_data_science.md)
   _Como convertemos focos isolados em Eventos Orgânicos (ST-DBSCAN) e calculamos Riscos de Cascata na malha do ONS (Grafos de Transmissão)._

4. [Referencial Teórico e Formulações](04_referencial_teorico.md)
   _Fundamentação matemática e teórica dos índices de ameaça, propagação térmica, topologia de rede e vulnerabilidade territorial._

5. [Data Flow End-to-End](05_data_flow_end_to_end.md)
   _Fluxo ponta a ponta desde as APIs governamentais e sensoriamento orbital até Kafka, Apache Druid e dashboards no Apache Superset._

6. [Arquitetura POO e Princípios SOLID](06_arquitetura_poo_solid.md)
   _Design orientado a objetos, decomposição em 1 Classe por Arquivo (SRP), desacoplamento por Protocolos (ISP/DIP), Template Method e diagramas Mermaid de classes, sequência e Snowflake ER._
