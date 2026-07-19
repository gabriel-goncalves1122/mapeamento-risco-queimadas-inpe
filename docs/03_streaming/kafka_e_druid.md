# Ingestão e Processamento Contínuo (Apache Kafka e Apache Druid)

A capacidade de absorver, processar e interrogar milhões de eventos geolocalizados por hora exige uma cisão conceitual rígida entre o transporte ininterrupto da mensagem e sua consolidação persistente em disco.

## 1. Log Estruturado e Retenção Estrita: Apache Kafka
O **Apache Kafka** orquestra o *streaming* distribuído na camada de borda baseando-se nos ditames do *Commit Log* imutável. Essencialmente, ele encapsula os eventos analíticos para desacoplar a frequência estocástica do envio e as limitações de ingestão dos barramentos persistentes, viabilizando altíssimo *throughput*.

O `kafka_client.py` embute heurísticas de proteção (nível bancário) e loteamento inteligente:
- **`allow_nan=False`**: Garante imunidade a *poison pills*. A serialização repudia variáveis corrompidas e Not-a-Number (NaN) antes que o banco final Druid sofra poluição silenciosa.
- **`acks='all'` e `max_in_flight=1`**: Impõem sincronia replicada. Assegura a recepção da métrica entre todos os nodos subsidiários sem sacrificar a ordem temporal estrita das perturbações térmicas.
- **Loteamento Lógico (`linger_ms` / `batch_size`)**: Para aliviar tráfego, emula o empacotamento. Focos de calor discretos são agregados por dezenas de milissegundos e transmitidos por rajadas em uma matriz `gzip`, o que converte um fluxo oneroso numa fenda transacional maciça.

Ademais, as instâncias produtoras baseiam-se em requisições *Fire and Forget* (chamadas assíncronas de I/O) para não bloquear o pipeline Python, capturando anomalias em instâncias `callback`.

## 2. Engine Analítica Temporal: Apache Druid
O **Apache Druid** instila-se como um banco colunar focado em buscas geoespaciais e de séries temporais de baixa latência.

Sua arquitetura assíncrona divide-se em estratos lógicos:
- **MiddleManagers**: Capturam nativamente eventos do Kafka real-time em contêineres e constroem fragmentos transicionais.
- **Historicals**: Armazenam segmentos hiper-compactos, amparando-se em codificações por dicionário e bitmaps (*Roaring Bitmaps*).
- **Broker**: Aplica inferência distributiva (*Scatter-Gather*). Encapsula métricas (FRP) sobrepostas a polígonos e devolve agregações sob índices com precisão centesimal.

Tal arcabouço impede congestionamentos catastróficos, outorgando *dashboards* fluidos e garantindo integridade de governança sob picos sazonais extremos nas ocorrências de fogo florestal.

## 3. Granularidade e Segmentação
As dimensões estáticas usam `segmentGranularity = ALL`, pois são tabelas pequenas e substituíveis por carga batch completa. Já as fatos temporais usam `segmentGranularity = MONTH` com `maxRowsPerSegment` elevado, reduzindo a proliferação de *tiny segments* e aproximando os arquivos persistidos da faixa operacional recomendada para segmentos maiores.
