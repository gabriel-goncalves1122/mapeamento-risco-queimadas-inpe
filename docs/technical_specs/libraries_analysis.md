# Análise de Dependências e Bibliotecas Python - CCO DataOps

O ecossistema analítico do **CCO-DataOps** opera sobre o interpretador **Python 3.12**, com governança determinística e resolução de dependências em milissegundos provida pelo gerenciador moderno **Astral `uv`** (desenvolvido em Rust).

Todas as dependências declaradas no [`pyproject.toml`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/pyproject.toml) refletem escolhas técnicas fundamentadas em alta vazão, aceleração em código nativo C/C++ e rigor de contratos de dados.

---

## 🚀 1. Governança de Ambiente com Astral `uv`

Em conformidade com a regra de ouro do projeto:
* O uso de binários globais (`python`, `pip`, `virtualenv`) é terminantemente proibido.
* Toda a operação é isolada no ambiente virtual `.venv` gerenciado pelo `uv`:
  - Instalação e sincronização determinística: `uv sync`.
  - Execução de scripts com isolamento de `PYTHONPATH`: `uv run python ...`.
  - Execução da suíte de testes: `uv run pytest`.
  - Inclusão e fixação de pacotes no lockfile: `uv add <pacote>`.

---

## 🧩 2. Core DataOps, Tipagem e Contratos

* **`pydantic` (v2.x) e `pydantic-settings`**:
  - Aplica validação estrita de tipos nas bordas do sistema (Camada Gold -> Kafka -> Apache Druid).
  - Os contratos [`FocoFatoPayload`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/domain/foco_fato_payload.py) e [`EventoFatoPayload`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/domain/evento_fato_payload.py) utilizam `ConfigDict(frozen=True, extra="forbid")`, assegurando imutabilidade completa e veto sumário a valores `NaN` ou `Inf` que quebrariam o parser JSON do Druid.
* **`dagster` (>= 1.13.9) e `dagster-webserver`**:
  - Orquestrador declarativo baseado em *Software-Defined Assets* (SDA).
  - Executa as etapas do pipeline diretamente em memória compartilhada via instâncias de [`ExecutablePipelineStep`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/contracts/contracts.py), eliminando o custo de inicialização de subprocessos externos e oferecendo rastreabilidade de linhagem e telemetria nativa.
* **`kafka-python-ng`**:
  - Driver cliente de mensageria assíncrona para Apache Kafka.
  - Encapsulado no componente [`KafkaStreamClient`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/gold/streaming/kafka_client.py) com suporte a *Context Manager* (`__enter__` e `__exit__`), garantindo *flush* obrigatório e encerramento determinístico de conexões.

---

## 🗺️ 3. Processamento Geoespacial e Formatos Vetoriais

* **`shapely` (>= 2.0)**:
  - Motor de geometria computacional acelerado pela biblioteca C GEOS.
  - **Indexação STRtree**: Fornece árvores espaciais R-Tree baseadas no algoritmo *Sort-Tile-Recursive*, reduzindo a complexidade de consultas espaciais de vizinho mais próximo (*Nearest Neighbor*) e contenção (*Point-in-Polygon*) de $O(N)$ para **$O(\log N)$**.
* **`geopandas` e `pyogrio`**:
  - `pyogrio` injeta aceleração C++ (via GDAL) para leitura ultrarrápida dos arquivos vetoriais Shapefile e GeoJSON brutos do IBGE, FUNAI, DNIT e ANEEL.
  - Gerenciamento de GeoDataFrames e reprojeção cartográfica precisa entre WGS84 (`EPSG:4326`) e o sistema métrico oficial **SIRGAS 2000 Brasil Policônica (`EPSG:5880`)**.
* **`pyproj`**:
  - Transformações geodésicas e conversões de coordenadas métricas com precisão milimétrica.
* **`pandas` e `pyarrow`**:
  - Transformações vetorizadas em memória (`DataFrame -> DataFrame`) sem estado compartilhado (Functional Core).
  - Suporte a leitura e escrita colunar compactada (Parquet/Arrow).

---

## 🔬 4. Inteligência de Dados e Grafos Complexos

* **`scikit-learn` (ST-DBSCAN)**:
  - Clusterização não supervisionada baseada em densidade espaço-temporal (`EventizadorIncendios`).
  - Agrupa dezenas de coordenadas térmicas atômicas contíguas no espaço ($\le 8\text{ km}$) e tempo ($\le 2\text{ dias}$) em manchas orgânicas de desastre delimitadas por envoltória convexa (*Convex Hull*).
* **`networkx` (>= 3.0)**:
  - Modelagem do Sistema Interligado Nacional (SIN) em grafos matemáticos não direcionados $G(V, E)$ (`SINNetworkCentralityModel`).
  - Cálculo de Centralidade de Intermediação (*Betweenness Centrality*) e inferência de risco de queda em cascata e blecaute sistêmico (contingência N-2).
* **`scipy` (`scipy.spatial.cKDTree`)**:
  - Árvore de particionamento espacial de busca $k$-d para cruzamento ultrarrápido entre os vértices das Linhas de Transmissão e as coordenadas das Subestações elétricas dentro de raio de tolerância de 5 km.

---

## 🧪 5. Engenharia de Testes e Confiabilidade

* **`pytest` (>= 9.0) e `pytest-mock`**:
  - Execução automatizada e silenciosa da suíte de 121 testes unitários, contratuais e de integração co-localizados nas camadas (`src/core/tests`, `src/bronze/tests`, `src/silver/tests`, `src/gold/tests`, `src/orchestration/tests`, `infra/tests`, `scripts/tests`).
  - Tempo médio de execução de **~29 segundos**, viabilizando validação contínua em esteiras de CI/CD locais sem necessidade de contêineres Docker ativos.
