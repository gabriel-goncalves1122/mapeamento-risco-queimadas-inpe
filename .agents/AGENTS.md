# CCO DataOps - Source Code Context (Agent Guide)

Bem-vindo ao diretório raiz `src/`. Este documento orienta Agentes de IA sobre o contexto arquitetural do projeto, padronização e execução de comandos. **LEIA ATENTAMENTE**.

## 🔴 Regras de Ouro para Execução de Comandos (CRÍTICO)
1. **Nunca utilize o binário global `python` ou `pytest`.** 
2. Este projeto utiliza o `uv` como gerenciador de dependências e ambientes virtuais ultrarrápido em Rust. Todos os comandos Python DEVEM, sem exceção, ser executados através dele:
   - ✅ Correto: `uv run python script.py` ou `uv run pytest`
   - ✅ Correto: `uv run dagster dev -f src/orchestration/dagster/repo.py`
   - ❌ Errado: `python script.py` ou `pytest` (Isso polui o sistema global ou não acha dependências)
3. Trabalhe preferencialmente com `uv` para gestão de dependências (`uv add pacote`, `uv run comando`, `uv sync`). Nunca use `pip install`.

## 🏢 Arquitetura de Dados e Hierarquia (Medallion / Snowflake)
O projeto baseia-se num sistema de ingestão de dados em Streaming (Kafka -> Apache Druid -> Apache Superset) utilizando uma arquitetura analítica do tipo **Snowflake**, dividida pelas camadas Medallion sob o diretório `src/`. 

1. **Camada de Orquestração (`src/orchestration/`)**: Define o grafo de assets do Dagster. **Nenhum script roda solto/órfão.**
2. **Camada Bronze (`src/bronze/`)**: Extração de dados brutos (APIs do INPE, ONS, FUNAI). Persiste em `src/bronze/data/`.
3. **Camada Silver (`src/silver/`)**: Processa as Dimensões estáticas (Hospitais, Rodovias, Municípios). Cruza geometrias usando `shapely` e `geopandas`. Persiste em `src/silver/data/dimensions`.
4. **Camada Gold (`src/gold/`)**: Scripts de Ciência de Dados e Produção Kafka. A Tabela Fato `FATO_FOCOS_INCENDIO` é estruturada aqui. O payload **NÃO** deve conter strings redundantes (como nomes de municípios ou classes de vulnerabilidade), exceto FKs (identificadores) e Métricas. Persiste em `src/gold/data/`.
5. **Núcleo Compartilhado (`src/core/`)**: Contratos abstratos (`src/core/contracts/`), contratos Pydantic (`src/core/domain/`) e constantes/configurações (`src/core/config/`).
6. **Infraestrutura e Scripts (`infra/` e `scripts/`)**: Configurações de Docker, Druid e Superset em `infra/`. Scripts operacionais em `scripts/run/`, `scripts/maintenance/`, `scripts/benchmarks/` e `scripts/setup/`.
7. **Legado e Análises (`legacy/analytics/`)**: Centraliza relatórios gráficos offline.

## 🛡️ Regras Globais para Agentes (Padrão FCIS — `arquitetura-dados-pragmatica`)
1. **Núcleo Funcional para Dados (Functional Core)**:
   - Toda e qualquer transformação, sanitização, enriquecimento, cálculo matemático ou feature engineering deve ser estruturada como **função pura e sem estado** (`Data In -> Data Out`, preferencialmente `DataFrame -> DataFrame`).
   - É **proibido** criar classes para apenas uma função de transformação (anti-padrão *"Stop Writing Classes"* / Javaficação do Python). O arquivo `.py` (módulo) já é o namespace.
   - **Vetorização em primeiro lugar**: nunca instancie objetos linha a linha para iterar sobre DataFrames (destrói o throughput colunar).
   - Funções puras devem ser 100% determinísticas, idempotentes e testáveis em milissegundos com pequenos DataFrames sintéticos no `pytest`, sem depender de mocks de rede ou banco.
2. **Casca Orientada a Objetos para Infraestrutura (OO Shell)**:
   - Use POO e princípios SOLID estritos **exclusivamente** onde há gerenciamento real de estado e ciclo de vida:
     - Conexões de rede, sockets e buffers (Kafka, PostgreSQL, S3, MinIO) gerenciados obrigatoriamente via Context Managers (`__enter__` e `__exit__`) para flush e fechamento determinísticos.
     - Clientes de API HTTP externos que exigem paginação, controle de taxa (*rate-limiting*), retentativas e sessão persistente.
     - Estruturas pesadas em memória que devem ser cacheadas (árvores espaciais R-Tree, cKDTree, grafos NetworkX) para consultas $O(\log N)$.
     - Recursos e adaptadores de orquestração (`Dagster ConfigurableResource` / `IOManagers`).
   - **Inversão de Dependência (DIP)**: toda classe de infraestrutura deve aceitar clientes/sessões injetados no construtor para permitir testes unitários em memória sem contêineres Docker.
