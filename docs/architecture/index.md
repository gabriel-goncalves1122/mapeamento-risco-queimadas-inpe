# Especificações de Arquitetura de Sistema (`docs/architecture/`)

> **Trilha Geral de Documentação**: [Portal Geral (`docs/README.md`)](../README.md) | [Iniciar Leitura: 01. Introdução e Proposta](01_introducao_e_proposta.md) | [Dicionários de Dados](../data_dictionary/index.md)

Este diretório apresenta a arquitetura completa do sistema **CCO DataOps (SIRDA)** estruturada na **ordem cronológica e cognitiva do ciclo de vida do dado** — partindo da definição do problema e fundamentação teórica, passando pela engenharia de software do núcleo (`src/core/`) e pelas camadas **Bronze**, **Silver** e **Gold**, até a orquestração no **Apache Dagster** e o servimento analítico no **Apache Druid** e **Apache Superset**.

Seguindo a topologia **Hub & Spoke**, cada capítulo sintetiza as decisões arquiteturais do ciclo e referencia diretamente as especificações técnicas modulares co-localizadas no código-fonte (`src/`, `infra/` e `scripts/`).

---

## Trilha Sequencial de Arquitetura (Capítulos 01 a 06)

```mermaid
flowchart TD
    C1["01. Introdução, Proposta do Projeto e Fundamentação Teórica<br>(Problema, 4 Eixos de Monitoramento, Endsley 1995, DataOps Ereth 2018)"]
    C2["02. Visão Geral da Arquitetura, Fluxo End-to-End e Engenharia Core<br>(Medallion, Modelagem Snowflake, Padrão FCIS/SOLID e Contratos src/core/)"]
    C3["03. Ciclo 1 — Camada Bronze: Aquisição Bruta e APIs Governamentais<br>(6 Provedores: INPE, ANEEL, FUNAI, IBGE, DNIT, CNES e Extratores HTTP)"]
    C4["04. Ciclos 2 e 3 — Camada Silver: Dimensões, Limpeza e Motor Espacial<br>(Funções de Limpeza, 7 ETLs EPSG:5880, 23 Lookups, STRtree e Índices)"]
    C5["05. Ciclo 4 — Camada Gold: Ciência de Dados e Publicação Kafka<br>(Grafos SIN NetworkX, ST-DBSCAN 3D em Janelas Fechadas e Streaming Dual-Branch)"]
    C6["06. Ciclo 5 — Orquestração Dagster, Motor OLAP Druid e Operação<br>(12 Software-Defined Assets, Cluster Druid 34.0, Superset e Scripts 01..05)"]

    C1 --> C2 --> C3 --> C4 --> C5 --> C6
```

| Capítulo | Documento Arquitetural | Escopo Técnico | Especificações Modulares Co-localizadas (Links Diretos) |
| :-: | :--- | :--- | :--- |
| **01** | [**`01_introducao_e_proposta.md`**](01_introducao_e_proposta.md) | Problema técnico, proposta do sistema, os 4 eixos operacionais (ONS, FUNAI, DNIT, CNES) e fundamentação teórica (Consciência Situacional, DataOps, ST-DBSCAN e Teoria dos Grafos). | • [`docs/domain/README.md`](../domain/README.md)<br>• [`docs/domain/ti_parque_araguaia_canoana.md`](../domain/ti_parque_araguaia_canoana.md) |
| **02** | [**`02_visao_geral_e_engenharia_core.md`**](02_visao_geral_e_engenharia_core.md) | Fluxo de dados End-to-End, modelagem Snowflake com Lookups em RAM, padrão *Functional Core / Imperative Shell* (FCIS), princípios SOLID e contratos base do núcleo. | • [`src/core/README.md`](../../src/core/README.md)<br>• [`docs/adr/README.md`](../adr/README.md) |
| **03** | [**`03_camada_bronze_ingestao.md`**](03_camada_bronze_ingestao.md) | Arquitetura da zona bruta imutável, particularidades e anomalias das 6 fontes governamentais (`-999`, `13P8`, `PopupInfo` HTML) e extratores paginados. | • [`src/bronze/README.md`](../../src/bronze/README.md)<br>• [`src/bronze/FONTES_E_APIS.md`](../../src/bronze/FONTES_E_APIS.md)<br>• [`src/bronze/DICIONARIO_DADOS.md`](../../src/bronze/DICIONARIO_DADOS.md) |
| **04** | [**`04_camada_silver_dimensoes_e_motor_espacial.md`**](04_camada_silver_dimensoes_e_motor_espacial.md) | Catálogo de funções puras de limpeza, reprojeção `EPSG:5880`, serialização `path_json`, ETL das 7 dimensões, validadores de QA, 23 Lookups URI, `MotorEspacial` (`STRtree`) e equações de índices sintéticos. | • [`src/silver/README.md`](../../src/silver/README.md)<br>• [`src/silver/utils/README.md`](../../src/silver/utils/README.md)<br>• [`src/silver/etl/README.md`](../../src/silver/etl/README.md)<br>• [`src/silver/DICIONARIO_DADOS.md`](../../src/silver/DICIONARIO_DADOS.md)<br>• [`src/silver/validators/README.md`](../../src/silver/validators/README.md)<br>• [`src/silver/spatial/README.md`](../../src/silver/spatial/README.md)<br>• [`src/silver/streaming_processing/README.md`](../../src/silver/streaming_processing/README.md) |
| **05** | [**`05_camada_gold_ciencia_e_streaming.md`**](05_camada_gold_ciencia_e_streaming.md) | Centralidade de intermediação na malha do SIN (`SINNetworkCentralityModel`), clusterização espaço-temporal 3D em janelas fechadas (`EventizadorIncendios`) e publicação Kafka Dual-Branch. | • [`src/gold/README.md`](../../src/gold/README.md)<br>• [`src/gold/ARQUITETURA.md`](../../src/gold/ARQUITETURA.md)<br>• [`src/gold/streaming/README.md`](../../src/gold/streaming/README.md)<br>• [`src/gold/DICIONARIO_DADOS.md`](../../src/gold/DICIONARIO_DADOS.md) |
| **06** | [**`06_orquestracao_olap_e_operacao.md`**](06_orquestracao_olap_e_operacao.md) | Grafo de 12 Software-Defined Assets no Apache Dagster, topologia de 5 nós do Apache Druid 34.0 (`LZ4`, `Roaring`, `sample_bucket`), dashboards Superset e scripts operacionais e de benchmark. | • [`src/orchestration/README.md`](../../src/orchestration/README.md)<br>• [`infra/README.md`](../../infra/README.md)<br>• [`scripts/README.md`](../../scripts/README.md) |
