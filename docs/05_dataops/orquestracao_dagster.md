# Governança de Pipelines (Dagster e DataOps)

Em ambientes acadêmicos e analíticos complexos, a ausência de um escalonador semântico de fluxos ocasiona perdas críticas na estabilidade topológica e rastreabilidade (*Lineage*). A transição do acionamento discricionário de scripts por rotinas cronológicas cegas para um orquestrador centrado em dados eleva a maturidade intrínseca da solução.

## 1. Software-Defined Assets (SDA)
O projeto instituiu a plataforma **Dagster** como orquestrador *Data-Aware*. Em oposição ao modelo tradicional orientado a tarefas imperativas (Task-Based, e.g., Apache Airflow), o conceito adotado pelo módulo `src/orchestration/repo.py` descreve imperativamente os ativos matemáticos esperados como saída (Assets). 

- Scripts e modelagens matemáticas (tais como extração do ONS e compilação do ST-DBSCAN) assumem *decorators* `@asset`.
- O código-fonte transpassa a sua execução bruta e atua explicitamente demarcando suas entradas e saídas esperadas em um grafo direcionado acíclico (DAG) visível graficamente sob a suíte Dagster UI.

## 2. Integridade e Resiliência
O Dagster confere ao projeto um tecido rígido de estabilidade operativa:
- **Resolução Automática de Dependências**: O *Betweenness Centrality* dos grafos do ONS exige, invariavelmente, que os limites vetorizados (`dim_subestacoes` e `dim_linhas_transmissao`) encontrem-se estabilizados e imaculados no *Data Lake* primário antes da iniciação.
- **Isolamento Computacional**: A execução assíncrona encapsula o risco lógico, protegendo o *kernel* da engine de panes originadas em processos adjacentes que venham a sofrer colapso sistêmico (*Out-Of-Memory* ou Erros de Conexão).
