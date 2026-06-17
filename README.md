# 🔥 CCO-DataOps: Sistema de Inteligência e Resposta a Desastres Ambientais

![Version](https://img.shields.io/badge/version-v2.0.0-success?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white&style=flat-square)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-Streaming-black?logo=apachekafka&logoColor=white&style=flat-square)
![Apache Druid](https://img.shields.io/badge/Apache_Druid-OLAP-cyan?logo=apache&logoColor=white&style=flat-square)
![Apache Superset](https://img.shields.io/badge/Apache_Superset-Viz-red?logo=apache&logoColor=white&style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white&style=flat-square)

Bem-vindo ao repositório do **CCO-DataOps**, uma infraestrutura analítica de ponta a ponta desenvolvida para atuar como o núcleo de um Centro de Controle e Operações (CCO).

Este sistema processa dados climáticos e coordenadas de focos de incêndio em tempo real, fornecendo consciência situacional em sub-segundos para a tomada de decisão em cenários de missão crítica.

---

## 🧠 A Ciência por Trás: Superando o Gargalo de I/O

Em arquiteturas de _Big Data_ focadas em resposta a desastres, o desafio não é apenas armazenar os dados, mas sim a **latência de recuperação**. Quando um incêndio avança em direção a uma subestação de energia, o sistema não pode demorar minutos para varrer milhões de coordenadas espaciais.

A arquitetura deste projeto foi submetida a testes rigorosos de _benchmark_ cruzando o poder de processamento (2, 4 e 6 núcleos) com a **geometria física dos dados** no disco. A conclusão provou empiricamente que a injeção bruta de hardware (_Scale-Up_) sofre retornos decrescentes (Lei de Amdahl) se os dados estiverem fragmentados.

Ao implementar esteiras de **DataOps** para a compactação automatizada dos dados, consolidando micro-segmentos em blocos físicos otimizados, o sistema alcançou um desempenho notável: um ambiente estrangulado de apenas 2 núcleos lendo a base compactada revelou-se **~14 vezes mais rápido** do que um cluster em potência máxima tentando ler dados fragmentados. A latência analítica sobre uma base de ~3,1 milhões de registros foi esmagada para **~35 milissegundos**.

---

## 🏗️ Arquitetura do Pipeline

O fluxo de dados foi desenhado para ser resiliente e escalável, orquestrado inteiramente via containers Docker:

1. **Ingestão Otimizada:** Scripts Python extraem dados de fontes governamentais (INPE BDQueimadas e API NASA POWER). O processamento utiliza técnicas de _chunking_ para evitar o esgotamento de memória (OOM) ao lidar com arquivos CSVs massivos.
2. **Mensageria (Apache Kafka):** Atua como um _buffer_ de resiliência (desacoplamento). Garante que picos extremos de dados gerados por desastres em larga escala não derrubem o banco de dados.
3. **Motor Analítico (Apache Druid):** O coração OLAP do projeto. Indexa os dados utilizando compressão LZ4 e bitmaps _Roaring_, permitindo agregações temporais e cálculos geoespaciais ultrarrápidos.
4. **Camada de Visualização (Apache Superset):** Consome os dados do Druid para renderizar painéis táticos, mapas de calor interativos e tabelas de priorização em tempo real.

---

## 🎯 Casos de Uso: Os Eixos de Operação

Os _dashboards_ embutidos no Apache Superset foram projetados com foco em UX analítico para três autarquias específicas:

- ⚡ **Operador Nacional do Sistema (ONS):** Prevenção de blecautes. Cruzamento de polígonos de calor com a malha de linhas de transmissão de alta voltagem, ranqueando as infraestruturas com maior risco eletromagnético e de ruptura de cabos.
- 🏹 **Proteção Territorial (FUNAI / IBAMA):** Salvaguarda de biomas. Matrizes de alerta que filtram anomalias térmicas (FRP - _Fire Radiative Power_) estritamente dentro das delimitações de Terras Indígenas cadastradas.
- 🚒 **Comando da Defesa Civil:** Alocação de viaturas e evacuação. Mapas geoespaciais de calor de alta densidade e curvas temporais de contágio para prever o pico diário do fogo em municípios em estado de alerta.

---

## 🚀 Como Executar o Projeto Localmente

O ambiente foi empacotado para ser 100% reprodutível em qualquer máquina que suporte conteinerização.

### 1. Pré-requisitos

- Docker e Docker Compose instalados.
- `uv` instalado para execução Python reprodutível.
- Recomendado: Mínimo de 8GB de RAM dedicados ao Docker.

### 2. Ambiente Python e Testes

Sincronize as dependências e rode a suíte local sempre via `uv`:

```bash
uv sync
uv run pytest -q
```

Em ambientes com cache restrito, use:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q
```

### 3. Subindo a Infraestrutura Core

Clone o repositório e inicialize a rede de containers (Zookeeper, Kafka, Druid, PostgreSQL e Superset):

```bash
# Inicia todos os serviços em segundo plano
docker compose up -d
```

### 4. Pipelines Locais

Os pontos de entrada principais são:

```bash
uv run python -m src.etl.run_etl
uv run python -m src.streaming.produtor_focos
uv run dagster dev -m src.orchestration.repo
```

### 5. Inicializando o Apache Superset

Como o Superset necessita de configurações de segurança e metadados internos, execute os comandos abaixo em sequência para preparar a camada visual:

#### 5.1 Criar o usuário administrador do CCO

    docker exec -it superset superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname CCO \
    --email admin@superset.com \
    --password admin

#### 5.2 Atualizar as migrações do banco de dados interno

    docker exec -it superset superset db upgrade

#### 5.3 Inicializar papéis e permissões padrão

    docker exec -it superset superset init

### 6. Acessando as Interfaces

Com tudo rodando, acesse através do seu navegador:

    🗄️ Apache Druid (Console de Ingestão e SQL): http://localhost:8888

    📊 Apache Superset (Dashboards Operacionais): http://localhost:8088

        Login: admin

        Senha: admin

Este projeto foi desenvolvido por Gabriel Gonçalves Sampaio como parte de pesquisa vinculada ao curso de Engenharia de Computação da Universidade Federal de Itajubá (UNIFEI).

A pesquisa documentada neste repositório explora a intersecção entre a Engenharia de Dados Moderna, o planejamento de hardware e a visualização tática de dados aplicados a cenários de resposta a crises.

## Acervo histórico

Materiais legados, templates acadêmicos, relatórios antigos, referências pesadas e backups históricos do Superset ficam em `archive/legacy/`. A árvore principal mantém apenas código, documentação ativa e artefatos operacionais recentes.
