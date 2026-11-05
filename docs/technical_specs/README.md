# Especificações Técnicas de Hardware, Contêineres e Dependências (`docs/technical_specs/`)

> **Trilha Geral de Documentação**: [Portal Geral (`docs/README.md`)](../README.md) | [Capítulo 06: Orquestração e OLAP](../architecture/06_orquestracao_olap_e_operacao.md) | [Infraestrutura (`infra/README.md`)](../../infra/README.md)

Este diretório especifica os requisitos de hardware, o isolamento de recursos de contêineres Docker (`cgroups` e parâmetros JVM do Apache Druid), a árvore de dependências Python gerenciada pelo `uv` e as referências normativas do sistema **CCO DataOps**.

---

## 1. Índice de Especificações

| Documento | Escopo Técnico |
| :--- | :--- |
| [**`hardware_specs.md`**](hardware_specs.md) | Especificações de processador, memória RAM, armazenamento NVMe e ambiente operacional utilizados na validação experimental e nos ensaios de estresse. |
| [**`docker_analysis.md`**](docker_analysis.md) | Análise dos limites de memória (`MEM_LIMIT`), quotas de vCPU (`CPUS`), dimensionamento de Heap e Direct Memory (`JAVA_OPTS`) dos 5 serviços do Apache Druid 34.0. |
| [**`libraries_analysis.md`**](libraries_analysis.md) | Inventário das bibliotecas Python 3.12 (`geopandas`, `shapely`, `pyproj`, `scikit-learn`, `networkx`, `scipy`, `pydantic`, `kafka-python`, `dagster`) e gerenciamento determinístico via `uv`. |
| [**`referencias.md`**](referencias.md) | Referências bibliográficas e documentações técnicas oficiais dos provedores governamentais (INPE, ANEEL, ONS, FUNAI, IBGE, DNIT, DATASUS). |

---

## 2. Documentos Operacionais Correlatos
- [**Especificação de Infraestrutura OLAP e Perfis do Druid (`infra/README.md`)**](../../infra/README.md)
- [**Especificação de Scripts Operacionais e Benchmarks (`scripts/README.md`)**](../../scripts/README.md)
