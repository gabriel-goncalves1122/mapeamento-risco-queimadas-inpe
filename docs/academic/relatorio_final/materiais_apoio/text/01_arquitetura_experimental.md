# 1. Arquitetura Experimental do Teste de Carga

Este documento detalha o desenho do ecossistema alvo durante os *benchmarks* de capacidade do Apache Druid, servindo como registro metodológico para a validação do *data warehouse* da solução.

## Escopo e Limitação do Teste

O foco do experimento recai estritamente sobre a **camada OLAP de consulta**. Durante a execução das *queries*, nenhuma etapa de ingestão de dados em tempo real ou processamento de mensagens foi ativada.

- **Ausência de *Streaming***: O produtor Kafka, o injetor Python e o nó `MiddleManager` do Druid foram inativados ou ignorados durante a medição. Isso garante que a carga de trabalho medida reflete puramente a capacidade de resposta a consultas, sem o ruído do processamento de ingestão competindo por I/O e CPU.
- **Isolamento de Dimensões**: As dimensões estáticas (hospitais, municípios, terras indígenas e rodovias) já haviam sido previamente indexadas em segmentos persistentes no *deep storage*. A tabela fato de eventos ou focos não fez parte das consultas para manter a matriz de testes determinística.

A pergunta metodológica que governa este experimento é: *Dado que as dimensões já estão carregadas e os segmentos distribuídos, qual o comportamento dos nós de roteamento e processamento quando expostos a requisições simultâneas contendo agregações e joins espaciais pesados?*

## O Papel dos Nós Avaliados

Na arquitetura modular do Apache Druid, dois nós principais participam do ciclo de vida de uma *query* que varre dados em repouso. O dimensionamento adequado desses componentes é o alvo empírico do teste.

### Broker
O `Broker` é o ponto de entrada da consulta SQL.
- **Função Metodológica**: Sua carga primária neste teste decorre do planejamento das *queries* SQL (tradução para a sintaxe nativa do Druid), roteamento para o nó de armazenamento adequado e o *merge* final dos resultados.
- **Comportamento Esperado**: O *Broker* sofre forte impacto quando as consultas exigem *joins* e uniões volumosas, pois precisa compilar o resultado de fragmentos dispersos.

### Historical
O `Historical` é o cavalo de batalha do armazenamento de longo prazo.
- **Função Metodológica**: Ele carrega os arquivos baseados em colunas a partir do cache local, descompacta segmentos e executa a filtragem pesada.
- **Comportamento Esperado**: Nos cenários onde a concorrência se eleva e o motor é forçado a cruzar coordenadas geográficas (*ST_CONTAINS*, *ST_DISTANCE*), espera-se que o *Historical* sature seus recursos de CPU e memória nativa (*direct memory*).

### Coadjuvantes Operacionais
- **Coordinator**: Manteve-se ativo para monitorar o `loadstatus` (assegurando que 100% dos segmentos estavam disponíveis), mas não participou ativamente da varredura dos dados.
- **Zookeeper / PostgreSQL**: Suportes de orquestração de metadados, cujas latências de rede e CPU local provaram-se irrelevantes (não causaram contenção na matriz).

## Infraestrutura Física e Limites Locais

Para fins de reprodutibilidade, o experimento foi executado em hardware não-distribuído (ambiente local ou virtualizado).

- **CPU Lógica**: 8 núcleos (*cores*).
- **RAM Disponível**: 7.48 GiB de memória física total, com variação instantânea (cerca de 1.45 GiB livres no host antes de subir a plataforma Dockerizada).

Esses fatores restritivos são essenciais para a validade do teste empírico. O Druid administra a concorrência de recursos usando o processador, memória *heap* do Java e memória *off-heap* alocada diretamente para descompactar os segmentos. Ampliar arbitrariamente os *containers* de todos os nós poderia levar ao *thrashing* (competição excessiva por recursos entre o host e a JVM), mascarando gargalos genuínos do cluster simulado. 

Por conta destas restrições, as três variáveis de perfis (*Baseline*, *Balanced*, *Query Heavy*) foram cuidadosamente balanceadas em suas alocações, sem nunca ultrapassar o teto estrito do *hardware*.
