# CCO DataOps - Source Code Context (Agent Guide)

Bem-vindo ao diretório raiz `src/`. Este documento orienta Agentes de IA sobre o contexto arquitetural do projeto, padronização e execução de comandos. **LEIA ATENTAMENTE**.

## 🔴 Regras de Ouro para Execução de Comandos (CRÍTICO)
1. **Nunca utilize o binário global `python` ou `pytest`.** 
2. Este projeto utiliza o `uv` como gerenciador de dependências e ambientes virtuais ultrarrápido em Rust. Todos os comandos Python DEVEM, sem exceção, ser executados através dele:
   - ✅ Correto: `uv run python script.py` ou `uv run pytest`
   - ✅ Correto: `uv run dagster dev ...`
   - ❌ Errado: `python script.py` ou `pytest` (Isso polui o sistema global ou não acha dependências)
3. Trabalhe preferencialmente com `uv` para gestão de dependências (`uv add pacote`, `uv run comando`, `uv sync`). Nunca use `pip install`.

## 🏢 Arquitetura de Dados e Hierarquia (Snowflake Schema)
O projeto baseia-se num sistema de ingestão de dados em Streaming (Kafka -> Apache Druid -> Apache Superset) utilizando uma arquitetura analítica do tipo **Snowflake**. 

1. **Camada de Orquestração (`src/orchestration/`)**: Define o grafo de assets do Dagster. **Nenhum script roda solto/órfão.**
2. **Camada ETL / Batch (`src/etl/`)**: Processa as Dimensões estáticas (Hospitais, Rodovias, etc). Persiste em `data/processed/dimensions`.
3. **Camada Espacial (`src/spatial/`)**: Carrega as Dimensões (GeoDataFrames) e processa os cruzamentos espaciais vetoriais (Distâncias e Interseções).
4. **Camada de Streaming (`src/streaming/`)**: Processa Focos de Incêndio (Kafka) e gera a tabela fato `FATO_FOCOS_INCENDIO`. O payload **NÃO** deve conter strings redundantes (como nomes de municípios ou classes de vulnerabilidade), exceto FKs (identificadores) e Métricas (Distâncias Contínuas e Índices).
5. **Camada Analítica (`src/analytics/` e `scripts/sql/superset/`)**: Centraliza relatórios gráficos, SQLs setoriais e consultas de apoio sobre o Apache Druid. Benchmarks antigos ficam em `archive/legacy/analytics/`.
6. **Camada de Ciência/Redes (`src/science/`)**: Contém os algoritmos complexos de Machine Learning (como `st_dbscan_clustering.py` para agrupar focos de incêndio no espaço-tempo) e Inteligência Analítica em Grafos (como `network_builder.py` para o Risco de Cascata no ONS).
7. **Camada de Configuração (`src/config/`)**: Centraliza constantes globais (`constants.py`) e resolução de caminhos de dimensões (`settings.py`). Nenhum script de pipeline deve "inventar" paths; todos devem importar desta camada.
8. **Camada de Utilidades (`src/utils/`)**: Funções de limpeza textual (`cleaners.py`) reutilizáveis por todas as camadas do sistema.

## 🛡️ Regras Globais para Agentes
- **Sem Strings na Fato**: Nunca adicione colunas puramente textuais (`nome_X`, `classe_Y`) no payload de streaming. Isso quebra o modelo Snowflake. Use FKs para apontar para as Dimensões.
- **Tipagem Forte**: Utilize `Pydantic` (em `src/streaming/domain/models.py`) para definir contratos de dados estritos.
- **Antes de Codar**: Sempre leia o `agents.md` do subdiretório em que você está operando para respeitar as regras locais de Engenharia de Dados.

## 📝 Comentários e Legibilidade
Comentários devem explicar a intenção técnica e a regra de domínio por trás do código, não narrar operações óbvias do Python.

- **Comente o porquê**: deixe contexto antes de blocos com regra de negócio, CRS, geometria, thresholds, fallback, compatibilidade com Druid/Superset ou decisões de performance.
- **Docstrings obrigatórias em contratos públicos**: funções/classes públicas, pipelines, transformações ETL, contratos Pydantic e pontos de entrada CLI devem declarar propósito, entradas relevantes e efeito esperado.
- **Origem da regra**: ao tratar dados, cite de forma curta se a decisão vem de INPE, ONS, CNES, Druid, Superset, CRS geográfico/métrico ou limitação de payload.
- **Evite ruído**: não escreva comentários como "incrementa contador", "retorna valor", "cria lista" ou qualquer frase que apenas repete a linha seguinte.
- **Comentários curtos e vivos**: se um comentário ficar maior que o código que explica, prefira extrair uma função com nome claro e docstring objetiva.
