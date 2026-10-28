# Análise de Consumo de RAM (Memory Footprint)

## A Ideia do Gráfico
O objetivo da série temporal de **Memory Footprint** é rastrear a saúde sistêmica dos contêineres e verificar se há risco de *OOM Killed* (Out-Of-Memory) causado por vazamento de memória (*Memory Leak*) sob estresse severo. No Apache Druid, dois nós ditam o gargalo de RAM: o **Historical** (que aloca segmentos indexados em disco para a memória) e o **Broker** (que consolida essas massas de dados resultantes). 

## Fontes de Dados Utilizadas
- **Arquivo:** `docker_stats.csv`
- **Métricas Chave:** `timestamp` convertido em Minutos Decorridos (Eixo X) e `mem_percent` limitador do Cgroup do container Docker (Eixo Y).
- **Contexto:** Os dados foram colhidos nativamente através da Engine do Docker durante as rajadas do cenário Balanceado.

## Análise dos Resultados
A curva de consumo demonstra que a arquitetura não sofre com retenção infinita de objetos em Heap:
1. **Historical (O Varredor Frio):** A curva mais alta mantém-se estagnada na casa dos 65-75% durante todo o experimento. Como ele aloca segmentos "mmap'ados", seu custo de memória sobe velozmente no startup e estabiliza, atuando como um *buffer* robusto.
2. **Broker (O Consolidador Quente):** A curva inferior oscila nitidamente, exibindo "serras" de consumo (subindo para 60% e caindo para 50%). Isso é o *Garbage Collector* da JVM funcionando de forma ideal. A memória sobe à medida que ele recebe pacotes massivos do Superset, processa os Joins em RAM, serializa para JSON e, ato contínuo, libera esse lixo computacional, devolvendo a memória instantaneamente para a SO.

## Mitigação de Outliers (Anomalias de Desempenho)
**Fenômeno:** Oscilações agudas ("dentes de serrote" longos) no limite de RAM do Broker.
**Causa Raiz:** Montagem de enormes *Payloads*. Quando um painel dispara requisição espacial de 50 mil focos no mapa, o Broker aloca dezenas de milhares de Objetos/Strings pesadas (GeoJSON) na Heap da JVM *antes* de serializar e enviar de volta ao Superset, disparando o uso de memória instantâneo.
**Como Melhorar:** Adotar lógicas de Paginação estritas (Limites duros por consulta geográfica via `LIMIT`/`OFFSET`) para garantir que o painel não faça "dump" completo de dados no front-end, protegendo o Broker contra surtos de alocação violenta. Ligar também o cache a nível de resultado (`druid.broker.cache.useResultLevelCache = true`).

## Conclusões (Impacto no SIRDA)
Para manter o Centro de Controle Operacional (CCO) on-line 24/7 de forma confiável, um sistema não pode "sugar" memória até explodir. A série temporal de *Docker Stats* prova que o Apache Druid respeita estritamente o seu teto *Cgroup limit* de RAM (1.5GB configurado por nó no teste). Assim, mesmo que a CPU se afogue na matemática, o processo nunca morre por vazamento, garantindo a **disponibilidade contínua** (High Availability) exigida pelas operações do SIRDA.
