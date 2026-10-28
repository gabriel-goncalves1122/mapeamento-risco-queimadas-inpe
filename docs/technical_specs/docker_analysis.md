# Análise do Orquestrador e Contêineres (Docker)

O ecossistema analítico do SIRDA é provido através de uma stack robusta conteinerizada (Zookeeper, Kafka, Postgres, Druid, Superset e Dagster). Dada a limitação física do ambiente de validação (8 vCPUs e 7.5 GiB de RAM), as políticas de contenção (`deploy.resources.limits`) foram severamente arquitetadas no `docker-compose.yaml`.

## Telemetria e Consumo em *Standby*
Em estado de repouso (ociosidade), todo o cluster analítico consumiu **apenas ~1.85 GB** de memória RAM (apenas ~24% da capacidade total da máquina hospedeira), validando a exequibilidade operacional e a saúde da arquitetura.

| Serviço | Papel na Arquitetura | Limite Alocado (RAM) | Consumo Standby (RAM) | % de Uso |
| :--- | :--- | :--- | :--- | :--- |
| **Kafka** | Mensageria (Streaming) | 512 MiB | 101.0 MiB | 19.72% |
| **Zookeeper** | Gerenciador de Configuração | 256 MiB | 26.39 MiB | 10.31% |
| **Postgres** | Repositório de Metadados | 256 MiB | 13.95 MiB | 5.45% |
| **Coordinator (Druid)** | Coordenação OLAP | 384 MiB | 195.6 MiB | 50.95% |
| **Broker (Druid)** | Roteador de Consultas | 768 MiB | 186.0 MiB | 24.22% |
| **Historical (Druid)** | Armazenamento OLAP | 768 MiB | 209.3 MiB | 27.25% |
| **MiddleManager (Druid)** | Tarefas de Ingestão | 1.0 GiB | 626.8 MiB | 61.21% |
| **Router (Druid)** | Web Console / Roteamento | 384 MiB | 110.3 MiB | 28.72% |
| **Superset** | Business Intelligence (BI) | 768 MiB | 377.2 MiB | 49.12% |

> [!TIP]
> **Destaques de Consumo:**
> 1. O **MiddleManager** desponta como o consumidor mais alto (626 MiB) devido à pré-alocação dos *workers* JVM (`druid_worker_capacity: 2`), mantendo-se sempre vigilante para ingestão em tempo real.
> 2. O **Kafka** e **Postgres**, críticos em arquiteturas de dados clássicas, operam de forma extremamente eficiente, com consumos pífios de 101 MiB e 14 MiB, respectivamente.

## Isolamento e Persistência
- **Rede (`druid-net`):** Todo o tráfego intra-cluster ocorre por uma rede bridge isolada, prevenindo concorrência na rede do hospedeiro.
- **Volumes Persistentes:** Volumes fixos (`metadata_data`, `zookeeper_data`, `dagster_data`) isolam o armazenamento local, impedindo a degradação e garantindo retenção histórica nas reinicializações (especialmente vital para a arquitetura Kappa/Medallion no Druid).
