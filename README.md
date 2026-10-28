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

O fluxo de dados foi desenhado seguindo uma rigorosa arquitetura **Medallion**, orquestrado via **Dagster** e escalado via **Docker**.

### 1. Camada Bronze (Raw/Ingestion)
Scripts Python extraem dados de fontes governamentais (INPE, ONS, FUNAI, IBGE, DNIT, CNES). O processamento utiliza técnicas de _chunking_ para evitar o esgotamento de memória.
- **Responsabilidade**: Coletar dados como vieram da fonte.

### 2. Camada Silver (Conformed/Cleaned)
Camada de processamento pesado espacial e ETL tabular. 
- **Responsabilidade**: Gerar Dimensões analíticas tratadas (CSVs padronizados) cruzando geometrias espaciais.
- *Ferramentas*: Pandas, Shapely, PyProj.

### 3. Camada Gold (Science/Serving)
A camada que consome as Dimensões e aplica cálculos complexos, gerando Tabelas Fato focadas em performance.
- **Machine Learning**: ST-DBSCAN agrupa Focos de Incêndio (espaço e tempo) em Eventos maiores.
- **Teoria dos Grafos**: Centralidade de Intermediação (_Betweenness_) de Subestações via NetworkX, predizendo risco de colapso em cascata no ONS.
- **Streaming de Última Milha**: Envio de payloads Fato extremamente enxutos, usando apenas IDs (Snowflake Schema), via Apache Kafka.

### 4. Motores de Performance (A Ponta do Iceberg)
- **Mensageria (Apache Kafka):** Atua como um _buffer_ de resiliência. Garante que picos extremos de dados gerados por desastres não derrubem o banco de dados.
- **Motor Analítico (Apache Druid):** O coração OLAP. Indexa os dados utilizando compressão LZ4 e bitmaps _Roaring_ permitindo agregações temporais ultrarrápidas em ~35ms.
- **Camada de Visualização (Apache Superset):** Consome os dados do Druid para renderizar mapas táticos e dashboards.

---

## 🎯 Casos de Uso: Os Eixos de Operação

Os _dashboards_ embutidos no Apache Superset foram projetados com foco em UX analítico para três autarquias específicas:
- ⚡ **Operador Nacional do Sistema (ONS):** Prevenção de blecautes. Ranqueando infraestruturas com maior risco eletromagnético.
- 🏹 **Proteção Territorial (FUNAI / IBAMA):** Matrizes de alerta que filtram anomalias térmicas estritamente dentro das delimitações de Terras Indígenas.
- 🚒 **Comando da Defesa Civil:** Mapas geoespaciais e curvas temporais para prever o pico do fogo.

---

## 📚 Navegação da Documentação

A documentação detalhada foi dividida nos seguintes eixos para facilitar o entendimento técnico:
- 📖 [Dicionários de Dados das Camadas](docs/data_dictionary/index.md) *(Em construção)*
- 🏛️ [Guias de Arquitetura e Engenharia](docs/architecture/index.md) *(Em construção)*

---

## 🚀 Como Executar o Projeto Localmente

O ambiente é 100% conteinerizado e automatizado (Monorepo Python).

### 1. Pré-requisitos
- Docker e Docker Compose instalados.
- `uv` (Package Manager em Rust) instalado para execução Python reprodutível.
- Recomendado: Mínimo de 8GB de RAM dedicados ao Docker.

### 2. Sincronização e Testes (Ambiente Local)
Sincronize as dependências num ambiente virtual via `uv` e execute os testes independentes:
```bash
uv sync
uv run pytest -v
```

### 3. Pipeline Simplificada (Scripts de Etapas)
Para rodar todo o ecossistema (da extração até o streaming interativo), utilize a pasta `scripts/etapas`:

```bash
# Etapa 1: Ingestão e Geração das Dimensões Espaciais (Camada Silver)
./scripts/etapas/01_etl_batch.sh

# Etapa 2: Aplicação de Algoritmos Preditivos e Grafos (Camada Gold)
./scripts/etapas/02_modelos_ciencia.sh

# Etapa 3: Subir Kafka e Infraestrutura (Docker)
./scripts/etapas/03_docker_e_kafka.sh

# Etapa 4: Ingerir Dimensões e Lookups no Druid OLAP
./scripts/etapas/04_druid_dimensoes.sh

# Etapa 5: Iniciar o Streaming Contínuo dos Sensores Orbitais
./scripts/etapas/05_streaming_eventos.sh
```

### 4. Inicializando o Apache Superset
Como o Superset necessita de configurações de segurança, execute o utilitário na raiz:
```bash
./scripts/bootstrap_stack.sh
```

### 5. Orquestrador Dagster
Para visualizar e ativar as pipelines via interface gráfica do Dagster, inicie o `dev server`:
```bash
uv run dagster dev -m pipelines.orchestration.repo
```

### 6. Acessando as Interfaces

Com tudo rodando, acesse através do seu navegador:
- 🐙 **Orquestrador Dagster:** http://localhost:3000
- 🗄️ **Apache Druid (Console de Ingestão e SQL):** http://localhost:8888
- 📊 **Apache Superset (Dashboards Operacionais):** http://localhost:8088
  *(Login padrão: `admin` | Senha: `admin`)*

---

*Este projeto foi desenvolvido por Gabriel Gonçalves Sampaio como parte de pesquisa vinculada ao curso de Engenharia de Computação da Universidade Federal de Itajubá (UNIFEI).*

## Acervo histórico
Materiais legados, templates acadêmicos, e backups históricos ficam em `legacy/`. A árvore principal mantém apenas código operacional e documentação viva.
