# Registros de Decisões de Arquitetura (ADRs) - CCO DataOps

Este diretório formaliza os **Architectural Decision Records (ADRs)** do projeto **CCO-DataOps**. Cada ADR captura uma decisão arquitetural significativa, o contexto em que foi tomada, as alternativas consideradas e as consequências para a engenharia de software e performance de dados.

---

## 📑 Índice de Decisões Arquiteturais

| ADR | Título | Status | Data | Impacto Principal |
|:---:|:---|:---:|:---:|:---|
| [**001**](001_layout_semantico_monorepo.md) | **Layout Semântico Desacoplado no Monorepo** | Aprovado | 2026-11-03 | Unificação sob `src/` com remoção de pastas legadas redundantes. |
| [**002**](002_padrao_fcis_e_solid.md) | **Padrão FCIS (Functional Core, Imperative/OO Shell) e SOLID** | Aprovado | 2026-11-04 | Eliminação de classes utilitárias artificiais; POO restrita a estado e I/O. |
| [**003**](003_modelo_snowflake_e_druid_lookups.md) | **Modelagem Analítica Snowflake Estrita e Lookups no Apache Druid** | Aprovado | 2026-10-28 | Veto a strings descritivas em streaming Kafka; resolução em memória RAM no Druid. |
| [**004**](004_execucao_dagster_in_memory.md) | **Execução In-Memory Orientada a Objetos de Assets no Apache Dagster** | Aprovado | 2026-11-03 | Eliminação de subprocessos procedurais via despacho direto de `ExecutablePipelineStep`. |
| [**005**](005_indexacao_espacial_strtree_e_sirgas2000.md) | **Indexação Espacial Vetorial (STRtree) e Reprojeção SIRGAS 2000** | Aprovado | 2026-10-25 | Redução de busca de $O(N)$ para $O(\log N)$ e cálculo exato de distâncias métricas (EPSG:5880). |
| [**006**](006_centralidade_de_redes_topologicas_sin.md) | **Modelagem Topológica e Risco de Cascata no SIN via NetworkX** | Aprovado | 2026-10-28 | Cálculo de Betweenness Centrality normalizado (0-100) para contingência N-2. |

---

## 🎯 Estrutura Padrão dos Registros
Cada documento adota a estrutura padronizada:
1. **Contexto**: O problema ou desafio técnico enfrentado.
2. **Decisão**: A solução arquitetural adotada.
3. **Consequências**: Os benefícios obtidos e as restrições introduzidas.
