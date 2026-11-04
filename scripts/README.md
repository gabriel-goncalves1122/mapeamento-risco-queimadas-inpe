# Ferramental Operacional e Manutenção (`scripts/`) - CCO DataOps

O diretório `scripts/` centraliza todos os utilitários procedurais de linha de comando (CLI), rotinas de automação, suítes de benchmarking de desempenho e procedimentos de manutenção do projeto **CCO-DataOps**.

Em conformidade com a regra de ouro de governança **FCIS (Pragmatismo Operacional)**:
* Ferramentas de linha de comando, manutenção e setups pontuais são implementados como **scripts procedurais diretos** (`if __name__ == "__main__":` ou Bash com `set -euo pipefail`), sem hierarquias de classes abstratas desnecessárias.
* Toda a execução do ecossistema Python moderno é operada via `uv` (`uv run python ...`, `uv run pytest`).

---

## 🏗️ 1. Estrutura de Diretórios dos Scripts

```text
scripts/
├── README.md              # Este manual geral de scripts operacionais
├── run_all.sh             # Orquestrador mestre para executar o pipeline ponta a ponta
├── bootstrap_stack.sh     # Automação de setup inicial, permissões e importação no Superset
├── run_tests.sh           # Atalho de execução de testes automatizados com uv
├── run/                   # Scripts operacionais numerados de execução de etapas (01 a 05)
│   ├── 01_etl_batch.sh           # Etapa 1: Ingestão e geração das 7 Dimensões Silver
│   ├── 02_modelos_ciencia.sh     # Etapa 2: Execução de modelos de IA e Grafos SIN (Gold)
│   ├── 03_docker_e_kafka.sh      # Etapa 3: Inicialização da infraestrutura Docker e tópicos Kafka
│   ├── 04_druid_dimensoes.sh     # Etapa 4: Publicação de Lookups URI e ingestão Batch no Druid
│   ├── 04_druid_lookups.py       # Ponto de entrada CLI para o serviço DruidLookupRegistrar
│   └── 05_streaming_eventos.sh   # Etapa 5: Disparo dos produtores de streaming contínuo
├── benchmarks/            # Suíte de avaliação de desempenho e planejamento de capacidade
│   ├── capacity_metadata.py      # Metadados e catálogo de cenários dos experimentos
│   ├── compare_capacity_results.py # Comparador estatístico de benchmarks
│   ├── compile_capacity_reports.sh # Compilação dos relatórios técnicos em LaTeX/PDF
│   ├── run_capacity_matrix.sh    # Execução da matriz de concorrência (1 a 16 clientes)
│   ├── run_all_experiments.sh    # Runner de todos os cenários de carga do Druid
│   ├── benchmark_runner/         # Motor de estresse com amostragem de recursos Docker
│   └── report_generator/         # Gerador de figuras e tabelas estatísticas em LaTeX/Markdown
├── maintenance/           # Utilitários de manutenção e diagnósticos do cluster
│   ├── executar_validacoes_sql_druid.py  # Diagnóstico e testes das queries SQL analíticas
│   ├── run_superset_sector_queries.py    # Teste de carga e execução de queries por setor
│   ├── update_docs_and_configs.py        # Sincronização automatizada de docs e configs de infra
│   ├── reindex_com_sample_bucket.sh      # Reindexação de segmentos com granularidade uniforme
│   └── druid_reload/                     # Procedimentos de reinício e recarga de tabelas fato
│       ├── reload_all.sh                 # Reinício completo com recarga de lookups e fatos
│       ├── reload_event_fact.sh          # Recarga cirúrgica da tabela fato_eventos_incendio
│       └── reinicio_completo.sh          # Wipe completo e reinicialização limpa
├── setup/                 # Procedimentos de inicialização de dados estáticos
│   └── register_datasets_local.py        # Registro local de datasets
└── tests/                 # Testes unitários das ferramentas de benchmark e manutenção
    └── unit/
        ├── test_performance_benchmark.py
        └── test_event_fact_reload_script.py
```

---

## 🚀 2. Guia de Execução Rápida

### 2.1 Execução Completa Ponta a Ponta (`run_all.sh`)
Para executar todo o pipeline da aplicação de forma sequencial com verificação de integridade:
```bash
./scripts/run_all.sh
```

