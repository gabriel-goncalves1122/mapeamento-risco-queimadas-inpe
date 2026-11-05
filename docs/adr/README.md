# Registros de Decisões de Arquitetura — ADRs (`docs/adr/`)

> **Trilha Geral de Documentação**: [Portal Geral (`docs/README.md`)](../README.md) | [Capítulo 02: Visão Geral e Engenharia Core](../architecture/02_visao_geral_e_engenharia_core.md) | [Dicionários de Dados](../data_dictionary/index.md)

Este diretório contém os **Architectural Decision Records (ADRs)** do projeto **CCO DataOps**. Os registros estão ordenados da fundação estrutural do repositório e padrões de código (`001` e `002`) até a modelagem dimensional, orquestração, indexação espacial e ciência de redes (`003` a `006`).

---

## 1. Índice Ordenado de ADRs

| ADR | Documento | Status | Escopo e Consequência Técnica Principal |
| :-: | :--- | :-: | :--- |
| **001** | [**`001_layout_semantico_monorepo.md`**](001_layout_semantico_monorepo.md) | Aprovado | Unificação do código-fonte sob `src/` dividido pelas camadas semânticas `core/`, `bronze/`, `silver/`, `gold/` e `orchestration/`. |
| **002** | [**`002_padrao_fcis_e_solid.md`**](002_padrao_fcis_e_solid.md) | Aprovado | Adoção do padrão *Functional Core, Imperative Shell* (FCIS): transformações de dados como funções puras vetorizadas e POO restrita a gerenciamento de estado, I/O e protocolos SOLID. |
| **003** | [**`003_modelo_snowflake_e_druid_lookups.md`**](003_modelo_snowflake_e_druid_lookups.md) | Aprovado | Proibição de strings descritivas redundantes nos payloads Kafka das tabelas fato; resolução em tempo de consulta via 23 Lookups `cachedNamespace` em memória RAM no Apache Druid. |
| **004** | [**`004_execucao_dagster_in_memory.md`**](004_execucao_dagster_in_memory.md) | Aprovado | Execução polimórfica em memória de *Software-Defined Assets* no Apache Dagster sobre o contrato `ExecutablePipelineStep`, eliminando chamadas de subprocessos. |
| **005** | [**`005_indexacao_espacial_strtree_e_sirgas2000.md`**](005_indexacao_espacial_strtree_e_sirgas2000.md) | Aprovado | Indexação espacial em memória via `STRtree` e reprojeção métrica para SIRGAS 2000 Policônica (`EPSG:5880`), reduzindo a complexidade de busca espacial de $O(N)$ para $O(\log N)$. |
| **006** | [**`006_centralidade_de_redes_topologicas_sin.md`**](006_centralidade_de_redes_topologicas_sin.md) | Aprovado | Modelagem da malha do SIN como grafo não direcionado ponderado (`cKDTree` + `NetworkX`) e cálculo de *Betweenness Centrality* normalizado ($0$–$100$) para estratificação de risco de cascata. |

---

## 2. Estrutura Padronizada dos ADRs

Cada registro de decisão documenta:
1. **Contexto e Problema**: restrições operacionais, de performance ou de manutenibilidade identificadas.
2. **Decisão**: especificação técnica da solução adotada.
3. **Consequências**: ganhos mensuráveis e trade-offs assumidos pela arquitetura.
