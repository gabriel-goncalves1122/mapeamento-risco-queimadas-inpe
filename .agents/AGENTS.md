# CCO DataOps - Source Code Context (Agent Guide)

Bem-vindo ao diretório raiz `src/`. Este documento orienta Agentes de IA sobre o contexto arquitetural do projeto, padronização e execução de comandos. **LEIA ATENTAMENTE**.

## 🔴 Regras de Ouro para Execução de Comandos (CRÍTICO)
1. **Nunca utilize o binário global `python` ou `pytest`.** 
2. Este projeto utiliza o `uv` como gerenciador de dependências e ambientes virtuais ultrarrápido em Rust. Todos os comandos Python DEVEM, sem exceção, ser executados através dele:
   - ✅ Correto: `uv run python script.py` ou `uv run pytest`
   - ✅ Correto: `uv run dagster dev ...`
   - ❌ Errado: `python script.py` ou `pytest` (Isso polui o sistema global ou não acha dependências)
3. Trabalhe preferencialmente com `uv` para gestão de dependências (`uv add pacote`, `uv run comando`, `uv sync`). Nunca use `pip install`.

## 🏢 Arquitetura de Dados e Hierarquia (Medallion / Snowflake)
O projeto baseia-se num sistema de ingestão de dados em Streaming (Kafka -> Apache Druid -> Apache Superset) utilizando uma arquitetura analítica do tipo **Snowflake**, dividida pelas camadas Medallion. 

1. **Camada de Orquestração (`pipelines/orchestration/`)**: Define o grafo de assets do Dagster. **Nenhum script roda solto/órfão.**
2. **Camada Bronze (`pipelines/bronze/`)**: Extração de dados brutos (APIs do INPE, ONS, FUNAI).
3. **Camada Silver (`pipelines/silver/`)**: Processa as Dimensões estáticas (Hospitais, Rodovias, Municípios). Cruza geometrias usando `shapely` e `geopandas`. Persiste em `pipelines/silver/data/dimensions`.
4. **Camada Gold (`pipelines/gold/`)**: Scripts de Ciência de Dados e Produção Kafka. A Tabela Fato `FATO_FOCOS_INCENDIO` é estruturada aqui. O payload **NÃO** deve conter strings redundantes (como nomes de municípios ou classes de vulnerabilidade), exceto FKs (identificadores) e Métricas.
5. **Configurações e Shared (`config/` e `scripts/`)**: Constantes ficam em `config/`. Scripts bash operacionais ficam em `scripts/etapas/`.
6. **Legado e Análises (`legacy/analytics/`)**: Centraliza relatórios gráficos offline.

## 🛡️ Regras Globais para Agentes
- **Atenção aos Paths**: **Nunca** tente importar de diretórios que não existem mais (como `src.etl` ou `src.streaming`). Os imports devem seguir a estrutura `pipelines.silver.*`, `pipelines.gold.*`, etc.
- **Sem Strings na Fato**: Nunca adicione colunas puramente textuais (`nome_X`, `classe_Y`) no payload de streaming. Isso quebra o modelo Snowflake. Use FKs para apontar para as Dimensões.
- **Tipagem Forte**: Utilize `Pydantic` para definir contratos de dados estritos no payload Kafka.
- **Antes de Codar**: Consulte os `DICIONARIO_DADOS.md` nas pastas Silver e Gold para saber a estrutura correta.

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
