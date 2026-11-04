# Portal de Governança e Documentação Geral - CCO DataOps

Este diretório centraliza a documentação executiva, visão arquitetural macro, fundamentação científica, especificações de infraestrutura e relatórios acadêmicos do projeto **SIRDA / CCO-DataOps**.

O ecossistema adota uma **Arquitetura de Documentação Descentralizada**: cada camada física da arquitetura Medalhão (`src/core/`, `src/bronze/`, `src/silver/`, `src/gold/` e `src/orchestration/`), assim como `infra/` e `scripts/`, abriga seus guias operacionais, diagramas de fluxo, especificações de APIs e dicionários de dados especializados.

---

## 🏛️ Navegação Descentralizada por Camadas da Aplicação

Utilize os links diretos abaixo para acessar a documentação técnica específica de cada camada:

| Módulo / Camada | Propósito Principal | Documentos Disponíveis |
|---|---|---|
| **🧩 Núcleo Compartilhado**<br>`src/core/` | Contratos abstratos (POO/SOLID), interfaces desacopladas, contratos Pydantic imutáveis (`frozen=True`) e governança de configurações. | • [📘 **README.md (Guia do Núcleo)**](../src/core/README.md) |
| **🥉 Camada Bronze**<br>`src/bronze/` | Ingestão de dados brutos (*raw/unmutated*), paginação resiliente de APIs governamentais e preservação de metadados originais. | • [📘 **README.md (Guia da Camada)**](../src/bronze/README.md)<br>• [🌐 **FONTES_E_APIS.md (APIs e Provedores)**](../src/bronze/FONTES_E_APIS.md)<br>• [📋 **DICIONARIO_DADOS.md (Esquemas Brutos)**](../src/bronze/DICIONARIO_DADOS.md) |
| **🥈 Camada Silver**<br>`src/silver/` | Conformação das 7 Dimensões Espaciais (Snowflake), reprojeção SIRGAS 2000 (`EPSG:5880`), STRtree, validadores de QA e geração de `path_json`. | • [📘 **README.md (Guia da Camada)**](../src/silver/README.md)<br>• [🗺️ **README.md (Motor Espacial)**](../src/silver/spatial/README.md)<br>• [📊 **DICIONARIO_DADOS.md (Dimensões Conformadas)**](../src/silver/DICIONARIO_DADOS.md)<br>• [🛡️ **README.md (Validadores de QA)**](../src/silver/validators/README.md) |
| **🥇 Camada Gold**<br>`src/gold/` | Data Science avançado (ST-DBSCAN e Grafos NetworkX), Tabelas Fato e produtores de streaming Kafka para o Apache Druid. | • [📘 **README.md (Guia da Camada)**](../src/gold/README.md)<br>• [⚡ **README.md (Mensageria e Streaming)**](../src/gold/streaming/README.md)<br>• [🏛️ **ARQUITETURA.md (Engenharia e Modelos)**](../src/gold/ARQUITETURA.md)<br>• [📋 **DICIONARIO_DADOS.md (Tabelas Fato)**](../src/gold/DICIONARIO_DADOS.md) |
| **⚙️ Orquestração**<br>`src/orchestration/` | Grafo declarativo de *Software-Defined Assets* (SDA) do Apache Dagster e despacho de classes POO em memória (`ExecutablePipelineStep`). | • [📘 **README.md (Guia de Orquestração)**](../src/orchestration/README.md) |
| **🐳 Infraestrutura**<br>`infra/` | Cluster distribuído Apache Druid 34.0, Apache Superset, Kafka/ZooKeeper, specs de ingestão e profiles de capacidade. | • [📘 **README.md (Guia de Infraestrutura)**](../infra/README.md) |
| **🛠️ Ferramental Operacional**<br>`scripts/` | Scripts procedurais diretos de execução por etapas (`01` a `05`), runners de benchmark e rotinas de manutenção. | • [📘 **README.md (Manual Operacional)**](../scripts/README.md) |

---

## 📚 Sumário da Documentação Geral (`docs/`)

Para aspectos transversais, benchmarks de performance, decisões arquiteturais e produção científica, consulte os módulos abaixo:

