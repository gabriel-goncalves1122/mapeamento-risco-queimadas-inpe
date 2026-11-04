# Análise do Orquestrador e Contêineres (Docker) - CCO DataOps

O ecossistema analítico do **CCO-DataOps** é provido através de uma stack de microsserviços distribuídos conteinerizados via **Docker Compose**: Apache Zookeeper, Apache Kafka, PostgreSQL, Apache Druid 34.0 (Coordinator, Broker, Historical, MiddleManager, Router) e Apache Superset.

Dada a meta de viabilizar a arquitetura em hardware de perfil intermediário (8 vCPUs e 8 GB de RAM) sem ocorrência de *Out Of Memory (OOM Killer)*, as políticas de contenção de recursos (`deploy.resources.limits`) e parâmetros de máquina virtual Java (`JAVA_OPTS`) foram milimetricamente calibradas.

---

## 📊 1. Alocação de Recursos e Limites de *cgroups*

A tabela abaixo detalha os limites estritos configurados no [`docker-compose.yaml`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/docker-compose.yaml) e a telemetria média em repouso (*standby*):

| Serviço | Papel na Arquitetura | Limite vCPU | Limite RAM | Consumo Standby | % Uso RAM |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Kafka** | Mensageria (Buffer de Streaming) | 0.50 | 512 MiB | 101.0 MiB | 19.72% |
| **Zookeeper** | Coordenação de Cluster | 0.25 | 256 MiB | 26.39 MiB | 10.31% |
| **Postgres** | Metastore Transacional (Druid/Superset) | 0.50 | 256 MiB | 13.95 MiB | 5.45% |
| **Coordinator (Druid)** | Gestão de Segmentos e Lookups | 0.50 | 384 MiB | 195.6 MiB | 50.95% |
| **Broker (Druid)** | Roteador SQL e Cache | 1.00 | 768 MiB | 186.0 MiB | 24.22% |
| **Historical (Druid)** | Servimento de Segmentos Colunares | 1.00 | 768 MiB | 209.3 MiB | 27.25% |
| **MiddleManager (Druid)** | Indexação Streaming (Kafka KIS) | 1.50 | 1024 MiB | 626.8 MiB | 61.21% |
| **Router (Druid)** | Web Console e Roteamento Unificado | 0.25 | 384 MiB | 110.3 MiB | 28.72% |
| **Superset** | Visualização Tática e BI | 1.00 | 768 MiB | 377.2 MiB | 49.12% |
| **Total Stack** | **Ecossistema Completo** | **6.50 vCPUs** | **5.0 GiB** | **~1.85 GiB** | **~37%** |

> [!TIP]
> **Destaques de Consumo e Dimensionamento:**
> 1. O **MiddleManager** desponta como o maior consumidor em repouso (~626 MiB) devido à alocação preventiva de *workers* JVM (`druid_worker_capacity: 2`), garantindo que os *Peons* de ingestão Kafka estejam permanentemente prontos para absorver picos de transmissão sem *cold start*.
> 2. O **Kafka** e o **Postgres** operam de forma extremamente enxuta (101 MiB e 14 MiB), demonstrando que o buffer de mensageria não impõe sobrecarga ao hospedeiro quando os contratos de dados evitam payloads inflados.

---

## 🛠️ 2. Mapeamento de Volumes e Layout Semântico

Em decorrência da reestruturação semântica sob `src/` (ADR 001), todos os volumes dimensionais montados nos contêineres refletem a nova árvore física:

* **Dimensões Silver**:
  `- ./src/silver/data:/opt/src/silver/data:ro`
  *(com montagem legada de compatibilidade `./src/silver/data:/opt/pipelines/silver/data:ro`)*.
  Permite que o Coordinator do Druid acesse os CSVs das 7 dimensões via protocolo local `file:///opt/src/silver/data/dimensions/*.csv` para construção dos mapas de *Lookup* em memória RAM sem tráfego de rede.
* **Tabelas Fato Gold**:
  `- ./src/gold/data:/opt/src/gold/data:ro`
  Permite ao MiddleManager ingerir lotes históricos via task `index_parallel` apontando para `/opt/src/gold/data/fatos`.
* **Deep Storage Compartilhado**:
  Volume Docker `druid_shared:/opt/shared` montado em Coordinator, Historical e MiddleManager, atuando como o armazenamento persistente (*Deep Storage*) de segmentos colunares indexados com compressão LZ4.
* **Metadados Persistentes**:
  Volumes nomeados `metadata_data` (PostgreSQL), `zookeeper_data`, `broker_var` e `coordinator_var` garantem que a reinicialização dos contêineres não cause perda de catálogo, tabelas registradas ou dashboards.

---

## 🔬 3. Cenários de Carga e Perfis de Capacidade (`infra/druid/profiles/`)

Para ensaios de estresse e avaliação empírica de desempenho analítico, o ecossistema disponibiliza 3 perfis de configuração via variáveis de ambiente:

1. **`scenario_01_baseline.env` (1.0 vCPU / 2 GB RAM)**:
   - Configuração estrita de recursos mínimos. Sob concorrência de múltiplos operadores, atinge saturação prematura devido à sobrecarga de processamento vetorial geoespacial.
2. **`scenario_02_balanced.env` (2.0 vCPUs / 4 GB RAM - Padrão de Produção)**:
   - Configuração equilibrada que aloca `-Xms256m -Xmx512m` para o Heap do Broker e `-XX:MaxDirectMemorySize=512m` para processamento de agregações colunares.
   - Suporta **16 clientes analíticos simultâneos** mantendo **0% de falhas HTTP 500** e taxa de vazão sustentada em torno de **2.0 QPS**.
3. **`scenario_03_query_heavy.env` (4.0 vCPUs / 8 GB RAM)**:
   - Configuração orientada a grandes volumes analíticos históricos, expandindo a memória direta para 1024 MiB e acelerando queries complexas com filtros temporais extensos.

---

## ⚡ 4. Diagnóstico de Gargalo: Natureza CPU-Bound

Os ensaios empíricos de concorrência evidenciaram que a stack analítica com dados geoespaciais e streaming de queimadas apresenta comportamento predominantemente **CPU-Bound**:
* O consumo de memória RAM dos nós Docker permaneceu estável entre 70% e 80% do teto mesmo sob concorrência máxima de 16 operadores.
* O aumento de carga concorrente satura os ciclos de vCPU devido ao cálculo vetorial de polígonos, ordenação de centenas de milhares de linhas e serialização JSON para o Apache Superset.
* A adição de núcleos de vCPU no cenário balanceado gerou um ganho relativo de eficiência de aproximadamente **38,8 vezes** em relação ao cenário baseline mononúcleo.
