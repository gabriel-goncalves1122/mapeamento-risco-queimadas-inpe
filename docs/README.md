# Documentação Científica: Plataforma DataOps para Monitoramento Geoespacial de Focos de Incêndio

## Escopo do Projeto
Este repositório documenta a arquitetura, os modelos preditivos e a topologia de dados desenvolvida para o projeto de Iniciação Científica (IC). O sistema consiste em uma plataforma de Engenharia de Dados orientada a eventos (Event-Driven Architecture) acoplada a módulos de Ciência de Dados espaciais, destinada à modelagem, ingestão e análise de focos de incêndio florestal no território nacional e suas intersecções com infraestruturas críticas (e.g., Sistema Interligado Nacional, Terras Indígenas e Estabelecimentos de Saúde).

A abordagem empregada afasta-se de metodologias monolíticas tradicionais, incorporando pipelines escaláveis via Apache Kafka e Apache Druid, além da orquestração rigorosa de dependências utilizando Dagster. O rigor analítico é assegurado pela integração de modelos de Ciência de Redes (Network Science) e algoritmos de clusterização de densidade espaço-temporal (ST-DBSCAN).

## Sumário Executivo da Documentação
Para uma compreensão sistêmica da plataforma, a documentação está estratificada nas seguintes vertentes ontológicas:

1. [Fundamentação e Topologia Arquitetural](./01_introducao/arquitetura.md)
2. [Diagramas Arquiteturais e Científicos](./01_introducao/diagramas.md)
3. [Modelagem Dimensional Snowflake e Extração Espacial](./02_dados_e_etl/modelo_snowflake.md)
4. [Processamento Geoespacial (ETL Batch)](./02_dados_e_etl/etl_geospacial.md)
5. [Ingestão e Processamento Contínuo (Kafka e Druid)](./03_streaming/kafka_e_druid.md)
6. [Modelagem de Centralidade em Grafos (SIN)](./04_ciencia_de_dados/grafos_networkx.md)
7. [Clusterização Espaço-Temporal Multivariável (ST-DBSCAN)](./04_ciencia_de_dados/clusterizacao_st_dbscan.md)
8. [Governança de Pipelines (Dagster)](./05_dataops/orquestracao_dagster.md)
9. [Gerenciamento de Infraestrutura via Contêineres](./05_dataops/docker_infra.md)

## Acervo Histórico

Materiais pesados ou históricos, como templates da SBC, relatórios antigos, referências em PDF e backups do Superset, foram movidos para `../archive/legacy/`. A pasta `docs/` deve permanecer focada nas fontes ativas da documentação.
