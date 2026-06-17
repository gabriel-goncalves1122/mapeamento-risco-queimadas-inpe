# Gerenciamento de Infraestrutura via Contêineres

O encapsulamento da malha de computação analítica, via *OS-level Virtualization* (Docker), blinda o sistema contra os detritos ambientais típicos do ecossistema de *Host OS*, promovendo a imutabilidade estrita das execuções em qualquer máquina reprodutora da ciência metodológica aplicada na pesquisa.

## 1. Arquitetura Multisserviços e Orquestração Local
O orquestrador descritivo contido em `docker-compose.yaml` estipula as alocações determinísticas para o ciclo de serviços da plataforma, estabelecendo uma rede intra-virtual (overlay net) para assegurar o isolamento do tráfego local.

- **Sistemas de Estado**: Apache Kafka e Apache Druid necessitam fundamentalmente do `Zookeeper` como vetor distribuído para estabilizar partições ativas e consensos paralelos.
- **Persistência Relacional Suporte**: O banco transacional PostgreSQL armazena restritivamente dados e esquemas de configuração de repositório (Metadados do Apache Superset e Grafo de Históricos do Dagster).

## 2. Otimização Cirúrgica de Recursos Analíticos
O tráfego de métricas espaciais interacionais requer otimizações imperativas para hardware restrito (e.g., máquinas computacionais convencionais restritas a 8 threads virtuais de CPU e escassa RAM).

Sob a diretiva padrão do Motor de Contêineres, as *Limits Flags* (`deploy.resources.limits`) limitaram, em *Hard-Capping*, o consumo total dos processos subjacentes. A configuração do Java Virtual Machine (`JAVA_OPTS -Xms -Xmx -XX:MaxDirectMemorySize`) no Kafka e nos *nodes* espaciais do Apache Druid previnem coletas de lixo dispendiosas (Garbage Collection Pauses) desproporcionais ou estouro virtual do Linux Kernel (*OOMKilled Event*), provendo resiliência máxima mediante execuções ininterruptas sob os preceitos de Engenharia SRE (Site Reliability Engineering).
