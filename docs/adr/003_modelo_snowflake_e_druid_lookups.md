# ADR 003: Modelagem Analítica Snowflake Estrita e Lookups no Apache Druid

* **Status:** Aprovado
* **Data:** 2026-10-28
* **Decisores:** Engenharia de Dados CCO-DataOps

---

## 1. Contexto

Em arquiteturas tradicionais de Data Lakehouse, pipelines de streaming frequentemente denormalizam completamente os eventos antes da publicação na mensageria, duplicando atributos textuais (como nomes de municípios, descrições hospitalares e nomes de concessionárias elétricas) em cada linha do payload.

Em cenários de incêndios florestais massivos (com picos de milhares de focos orbitais por hora):
* O tráfego de dados no Apache Kafka é multiplicado exponencialmente, sobrecarregando a largura de banda da rede e os buffers de memória.
* No banco colunar (Apache Druid), dicionários de colunas de texto inflacionam o consumo de memória RAM e aumentam a latência de compressão nos nós MiddleManager.
* Se um município ou concessionária alterar sua razão social, todas as linhas históricas exigem reindexação cara (*backfill*).

---

## 2. Decisão

Adotamos a **Modelagem Snowflake Estrita** associada ao mecanismo de **Lookups em Memória RAM (`cachedNamespace`)** no Apache Druid:

1. **Veto a Strings Decorativas no Payload da Tabela Fato**:
   - Os contratos [`FocoFatoPayload`](../../src/core/domain/foco_fato_payload.py) e [`EventoFatoPayload`](../../src/core/domain/evento_fato_payload.py) contêm **exclusivamente**:
     - Chaves Temporais e Primárias (`data_hora`, `id_foco_orbital`, `fire_event_id`).
     - Chaves Estrangeiras (`fk_municipio_ibge`, `fk_linha_transmissao`, `fk_subestacao`, `fk_terra_indigena`, etc.).
     - Métricas Físicas e Analíticas (`frp`, `risco_fogo`, `precipitacao_mm`, `distancia_*_km`, `area_mancha_km2`).
     - Geometrias compactas `path_json`.
2. **Carga das Dimensões via URI Lookups**:
   - As 7 tabelas de dimensão geradas pela Camada Silver são carregadas via protocolo local `file:///opt/src/silver/data/dimensions/*.csv`.
   - O serviço [`DruidLookupRegistrar`](../../src/silver/lookups/druid_lookup_registrar.py) publica a configuração no Coordinator, que mantém tabelas hash em memória RAM em todos os nós Broker e Historical.
3. **Resolução Dinâmica em Consultas SQL**:
   - Consultas SQL no Superset utilizam a função nativa `LOOKUP(fk, 'mapa_nome')`, resolvendo strings textuais em $O(1)$ no momento da exibição dos dashboards.

---

## 3. Consequências

### Positivas
* **Throughput Máximo de Ingestão**: O tamanho médio do payload JSON no Kafka foi reduzido em mais de 65%, permitindo que a stack absorva picos severos de dados com latência de ingestão $< 100\text{ ms}$.
* **Governança Centralizada**: Alterações semânticas em nomes de municípios ou etnias são aplicadas instantaneamente no CSV dimensional Silver, sem tocar nas tabelas fato históricas.
* **Economia de Recursos**: Redução do footprint de armazenamento em Deep Storage e menor pressão no Heap da JVM do Druid.

### Negativas / Trade-offs
* Consultas SQL dependem da sintaxe `LOOKUP()` do Druid SQL, exigindo disciplina ao formular dashboards no Apache Superset.
