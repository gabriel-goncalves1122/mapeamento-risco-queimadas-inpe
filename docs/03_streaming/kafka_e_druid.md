# Ingestão e Processamento Contínuo (Apache Kafka e Apache Druid)

A capacidade de absorver, processar e interrogar milhões de eventos geolocalizados por hora exige uma cisão conceitual rígida entre o transporte da mensagem e sua consolidação persistente.

## 1. Log Estruturado e Retenção: Apache Kafka
O **Apache Kafka** atua como uma plataforma de *Streaming* distribuída construída sob os preceitos do *Commit Log* imutável. Ele não processa os dados, mas sim os transporta em tópicos particionados com altíssimo *throughput* e baixa latência (geralmente abaixo da faixa dos milissegundos).

- O módulo `produtor_focos.py` adquire os pacotes orbitais.
- O módulo `processador.py` atua como um nó *Stream Processing* intermediário. Ele intercepta a mensagem bruta, projeta métricas euclidianas complexas de proximidade e índices matemáticos de ameaça estrutural a rodovias e sistemas elétricos (vide `calculators.py`).
- Após enriquecido, o registro final assinado sob forte tipagem Pydantic (`FocoFatoPayload`) é inserido no tópico Kafka `streaming_focos_incendio`, consumido pela datasource Druid `fato_focos_incendio`.
- O payload da fato transporta FKs e métricas. Nomes, classes textuais e geometrias completas permanecem nas dimensões e são resolvidos por joins/lookups no consumo analítico.

## 2. Engine Analítica: Apache Druid
O **Apache Druid** é instanciado na borda consumidora. Trata-se de uma arquitetura colunar (Column-Oriented), projetada essencialmente para buscas geoespaciais em séries temporais. 

Sua arquitetura é subdividida em múltiplos processos cooperativos:
- **MiddleManagers**: Consomem os registros diretamente das partições Kafka no modo Real-Time.
- **Historicals**: Armazenam segmentos profundamente compactados (usando matrizes e dicionários) oriundos do MiddleManager.
- **Broker e Router**: Aceitam e otimizam *queries* (e.g., consultas de polígonos ST_CONTAINS vindas do Superset) espalhando o custo computacional por todos os nós ativos via metodologias *Scatter-Gather*.

O Apache Druid garante que varreduras massivas sob uma topologia Fato altamente densa sejam efetuadas com resposta interativa, eliminando gargalos característicos de bancos transacionais tradicionais frente a petabytes de dados de sensores.
