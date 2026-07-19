# CCO DataOps - Streaming Context (Agent Guide)

Bem-vindo à Fato de Streaming. O coração pulsante da arquitetura lambda/real-time do projeto.

## 🏗️ Separação de Preocupações (SoC)
Não misture extração bruta com lógica matemática.
1. `processors/extractor.py`: Responsável por tratar a linha bruta e limpar datas (cálculo de horas, timestamps UNIX, padronização temporal).
2. `processors/calculators.py`: Cálculos puramente numéricos dos nossos índices de risco analíticos (Ameaça Hospitalar, Criticidade de Fogo, Pressão Territorial, etc). Retorna exclusivmente *floats* e *integers*.
3. `processador.py`: Atua como Maestro. Pega os dados extraídos, aplica o `MotorEspacial` e anexa os `Calculators`.
4. `eventos/eventizador.py`: Fecha focos brutos em eventos operacionais antes do Kafka. Não grave CSV processado por padrão; a persistência pública acontece no Druid via supervisor Kafka.

## 🛡️ O Contrato de Dados (Payload Pydantic)
- A Fato deve ser blindada. O `FocoFatoPayload` e o `EventoFatoPayload` (em `models.py`) são a última linha de defesa estrutural. 
- Mantenha a tipagem em Pydantic extremamente rígida (ex: StrictInt, validator customizado).
- **Atenção**: É ESTRITAMENTE PROIBIDO adicionar descrições literais de strings (ex: `nome_municipio`, `nome_bioma`, `nivel_risco_texto`) ao payload de streaming. 
- Insira apenas Códigos IBGE, Chaves Naturais e Métricas puras. O Apache Druid cuidará da desnormalização em tempo de consulta usando `Lookups` para cruzar com as Dimensões Batch.

## 🚀 Mensageria Kafka
- `produtor_focos.py`: Deve ler `csv.DictReader` rápido e atirar de forma assíncrona.
- `produtor_eventos.py`: Deve ler o CSV bruto em chunks, publicar apenas eventos finalizados no tópico `streaming_eventos_incendio` e manter `path_json` como mancha de visualização do evento.
- Progresso (`progress.jsonl`/`progress.csv`) é evidência operacional da ingestão, não tabela fato processada. Não use esses arquivos como fonte do Druid.
- `kafka_client.py`: O client gerencia o ciclo de vida da fila. Lembre-se do comportamento `linger.ms` e `batch.size` para otimizar compressão e vazão na rede. Nunca atire 1 em 1 sincronicamente no loop central, pois destruirá a performance do produtor. Use acks='all' para tolerância a falhas.

## 🌪️ Fato de Eventos
- A fato nova é `fato_eventos_incendio`, ingerida por supervisor Kafka. Não use `fogo_eventos_stdbscan.csv` nem `fato_focos_incendio` para o fluxo principal de eventos.
- `latitude_centroide` e `longitude_centroide` são âncoras métricas; `path_json` é a mancha do evento no Superset. Não substitua a mancha pelo centróide.
- Comente mudanças nos parâmetros `eps_km`, `eps_dias`, `min_samples` e `max_duration_days`, porque eles definem a interpretação científica do que é um evento.
- A segmentação Druid da fato de eventos deve equilibrar pruning temporal e tamanho de segmento. Evite trocar `MONTH` para `DAY` sem evidência de que os segmentos não ficarão pequenos demais.
- Ao rodar replay completo, registre raw lidas, focos válidos, eventos enviados, taxa e erros por chunk para comprovar que o CSV bruto inteiro foi processado.

## 📝 Comentários em Streaming
- Comente as fronteiras entre extração bruta, cálculo numérico, enriquecimento espacial e montagem da Fato. Isso evita que regras de uma camada vazem para outra.
- Antes de fallbacks de data, coordenada, FK ou métrica, explique o impacto no Kafka/Druid e por que o valor escolhido é seguro.
- Comentários sobre índices de risco devem apontar quais variáveis entram na fórmula e se a saída é métrica contínua ou apenas classificação auxiliar.
- Não comente serialização, loops ou chamadas simples; prefira comentários nos pontos onde o payload Snowflake poderia ser quebrado por mudança futura.