3. **Rigor de Contratos nas Bordas, Flexibilidade no Miolo**:
   - **Bordas do Sistema** (Ingestão externa, Mensageria/Kafka e Carga na Tabela Fato): rigor estrito de schema e tipagem usando `Pydantic` ou Dataclasses imutáveis.
   - **Modelagem Analítica Snowflake**: a tabela Fato deve conter **exclusivamente** Chaves Estrangeiras (FKs), métricas numéricas e timestamps/geometrias. **Nunca** insira strings textuais redundantes (`nome_X`, `classe_Y`) no payload da Fato — essas pertencem exclusivamente às Tabelas Dimensão.
   - **Miolo Analítico**: mantenha o processamento intermediário flexível, livre e vetorizado (Polars, Pandas, DuckDB).
4. **Pragmatismo Operacional e Scripts Procedurais**:
   - Ferramentas de linha de comando (CLI), rotinas de manutenção (`scripts/maintenance/`), diagnósticos de banco, backfills únicos (*one-off*) e scripts de setup/deploy (`scripts/setup/`) devem ser **scripts procedurais diretos** (`if __name__ == "__main__":`), sem classes abstratas artificiais.
5. **Atenção aos Paths e Dicionário de Dados**:
   - **Nunca** tente importar de diretórios legados (`pipelines.*`, `config.*` ou `src.etl`). Os imports devem seguir a estrutura `src.silver.*`, `src.gold.*`, `src.core.*`, etc.
   - Consulte os `DICIONARIO_DADOS.md` nas pastas Silver e Gold antes de codificar.

## 📝 Comentários e Legibilidade
Comentários devem explicar a intenção técnica e a regra de domínio por trás do código, não narrar operações óbvias do Python.

- **Comente o porquê**: deixe contexto antes de blocos com regra de negócio, CRS, geometria, thresholds, fallback, compatibilidade com Druid/Superset ou decisões de performance.
- **Docstrings obrigatórias em contratos públicos**: funções/classes públicas, pipelines, transformações ETL, contratos Pydantic e pontos de entrada CLI devem declarar propósito, entradas relevantes e efeito esperado.
- **Origem da regra**: ao tratar dados, cite de forma curta se a decisão vem de INPE, ONS, CNES, Druid, Superset, CRS geográfico/métrico ou limitação de payload.
- **Evite ruído**: não escreva comentários como "incrementa contador", "retorna valor", "cria lista" ou qualquer frase que apenas repete a linha seguinte.
- **Comentários curtos e vivos**: se um comentário ficar maior que o código que explica, prefira extrair uma função com nome claro e docstring objetiva.

## 📐 Padrões Arquiteturais para Criação de Diagramas TikZ
A estruturação visual deste projeto exige clareza absoluta, sem conectores sobrepostos ou geometria confusa. Ao manipular ou criar arquivos LaTeX na pasta `diagrams/`:
1. **Regra das Portas Ortogonais**: Interligue os fluxos direcionais utilizando obrigatoriamente as âncoras nominais (ex: `.east` saindo, `.west` entrando).
2. **Geometria Lógica e Sem Overlap**: Abandone comandos de roteamento curvilíneo ou elástico caótico (`to[out=..., in=...]`) em arquiteturas de sistema. Empregue roteamento ortogonal limpo com quebras explícitas `([xshift=Xcm]no_A.east) |- (no_B.west)`. Estruture o grid baseado em colunas fixas por coordenadas `(X, Y)` em vez de posicionamento relativo indiscriminado (`right of`).
3. **Identidade Medallion**: Categorize zonas de agrupamento no `background layer` (com `fit`) seguindo a taxonomia:
   - *Camada Bronze*: `fill=orange!5, draw=orange!40!brown`
   - *Camada Silver*: `fill=gray!8, draw=gray!50`
   - *Camada Gold / Streaming*: `fill=yellow!10, draw=yellow!60!orange`
   - Mantenha a fonte dos títulos dessas boundaries *sempre na cor preta* (`\color{black}`) para contraste universal.
4. **Legibilidade de Rótulos de Arestas**: Rótulos sobre linhas (`node[lbl]`) precisam ter um background de proteção contra o traço inferior, geralmente com `fill=white, draw=gray!40, inner sep=3pt`.
5. **Tipologia de Elementos (Shapes)**: Fica proibido o uso elástico de `text width` para caixas visuais! Use dimensões rígidas `minimum width` e `minimum height` para todos os estilos para forçar padronização em bloco.
   - **Bancos de Dados/Tabelas**: `database/.style={cylinder, shape border rotate=90, cylinder end fill=gray!10}`.
   - **Tópicos e Mensageria (Kafka/Filas)**: `queue/.style={chamfered rectangle, draw=blue!50, fill=cyan!5}`.
   - **Processamento e APIs**: `process/.style={rectangle, rounded corners=4pt}` e `source/.style={tape}`.
   - **Payloads**: `payload/.style={ellipse}`.
