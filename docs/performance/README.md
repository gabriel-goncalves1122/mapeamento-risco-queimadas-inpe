# Avaliação de Desempenho e Planejamento de Capacidade (`docs/performance/`)

> **Trilha Geral de Documentação**: [Portal Geral (`docs/README.md`)](../README.md) | [Especificações de Hardware (`docs/technical_specs/`)](../technical_specs/README.md) | [Scripts de Benchmark (`scripts/README.md`)](../../scripts/README.md)

Este diretório armazena os relatórios experimentais, matrizes de concorrência e análises estatísticas de capacidade do cluster **Apache Druid 34.0** no projeto **CCO DataOps**.

---

## 1. Escopo Metodológico dos Ensaios

Os experimentos avaliam o comportamento do motor OLAP sob três perfis de alocação de hardware (`scenario_01_baseline`, `scenario_02_balanced` e `scenario_03_query_heavy`) submetidos a baterias de consultas SQL concorrentes ($1, 2, 4, 8\text{ e }16$ clientes simultâneos):

1. **Vazão Analítica (*Queries Per Second* — QPS)** em função do nível de concorrência.
2. **Distribuição de Latência (P50, P95 e P99)** em agregações temporais, filtros geoespaciais (`sample_bucket`) e resoluções de *Lookups* em memória.
3. **Impacto do Cache do Broker** (`useCache: true` vs `useCache: false`) sobre a carga de I/O e CPU dos nós `Historical`.
4. **Saturação de CPU e Consumo de Memória RAM** amostrados continuamente via `docker stats`.

---

## 2. Relatórios Experimentais Disponíveis

| Ensaio Experimental | Caminho | Descrição Técnica |
| :--- | :--- | :--- |
| **Campanha Consolidada (2026-08-18)** | [**`druid_capacity/20260818_212232/README.md`**](druid_capacity/20260818_212232/README.md) | Avaliação comparativa completa entre os perfis *Baseline* (`1 vCPU / 2 GB`), *Balanced* (`2 vCPUs / 4 GB`) e *Query-Heavy* (`4 vCPUs / 8 GB`). |
| **Campanha Preliminar (2026-06-30)** | [**`druid_capacity/20260630_000802/README.md`**](druid_capacity/20260630_000802/README.md) | Ensaio inicial de caracterização de saturação dos serviços Broker e Historical. |
| **Diretrizes de Análise (`agents.md`)** | [**`agents.md`**](agents.md) | Critérios metodológicos para interpretação estatística dos resultados e compilação de tabelas/figuras. |

---

## 3. Reprodução Automatizada dos Relatórios

```bash
bash scripts/benchmarks/compile_capacity_reports.sh docs/performance/druid_capacity/20260818_212232
```
Para detalhes sobre o motor de geração de carga (`benchmark_runner`) e o gerador de relatórios (`report_generator`), consulte [`scripts/README.md`](../../scripts/README.md).