### 1. 🏛️ [Guias de Arquitetura Sistêmica Macro](./architecture/index.md)
* **[Streaming e OLAP (Kafka + Druid)](./architecture/01_streaming_e_olap.md):** Desacoplamento via mensageria, indexação colunar em bitmaps (*Roaring*) e Lookups em memória.
* **[Orquestração e Medallion (Dagster)](./architecture/02_orquestracao.md):** Governança declarativa de linhagem (*lineage*), execução em memória e particionamento temporal.
* **[Data Science e Modelagem Preditiva](./architecture/03_data_science.md):** Agrupamento espaço-temporal ST-DBSCAN (*Convex Hull*) e Teoria dos Grafos (*Betweenness Centrality* no SIN).
* **[Referencial Teórico (SIRDA)](./architecture/04_referencial_teorico.md):** Consciência Situacional de Endsley, Paradigma DataOps de Ereth e modelos estocásticos.
* **[Data Flow End-to-End](./architecture/05_data_flow_end_to_end.md):** Trânsito ponta a ponta desde as APIs até os painéis de consciência situacional no Superset.
* **[Arquitetura Orientada a Objetos e SOLID](./architecture/06_arquitetura_poo_solid.md):** Princípios SOLID, padrões Template Method, Context Manager, Injeção de Dependências e diagramas exatos.

### 2. 📑 [Registros de Decisões de Arquitetura (ADRs)](./adr/README.md)
* **[ADR 001 - Layout Semântico no Monorepo](./adr/001_layout_semantico_monorepo.md):** Unificação semântica em `src/`, `infra/`, `scripts/` e `docs/`.
* **[ADR 002 - Padrão FCIS e Princípios SOLID](./adr/002_padrao_fcis_e_solid.md):** Functional Core (funções puras) vs Imperative/OO Shell (estado e I/O).
* **[ADR 003 - Modelagem Snowflake e Lookups no Druid](./adr/003_modelo_snowflake_e_druid_lookups.md):** Veto a strings em streaming Kafka e resolução via URI Lookups.
* **[ADR 004 - Execução In-Memory no Dagster](./adr/004_execucao_dagster_in_memory.md):** Despacho em memória de `ExecutablePipelineStep` com telemetria nativa.
* **[ADR 005 - Indexação Espacial STRtree e SIRGAS 2000](./adr/005_indexacao_espacial_strtree_e_sirgas2000.md):** Busca $O(\log N)$ com projeção métrica oficial `EPSG:5880`.
* **[ADR 006 - Modelagem Topológica e Risco de Cascata no SIN](./adr/006_centralidade_de_redes_topologicas_sin.md):** Betweenness Centrality normalizado (0-100) via NetworkX.

### 3. 🌿 [Contexto Territorial e Socioambiental](./domain/ti_parque_araguaia_canoana.md)
* **[Terra Indígena Parque do Araguaia e Aldeia Canoanã](./domain/ti_parque_araguaia_canoana.md):** Ilha do Bananal/TO, histórico territorial (1959-1998), povos Iny (Javaé, Karajá), acolhimento dos Avá-Canoeiro em 1976 e relevância para mitigação de queimadas no CCO-DataOps.

### 4. 📖 [Índice Geral de Dicionários de Dados](./data_dictionary/index.md)
* Portal unificado indexando os dicionários de dados das camadas [Bronze](../src/bronze/DICIONARIO_DADOS.md), [Silver](../src/silver/DICIONARIO_DADOS.md) e [Gold](../src/gold/DICIONARIO_DADOS.md).

### 5. 🔬 [Benchmarking e Avaliação de Desempenho](./performance/druid_capacity/)
* Matrizes de estresse concorrente (QPS, P95/P99), saturação de CPU (*CPU-Bound*), consumo de memória dos nós Docker e eficiência de cache (*Broker Cache*).

### 6. ⚙️ [Especificações Técnicas de Infraestrutura](./technical_specs/)
* **[Análise de Contêineres Docker](./technical_specs/docker_analysis.md):** Limites de *cgroups* e parâmetros JVM (`JAVA_OPTS`).
* **[Especificações de Hardware](./technical_specs/hardware_specs.md):** Recursos computacionais utilizados nos ensaios.
* **[Análise de Bibliotecas e Dependências](./technical_specs/libraries_analysis.md):** Pilha Python 3.12 gerenciada via `uv`.

### 7. 🎓 [Produção Científica e Acadêmica](./academic/)
* **[Relatório Final de Iniciação Científica](./academic/relatorio_final/main.tex):** Monografia técnica consolidada da pesquisa com referências bibliográficas completas.
* **[Artigo no Padrão SBC](./academic/SBC/artigo_final.tex):** Artigo completo sobre a arquitetura DataOps e avaliação empírica.
* **[Pôster e Apresentações em Simpósio](./academic/poster/):** Materiais gráficos de apresentação institucional na UNIFEI.

---

## 🗄️ Acervo Histórico e Legado
Materiais legados, relatórios antigos e backups offline de visualização ficam centralizados em `legacy/`. A pasta `docs/` e os diretórios das camadas mantêm exclusivamente documentação viva, ativa e alinhada ao código-fonte em produção.
