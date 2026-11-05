# CCO DataOps (SIRDA): Sistema de Inteligência e Resposta a Desastres Ambientais

![Version](https://img.shields.io/badge/version-v2.0.0-success?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white&style=flat-square)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-Streaming-black?logo=apachekafka&logoColor=white&style=flat-square)
![Apache Druid](https://img.shields.io/badge/Apache_Druid-OLAP-cyan?logo=apache&logoColor=white&style=flat-square)
![Apache Superset](https://img.shields.io/badge/Apache_Superset-BI-red?logo=apache&logoColor=white&style=flat-square)
![Dagster](https://img.shields.io/badge/Dagster-Orchestration-blue?style=flat-square)

O **CCO DataOps (SIRDA)** é uma plataforma de engenharia e ciência de dados em streaming e OLAP projetada para monitoramento de queimadas e avaliação de risco sobre infraestruturas críticas nacionais: **Sistema Interligado Nacional (ONS/ANEEL)**, **Terras Indígenas (FUNAI)**, **Rodovias Federais (DNIT)** e **Rede Hospitalar (CNES/DATASUS)**.

O sistema estrutura-se sob a arquitetura **Medallion (Bronze, Silver, Gold)** com modelagem dimensional **Snowflake**, separação entre **Núcleo Funcional e Casca Orientada a Objetos (FCIS / SOLID)**, orquestração declarativa via **Apache Dagster**, ingestão contínua via **Apache Kafka**, armazenamento colunar no **Apache Druid 34.0** e visualização geoespacial no **Apache Superset**.

---

## 1. Ordem de Leitura da Documentação Técnica

A documentação segue o padrão **Hub & Spoke Descentralizado**. O portal central encontra-se em [**`docs/README.md`**](docs/README.md).

### 1.1 Trilha de Arquitetura Geral (`docs/architecture/01..06`)
Recomendada para leitura inicial na ordem cronológica de concepção e fluxo do sistema:
1. [**01. Introdução, Proposta do Projeto e Fundamentação Teórica**](docs/architecture/01_introducao_e_proposta.md) — Definição do problema, os 4 eixos operacionais e referenciais de Consciência Situacional (Endsley, 1995) e DataOps (Ereth, 2018).
2. [**02. Visão Geral da Arquitetura, Fluxo End-to-End e Engenharia Core**](docs/architecture/02_visao_geral_e_engenharia_core.md) — Fluxo Medallion completo, modelagem Snowflake, padrão FCIS/SOLID e contratos do núcleo (`src/core/`).
3. [**03. Ciclo 1 — Camada Bronze: Aquisição Bruta e APIs Governamentais**](docs/architecture/03_camada_bronze_ingestao.md) — Coleta imutável dos 6 provedores oficiais (INPE, ANEEL, FUNAI, IBGE, DNIT, CNES).
4. [**04. Ciclos 2 e 3 — Camada Silver: Dimensões, Limpeza e Motor Espacial**](docs/architecture/04_camada_silver_dimensoes_e_motor_espacial.md) — Sanitização funcional, reprojeção `EPSG:5880`, 7 dimensões CSV, 23 Lookups URI, `MotorEspacial` (`STRtree`) e índices matemáticos.
5. [**05. Ciclo 4 — Camada Gold: Ciência de Dados (ST-DBSCAN e Grafos SIN) e Kafka**](docs/architecture/05_camada_gold_ciencia_e_streaming.md) — Centralidade de intermediação no SIN (`NetworkX`), clusterização espaço-temporal 3D em janelas fechadas e publicação Kafka Dual-Branch.
6. [**06. Ciclo 5 — Orquestração Dagster, Motor OLAP Apache Druid e Operação**](docs/architecture/06_orquestracao_olap_e_operacao.md) — Grafo de 12 Software-Defined Assets, topologia de 5 nós do Druid 34.0, dashboards Superset e automação CLI.

### 1.2 Trilha de Especificações Modulares por Ciclo (Etapas `01` a `18`)
Cada módulo do código-fonte possui documentação técnica detalhada co-localizada, encadeada sequencialmente:

| Ciclo | Etapas | Módulos e Especificações Co-localizadas |
| :--- | :-: | :--- |
| **Ciclo 0 — Núcleo e Contratos** | `01` | • [`01. src/core/README.md`](src/core/README.md) (Constantes, `PipelineSettings`, Protocolos e Payloads Pydantic) |
| **Ciclo 1 — Camada Bronze** | `02`–`04` | • [`02. src/bronze/README.md`](src/bronze/README.md) (Extratores `AneelArcGisExtractor` e `InpeQueimadasExtractor`)<br>• [`03. src/bronze/FONTES_E_APIS.md`](src/bronze/FONTES_E_APIS.md) (Endpoints, parâmetros HTTP e particularidades das 6 fontes)<br>• [`04. src/bronze/DICIONARIO_DADOS.md`](src/bronze/DICIONARIO_DADOS.md) (Esquemas brutos originais) |
| **Ciclo 2 — Camada Silver (Batch Dimensional)** | `05`–`09` | • [`05. src/silver/README.md`](src/silver/README.md) (Hub da Camada Silver)<br>• [`06. src/silver/utils/README.md`](src/silver/utils/README.md) (Funções puras de limpeza, chaves, geometria e `PathJsonCodec`)<br>• [`07. src/silver/etl/README.md`](src/silver/etl/README.md) (Pipelines ETL das 7 dimensões em `EPSG:5880`)<br>• [`08. src/silver/DICIONARIO_DADOS.md`](src/silver/DICIONARIO_DADOS.md) (Dicionário físico das 7 dimensões CSV)<br>• [`09. src/silver/validators/README.md`](src/silver/validators/README.md) (Validadores de QA e catálogo dos 23 Lookups URI do Druid) |
| **Ciclo 3 — Camada Silver (Motor Espacial e Índices)** | `10`–`11` | • [`10. src/silver/spatial/README.md`](src/silver/spatial/README.md) (`MotorEspacial`, `SpatialLayer` `STRtree` e `DistanceClassifier`)<br>• [`11. src/silver/streaming_processing/README.md`](src/silver/streaming_processing/README.md) (`transformar_foco`, `extractor.py` e equações de `calculators.py`) |
| **Ciclo 4 — Camada Gold (Ciência e Streaming)** | `12`–`15` | • [`12. src/gold/README.md`](src/gold/README.md) (Hub da Camada Gold)<br>• [`13. src/gold/ARQUITETURA.md`](src/gold/ARQUITETURA.md) (Modelos `EventizadorIncendios` ST-DBSCAN e `SINNetworkCentralityModel` NetworkX)<br>• [`14. src/gold/streaming/README.md`](src/gold/streaming/README.md) (`KafkaStreamClient`, `StreamingAuditLogger` e produtores de streaming)<br>• [`15. src/gold/DICIONARIO_DADOS.md`](src/gold/DICIONARIO_DADOS.md) (Dicionário das tabelas fato `FATO_FOCOS` e `FATO_EVENTOS`) |
| **Ciclo 5 — Orquestração, OLAP e CLI** | `16`–`18` | • [`16. src/orchestration/README.md`](src/orchestration/README.md) (Grafo de 12 Software-Defined Assets no Apache Dagster)<br>• [`17. infra/README.md`](infra/README.md) (Cluster Apache Druid 34.0, specs de ingestão, perfis de hardware e Superset)<br>• [`18. scripts/README.md`](scripts/README.md) (Scripts operacionais `01..05`, manutenção e suíte de benchmarks) |

### 1.3 Governança, Dicionários, Benchmarks e Produção Científica (`docs/`)
- [**Índice Geral de Dicionários de Dados (`docs/data_dictionary/index.md`)**](docs/data_dictionary/index.md)
- [**Registros de Decisão de Arquitetura — ADRs 001 a 006 (`docs/adr/README.md`)**](docs/adr/README.md)
- [**Contexto Territorial — TI Parque do Araguaia (`docs/domain/README.md`)**](docs/domain/README.md)
- [**Especificações de Hardware, Docker e Dependências (`docs/technical_specs/README.md`)**](docs/technical_specs/README.md)
- [**Avaliação de Desempenho e Capacidade do Druid (`docs/performance/README.md`)**](docs/performance/README.md)
- [**Produção Científica — Relatório Final, Artigo SBC e Pôster (`docs/academic/README.md`)**](docs/academic/README.md)

---

## 2. Procedimentos de Execução Local

Todos os comandos Python do projeto devem ser executados por meio do gerenciador de pacotes e ambientes virtuais `uv`.

### 2.1 Sincronização de Dependências e Testes Automatizados
```bash
uv sync
uv run pytest -v
```

### 2.2 Execução Direta de Módulos (ETL, Grafos e Validação)
```bash
# Geração paralela das 7 dimensões espaciais (Camada Silver)
uv run python src/silver/etl/run_etl.py

# Cálculo de Betweenness Centrality e Risco de Cascata no SIN (Camada Gold)
uv run python src/gold/science/networkx/network_builder.py

# Validação de integridade primária e referencial das dimensões Silver
uv run python src/silver/validators/dimension_Normalizer_validator.py
uv run python src/silver/validators/valida_joins_municipios_hospital.py
```

### 2.3 Execução Sequencial da Stack Completa (`scripts/run/`)
```bash
# Execução ponta a ponta (ETL -> Grafos -> Docker/Kafka -> Druid Lookups/Batch -> Streaming)
./scripts/run_all.sh

# Inicialização e importação de dashboards no Apache Superset
./scripts/bootstrap_stack.sh
```

### 2.4 Orquestração via Apache Dagster
```bash
uv run dagster dev -f src/orchestration/dagster/repo.py
```

### 2.5 Portas dos Serviços Locais
- **Apache Dagster UI**: `http://localhost:3000`
- **Apache Druid Router / Console**: `http://localhost:8888`
- **Apache Druid Broker (SQL Endpoint)**: `http://localhost:8082`
- **Apache Superset**: `http://localhost:8088` (credenciais padrão: `admin` / `admin`)

---

*Projeto desenvolvido por Gabriel Gonçalves Sampaio no âmbito de Iniciação Científica em Engenharia de Computação — Universidade Federal de Itajubá (UNIFEI).*
