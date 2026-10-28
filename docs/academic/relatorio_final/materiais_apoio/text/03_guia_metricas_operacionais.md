# 3. Guia de Métricas Operacionais

O *benchmark* de estresse de um banco analítico como o Apache Druid pode gerar métricas ilusórias caso lidas de forma isolada (ex: exibir alto *throughput* escondendo a quebra do serviço por conta de falhas silenciosas). Este guia formaliza os critérios rigorosos utilizados para classificar o sucesso, a degradação ou a saturação do ecossistema frente a requisições de *Data Analytics*.

## Glossário de Métricas

Para fins de reprodutibilidade, as variáveis de performance capturadas do cliente e do *Docker Daemon* foram classificadas e normalizadas segundo os conceitos abaixo:

| Métrica | Definição | Como Interpretar | Riscos / Cuidado na Leitura |
| :--- | :--- | :--- | :--- |
| **QPS** (*Queries Per Second*) | Consultas finalizadas por segundo dentro do bloco temporal medido. | Maior QPS indica maior vazão e eficiência do roteamento do *Broker*. | QPS pode parecer excepcionalmente bom quando muitas consultas falham rapidamente, pois a devolução de falha requer poucos milissegundos. **QPS só é ganho real se o Erro for 0.** |
| **p50** (Mediana) | Metade das requisições foi mais rápida que esse valor absoluto (ms). | Mostra a experiência "típica" de uma única consulta bem-sucedida. | Não revela cauda longa nem saturação extrema; esconde as queries de agrupamento complexo que afetam o Superset. |
| **p95** (Latência de Cauda) | Latência abaixo da qual 95% das requisições ficaram circunscritas. | **Principal métrica de estabilidade** percebida em *dashboards*. Se o p95 for alto, o *dashboard* demora a renderizar, independentemente do p50. | Deve obrigatoriamente ser lida em conjunto com a Taxa de Erro. |
| **p99** | Latência de cauda extrema (99% concluídas abaixo desse limite). | Indica o custo dos piores casos analíticos operacionais ainda bem-sucedidos. | Com poucas amostras (concorrência N=1), oscila bastante e introduz ruído, mas ainda assim revela o teto de *timeout*. |
| **Taxa de Erro** | Percentual de requisições que terminaram em *timeout*, exceção Java no Broker, ou erro HTTP/TCP. | **Qualquer valor acima de 0%** num teste restrito e local sinaliza limite de capacidade atingido. | Nunca se deve comparar latência p95/p99 entre um cenário com erro 0% e outro com erro 5%. A falha mascara o tempo real da resposta. |
| **Saturação** | Classificação (booleana ou de limite) derivada do erro ou exaustão de CPU/Memória. | Marca o momento exato em que o cenário deixou de sustentar a carga de forma confiável. | Uma rodada saturada não é um ganho de *performance*, é um estrangulamento arquitetural. |
| **CPU e RAM Docker** | Consumo absoluto normalizado extraído via `docker stats` para *Broker* e *Historical*. | Picos de CPU > 100% indicam consumo multi-core (mais de uma CPU lógica emparelhada pelo sistema). | Comparar o percentual com os limites estipulados para o perfil em específico, não com a capacidade macro do *host*. Queda percentual pode ser mera decorrência do aumento do teto configurado, não da otimização da *query*. |

*(Baseado no catálogo semântico importado de `tables/metric_definitions.tex`)*

## Abordagem de Cache (Cold vs. Warm Start)

Para espelhar a utilização cotidiana do Apache Superset por um usuário explorando painéis visuais interativos, a matriz de carga avalia duas facetas de disponibilidade de cache:

1. **Cold-start (Início Frio)**: Mede o custo computacional puro de buscar os dados armazenados em disco (segmentos profundos), descompactá-los sem uso de reaproveitamento temporal na JVM, e agrupá-los na memória *off-heap* (*direct memory*).
2. **Warm-start (Aquecido)**: Simula os painéis analíticos aplicando cache nos metadados da consulta. Demonstra o ganho da resposta repetida, mas atesta o fato primário: o *cache* mitiga leitura, mas não corrige a falta crônica de CPU e Memória para alocar múltiplos *Merge Buffers* ou processar junções (*joins*) de alta cardinalidade sob forte concorrência.

## Ordem Hierárquica de Auditoria do Benchmark

Para evitar interpretações superficiais, os dados extraídos das rodadas (N=1, N=2, N=4) devem sempre ser processados por um **funil condicional**:

1. Validar se o `Loadstatus` registrou 100% de disponibilidade, comprovando que nenhum *segmento* foi ejetado do cluster.
2. Ler a **Taxa de Erro**. Cenários com qualquer erro perdem validação analítica para a próxima etapa.
3. Analisar e confrontar o **QPS** apenas entre perfis/cenários que comprovaram 0% de erro (Equivalência Operacional).
4. Subir a lupa para a **Cauda (p95 / p99)** para entender as perdas na experiência do usuário final.
5. Inspecionar o gráfico de **CPU/Memória do Docker** (ver pasta `figures/`) para atestar se o gargalo foi orquestração (*Broker*) ou I/O e computação bruta (*Historical*).
