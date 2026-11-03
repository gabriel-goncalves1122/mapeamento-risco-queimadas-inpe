# Portal de Governança e Documentação Geral - CCO DataOps

Este diretório centraliza a documentação executiva, visão arquitetural macro, fundamentação científica, especificações de infraestrutura e relatórios acadêmicos do projeto **SIRDA / CCO-DataOps**.

O ecossistema adota uma **Arquitetura de Documentação Descentralizada**: cada camada física da arquitetura Medalhão (`src/bronze/`, `src/silver/`, `src/gold/` e `src/orchestration/`) abriga seus guias operacionais, diagramas de fluxo, especificações de APIs e dicionários de dados especializados.

---

## 🏛️ Navegação Descentralizada por Camadas da Arquitetura Medalhão

Utilize os links diretos abaixo para acessar a documentação técnica específica de cada camada:

| Camada | Propósito Principal | Documentos Disponíveis |
|---|---|---|
| **🥉 Camada Bronze**<br>`src/bronze/` | Ingestão de dados brutos (*raw/unmutated*), paginação resiliente de APIs governamentais e preservação de metadados originais. | • [📘 **README.md (Guia da Camada)**](../src/bronze/README.md)<br>• [🌐 **FONTES_E_APIS.md (APIs e Provedores)**](../src/bronze/FONTES_E_APIS.md)<br>• [📋 **DICIONARIO_DADOS.md (Esquemas Brutos)**](../src/bronze/DICIONARIO_DADOS.md) |
| **🥈 Camada Silver**<br>`src/silver/` | Conformação das 7 Dimensões Espaciais (Snowflake), reprojeção SIRGAS 2000 (`EPSG:5880`), STRtree e geração de `path_json`. | • [📘 **README.md (Guia da Camada)**](../src/silver/README.md)<br>• [📊 **DICIONARIO_DADOS.md (Dimensões Conformadas)**](../src/silver/DICIONARIO_DADOS.md) |
| **🥇 Camada Gold**<br>`src/gold/` | Data Science avançado (ST-DBSCAN e Grafos NetworkX), Tabelas Fato e produtores de streaming Kafka para o Apache Druid. | • [📘 **README.md (Guia da Camada)**](../src/gold/README.md)<br>• [🏛️ **ARQUITETURA.md (Engenharia e Modelos)**](../src/gold/ARQUITETURA.md)<br>• [📋 **DICIONARIO_DADOS.md (Tabelas Fato)**](../src/gold/DICIONARIO_DADOS.md) |
| **⚙️ Orquestração**<br>`src/orchestration/` | Grafo declarativo de *Software-Defined Assets* (SDA) do Apache Dagster e despacho de classes POO em memória (`ExecutablePipelineStep`). | • [📘 **README.md (Guia de Orquestração)**](../src/orchestration/README.md) |

---

## 📚 Sumário da Documentação Geral (`docs/`)

Para aspectos transversais, benchmarks de performance e produção científica, consulte os módulos abaixo:

### 1. 🏛️ [Guias de Arquitetura Sistêmica Macro](./architecture/index.md)
* **[Streaming e OLAP (Kafka + Druid)](./architecture/01_streaming_e_olap.md):** Desacoplamento via mensageria, indexação colunar em bitmaps (*Roaring*) e Lookups em memória.
* **[Orquestração e Medallion (Dagster)](./architecture/02_orquestracao.md):** Governança declarativa de linhagem (*lineage*), execução em memória e particionamento temporal.
* **[Data Science e Modelagem Preditiva](./architecture/03_data_science.md):** Agrupamento espaço-temporal ST-DBSCAN (*Convex Hull*) e Teoria dos Grafos (*Betweenness Centrality* no SIN).
* **[Referencial Teórico (SIRDA)](./architecture/04_referencial_teorico.md):** Consciência Situacional de Endsley, Paradigma DataOps de Ereth e modelos estocásticos.
* **[Data Flow End-to-End](./architecture/05_data_flow_end_to_end.md):** Trânsito ponta a ponta desde as APIs até os painéis de consciência situacional no Superset.
* **[Arquitetura Orientada a Objetos e SOLID](./architecture/06_arquitetura_poo_solid.md):** Princípios SOLID, padrões Template Method, Context Manager, Injeção de Dependências e diagramas exatos.

### 2. 📖 [Índice Geral de Dicionários de Dados](./data_dictionary/index.md)
* Portal unificado indexando os dicionários de dados das camadas [Bronze](../src/bronze/DICIONARIO_DADOS.md), [Silver](../src/silver/DICIONARIO_DADOS.md) e [Gold](../src/gold/DICIONARIO_DADOS.md).

### 3. 🔬 [Benchmarking e Avaliação de Desempenho](./performance/druid_capacity/)
* Matrizes de estresse concorrente (QPS, P95/P99), saturação de CPU (*CPU-Bound*), consumo de memória dos nós Docker e eficiência de cache (*Broker Cache*).

### 4. ⚙️ [Especificações Técnicas de Infraestrutura](./technical_specs/)
* **[Análise de Contêineres Docker](./technical_specs/docker_analysis.md):** Limites de *cgroups* e parâmetros JVM (`JAVA_OPTS`).
* **[Especificações de Hardware](./technical_specs/hardware_specs.md):** Recursos computacionais utilizados nos ensaios.
* **[Análise de Bibliotecas e Dependências](./technical_specs/libraries_analysis.md):** Pilha Python 3.12 gerenciada via `uv`.

### 5. 🎓 [Produção Científica e Acadêmica](./academic/)
* **[Relatório Final de Iniciação Científica](./academic/relatorio_final/main.tex):** Monografia técnica consolidada da pesquisa com referências bibliográficas completas.
* **[Artigo no Padrão SBC](./academic/SBC/artigo_final.tex):** Artigo completo sobre a arquitetura DataOps e avaliação empírica.
* **[Pôster e Apresentações em Simpósio](./academic/poster/):** Materiais gráficos de apresentação institucional na UNIFEI.

---

## 🗄️ Acervo Histórico e Legado
Materiais legados, relatórios antigos e backups offline de visualização ficam centralizados em `legacy/`. A pasta `docs/` e os diretórios das camadas mantêm exclusivamente documentação viva, ativa e alinhada ao código-fonte em produção.
