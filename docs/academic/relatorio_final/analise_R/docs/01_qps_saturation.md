# Análise de Saturação de Throughput (QPS)

## A Ideia do Gráfico
O gráfico de **Saturação de QPS (Queries Per Second)** visa identificar o "ponto de quebra" da infraestrutura analítica. O objetivo é responder à pergunta: *A partir de quantos operadores simultâneos acessando o painel do CCO o sistema para de escalar linearmente e começa a enfileirar processos até colapsar?*

## Fontes de Dados Utilizadas
- **Arquivo:** `capacity_enriched.csv`
- **Métricas Chave:** `concurrency_factor` (eixo X) e taxa consolidada de requisições concluídas com sucesso.
- **Contexto:** Os dados foram extraídos dos resumos gerados após cada bateria de estresse, testando de 1 a 16 *threads* concorrentes contra as topologias Baseline (1.0 CPU), Balanced (1.5 CPU) e Query Heavy (2.0 CPU).

## Análise dos Resultados
A curva demonstra um fenômeno clássico de saturação de CPU. 
1. O nódulo **Baseline** (vermelho) quebra precocemente; com apenas 1 a 2 *threads*, ele já atinge seu teto arquitetural de processamento, provando que 1.0 vCPU não é suficiente para a carga matemática exigida pelos Joins Espaciais GeoJSON.
2. O ambiente **Query Heavy** (roxo) demonstrou resiliência formidável. Ele conseguiu acompanhar o escalonamento até a casa de 8 *threads* simultâneas com crescimento quase linear. Após 8 conexões pesadas ativas, a curva achata (saturação em "platô"), significando que novas conexões aguardam em fila, mas o sistema não deixa de entregá-las.

## Mitigação de Outliers (Anomalias de Desempenho)
**Fenômeno:** Durante a escalada, percebem-se instantes microscópicos de queda no QPS, onde o painel engasga.
**Causa Raiz:** *Thread Contention* ou Pausas de *Garbage Collection (GC)*. Quando muitos operadores acionam os mesmos filtros simultaneamente, o pool de processamento HTTP do Broker enfileira requisições. 
**Como Melhorar:** Otimizar a JVM trocando o coletor de lixo para arquiteturas sem pausa (G1GC ou ZGC) e aumentar a configuração `druid.server.http.numThreads` no arquivo *runtime.properties* do nó Broker.

## Conclusões (Impacto no SIRDA)
Para um Centro de Controle Operacional (CCO) do projeto SIRDA, onde diversos operadores monitoram emergências simultaneamente, implementar o Druid com hardware mínimo (Baseline) seria desastroso e resultaria em painéis "congelados". Fica evidenciado que o perfil **Query Heavy (2.0 vCPU)** é a recomendação mínima de arquitetura em nuvem para garantir a atualização fluida (Throughput saudável) dos gráficos de monitoramento ambiental.