O script aceita opções para controle de execução parcial:
* `--skip-etl`: Pula a regeneração das dimensões da Camada Silver.
* `--skip-docker`: Executa assumindo que a infraestrutura Docker já está operando.
* `--profile <nome>`: Define o perfil de recursos do Druid (`scenario_01_baseline`, `scenario_02_balanced` ou `scenario_03_query_heavy`).

### 2.2 Inicialização da Stack e Superset (`bootstrap_stack.sh`)
Executa o provisionamento de diretórios compartilhados, corrige permissões de volume Linux/Docker, sobe o contêiner do Superset, executa as migrações de banco (`superset db upgrade`), cria o usuário administrador padrão (`admin`/`admin`) e importa datasources e dashboards pré-configurados:
```bash
./scripts/bootstrap_stack.sh
```

---

## 📋 3. As Etapas Sequenciais Operacionais (`scripts/run/`)

A execução por etapas isoladas permite depuração cirúrgica durante o ciclo de desenvolvimento:

| Etapa | Script | Ação Executada | Saída Gerada |
|:---:|:---|:---|:---|
| **01** | [`01_etl_batch.sh`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/scripts/run/01_etl_batch.sh) | Executa `src/silver/etl/run_etl.py` gerando as 7 dimensões analíticas em paralelo. | `src/silver/data/dimensions/*.csv` |
| **02** | [`02_modelos_ciencia.sh`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/scripts/run/02_modelos_ciencia.sh) | Executa `src/gold/science/networkx/network_builder.py`, calculando Betweenness Centrality e Risco de Cascata no SIN. | Atualiza `dim_ons_subestacoes.csv` com métricas de grafos. |
| **03** | [`03_docker_e_kafka.sh`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/scripts/run/03_docker_e_kafka.sh) | Sobe contêineres Docker essenciais e assegura a criação dos tópicos Kafka `focos-incendio` e `eventos-incendio`. | Kafka ativo na porta 9092. |
| **04** | [`04_druid_dimensoes.sh`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/scripts/run/04_druid_dimensoes.sh) | Invoca [`04_druid_lookups.py`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/scripts/run/04_druid_lookups.py) para registrar Lookups URI e submete as specs batch ao Overlord. | Lookups em memória e tabelas dimensionais no Druid. |
| **05** | [`05_streaming_eventos.sh`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/scripts/run/05_streaming_eventos.sh) | Submete as specs de ingestão contínua do Kafka ao Druid e inicia a publicação de dados streaming na Camada Gold. | Streaming ativo alimentando dashboards. |

---

## 🔬 4. Suíte de Benchmarking e Capacidade (`scripts/benchmarks/`)

Desenvolvida para a pesquisa acadêmica de Iniciação Científica (UNIFEI), permite avaliar a escalabilidade e o comportamento do Apache Druid sob estresse concorrente:

1. **Matriz de Concorrência (`run_capacity_matrix.sh`)**:
   - Submete requisições analíticas concorrentes simulando de 1 a 16 clientes simultâneos via Apache Bench / HTTP.
   - Amostra periodicamente a utilização de vCPU e memória RAM de cada contêiner Docker via `docker_sampler.py`.
2. **Geração de Relatórios Acadêmicos (`compile_capacity_reports.sh`)**:
   - Processa os logs estatísticos (P50, P95, P99, vazão em QPS e desvio padrão).
   - Gera gráficos de violino e curvas de vazão (`report_generator/figures.py`).
   - Compila tabelas formatadas em sintaxe LaTeX (`report_generator/tables.py`) prontas para inclusão na monografia e no artigo SBC.

---

## 🛠️ 5. Rotinas de Manutenção (`scripts/maintenance/`)

* **`executar_validacoes_sql_druid.py`**: Conecta via HTTP SQL no Broker e valida que todas as 15 consultas do catálogo retornam dados com tempo de resposta $< 100ms$.
* **`reindex_com_sample_bucket.sh`**: Utilitário de compactação e particionamento dos dados do Druid, gerando granularidade temporal otimizada.
* **`druid_reload/reload_all.sh`**: Força o reinício dos serviços de streaming e sincronização dos mapas de lookup no Coordinator em caso de atualização de CSVs dimensionais.
