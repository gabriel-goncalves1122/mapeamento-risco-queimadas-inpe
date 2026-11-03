# 🔥 CCO-DataOps: Sistema de Inteligência e Resposta a Desastres Ambientais

![Version](https://img.shields.io/badge/version-v2.0.0-success?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white&style=flat-square)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-Streaming-black?logo=apachekafka&logoColor=white&style=flat-square)
![Apache Druid](https://img.shields.io/badge/Apache_Druid-OLAP-cyan?logo=apache&logoColor=white&style=flat-square)
![Apache Superset](https://img.shields.io/badge/Apache_Superset-Viz-red?logo=apache&logoColor=white&style=flat-square)
![Dagster](https://img.shields.io/badge/Dagster-Orchestration-blue?style=flat-square)

Bem-vindo ao repositório do **CCO-DataOps**, uma infraestrutura analítica de ponta a ponta desenvolvida para atuar como o núcleo de um Centro de Controle e Operações (CCO).

Este sistema processa dados climáticos e coordenadas de focos de incêndio em tempo real, fornecendo consciência situacional em sub-segundos para a tomada de decisão em cenários de missão crítica.

---

## 🏗️ Arquitetura Medallion & Fluxo de Dados

O fluxo de dados foi desenhado seguindo a arquitetura **Medallion**, orientada a objetos (POO) com princípios **SOLID**, orquestrada via **Dagster** e escalada via **Docker**.

### 1. Camada Bronze (Raw/Ingestion)
Classes extratoras especializadas (`AneelArcGisExtractor`) coletam dados brutos governamentais (INPE, ONS, FUNAI, IBGE, DNIT, CNES) com injeção de dependências e técnicas de *chunking* para evitar esgotamento de memória.
- **Responsabilidade**: Coletar dados como vieram da fonte e assegurar proveniência.

### 2. Camada Silver (Conformed/Cleaned)
Camada de processamento espacial vetorial e conformação dimensional estruturada em classes herdeiras de `BaseETL` e `ExecutablePipelineStep`.
- **Responsabilidade**: Gerar Dimensões analíticas padronizadas cruzando geometrias espaciais via *R-Tree* e indexação policônica (EPSG:5880).
- *Ferramentas*: GeoPandas, Shapely, PyProj.

### 3. Camada Gold (Science/Serving)
A camada que consome as Dimensões e aplica cálculos complexos, gerando Tabelas Fato focadas em performance analítica.
- **Machine Learning**: `EventizadorIncendios` agrupa focos de incêndio (espaço e tempo) em manchas poligonais (*Convex Hull*) via ST-DBSCAN.
- **Teoria dos Grafos**: `SINNetworkCentralityModel` calcula a Centralidade de Intermediação (*Betweenness Centrality*) das subestações via NetworkX, quantificando riscos de colapso em cascata no ONS.
- **Streaming de Última Milha**: Envio de payloads Fato extremamente enxutos, usando apenas IDs (Snowflake Schema), via Apache Kafka (`KafkaStreamClient` como Context Manager).

### 4. Motores de Performance (A Ponta do Iceberg)
- **Mensageria (Apache Kafka):** Atua como um *buffer* de resiliência, absorvendo picos extremos de dados gerados por desastres.
- **Motor Analítico (Apache Druid):** O coração OLAP colunar. Indexa os dados utilizando compressão LZ4 e bitmaps *Roaring*, permitindo agregações temporais ultrarrápidas em ~35ms.
- **Camada de Visualização (Apache Superset):** Consome os dados do Druid para renderizar mapas táticos e dashboards gerenciais.

---

## 🎯 Casos de Uso: Os Eixos de Operação

Os *dashboards* no Apache Superset foram projetados com foco em UX analítico para três autarquias específicas:
- ⚡ **Operador Nacional do Sistema (ONS):** Prevenção de blecautes e monitoramento de contingência N-2 em subestações de alta centralidade.
- 🏹 **Proteção Territorial (FUNAI / IBAMA):** Matrizes de alerta que filtram anomalias térmicas e pressão de borda estritamente dentro das delimitações de Terras Indígenas (ex: TI Parque do Araguaia).
- 🚒 **Comando da Defesa Civil:** Mapas geoespaciais e curvas temporais para prever o avanço e o perímetro dinâmico do fogo.

---

## 📚 Navegação da Documentação

A documentação adota um modelo **descentralizado por camadas** na arquitetura Medalhão, com governança executiva em `docs/`:

### Documentação Especializada por Camada
- 🥉 **Camada Bronze**: [Guia da Camada](src/bronze/README.md) | [Fontes e APIs Governamentais](src/bronze/FONTES_E_APIS.md) | [Dicionário de Esquemas Brutos](src/bronze/DICIONARIO_DADOS.md)
- 🥈 **Camada Silver**: [Guia da Camada e Motor Espacial](src/silver/README.md) | [Dicionário de Dimensões Conformadas](src/silver/DICIONARIO_DADOS.md)
- 🥇 **Camada Gold**: [Guia da Camada e Streaming](src/gold/README.md) | [Arquitetura POO e Modelos](src/gold/ARQUITETURA.md) | [Dicionário das Tabelas Fato](src/gold/DICIONARIO_DADOS.md)
- ⚙️ **Orquestração**: [Guia de Assets Dagster e Execução In-Memory](src/orchestration/README.md)

### Guias Sistêmicos e Acadêmicos (`docs/`)
- 🏛️ [Portal de Governança Geral](docs/README.md)
- 📖 [Índice Geral de Dicionários de Dados](docs/data_dictionary/index.md)
- 🏛️ [Guias de Arquitetura e Engenharia](docs/architecture/index.md)
  - [Streaming e OLAP (Kafka + Druid)](docs/architecture/01_streaming_e_olap.md)
  - [Orquestração e Medallion (Dagster)](docs/architecture/02_orquestracao.md)
  - [Data Science e Modelagem Preditiva](docs/architecture/03_data_science.md)
  - [Referencial Teórico (SIRDA)](docs/architecture/04_referencial_teorico.md)
  - [Data Flow End-to-End](docs/architecture/05_data_flow_end_to_end.md)
  - [Arquitetura POO e Princípios SOLID](docs/architecture/06_arquitetura_poo_solid.md)
- 🎓 [Portfólio Técnico e Síntese de Competências](iniciacao.md)

---

## 🚀 Como Executar o Projeto Localmente

O ambiente é 100% conteinerizado e automatizado (Monorepo Python com gestão determinística via `uv`).

### 1. Pré-requisitos
- Docker e Docker Compose instalados.
- `uv` (Package Manager em Rust) instalado para execução Python reprodutível.
- Recomendado: Mínimo de 8GB de RAM dedicados ao Docker.

### 2. Sincronização e Testes (Ambiente Local)
Sincronize as dependências num ambiente virtual via `uv` e execute a suíte de testes:
```bash
uv sync
uv run pytest -v
```

### 3. Execução Orientada a Objetos (Classes / Python Direto)
As etapas de processamento foram modeladas como classes herdando de `ExecutablePipelineStep`, permitindo execução direta e isolada:
```bash
# Execução da Camada Silver: orquestração de todas as 7 dimensões espaciais
uv run python src/silver/etl/run_etl.py

# Execução da Camada Gold: cálculo do modelo de grafos do SIN (Betweenness Centrality)
uv run python src/gold/science/networkx/network_builder.py

# Validação estrutural de integridade (Hospitais vs Municípios)
uv run python src/silver/validators/valida_joins_municipios_hospital.py
```

### 4. Pipeline Completa Automatizada (Scripts de Etapas)
Para subir a infraestrutura Docker e disparar o fluxo integrado:
```bash
# Etapa 1: Ingestão e Geração das Dimensões Espaciais (Camada Silver)
./scripts/run/01_etl_batch.sh

# Etapa 2: Aplicação de Algoritmos Preditivos e Grafos (Camada Gold)
./scripts/run/02_modelos_ciencia.sh

# Etapa 3: Subir Kafka e Infraestrutura (Docker)
./scripts/run/03_docker_e_kafka.sh

# Etapa 4: Ingerir Dimensões e Lookups no Druid OLAP
./scripts/run/04_druid_dimensoes.sh

# Etapa 5: Iniciar o Streaming Contínuo dos Sensores Orbitais
./scripts/run/05_streaming_eventos.sh
```

### 5. Inicializando o Apache Superset
Como o Superset necessita de configurações de segurança, execute o utilitário na raiz:
```bash
./scripts/bootstrap_stack.sh
```

### 6. Orquestrador Dagster
Para visualizar e ativar as pipelines via interface gráfica do Dagster, inicie o `dev server`:
```bash
uv run dagster dev -m pipelines.orchestration.repo
```

### 7. Acessando as Interfaces

Com tudo rodando, acesse através do seu navegador:
- 🐙 **Orquestrador Dagster:** http://localhost:3000
- 🗄️ **Apache Druid (Console de Ingestão e SQL):** http://localhost:8888
- 📊 **Apache Superset (Dashboards Operacionais):** http://localhost:8088
  *(Login padrão: `admin` | Senha: `admin`)*

---

*Este projeto foi desenvolvido por Gabriel Gonçalves Sampaio como parte de pesquisa vinculada ao curso de Engenharia de Computação da Universidade Federal de Itajubá (UNIFEI).*

## Acervo histórico
Materiais legados, templates acadêmicos, e backups históricos ficam em `legacy/`. A árvore principal mantém apenas código operacional e documentação viva.
