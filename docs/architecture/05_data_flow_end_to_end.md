# Data Flow End-to-End da Aplicação (Streaming e OLAP)

Este documento detalha o fluxo completo de dados na arquitetura **Snowflake** e **Medallion**, evidenciando as decisões de bifurcação paralela no nível de mensageria (Kafka) e as estratégias analíticas de indexamento vetorial (Apache Druid) e visualização (Apache Superset).

A representação arquitetural separa os conceitos de **Focos Unitários (Detecções Orbitais Atômicas)** e **Eventos Complexos (Desastres Consolidados via IA)** no momento da ingestão e persistência.

---

## 1. O Diagrama End-to-End

O diagrama abaixo ilustra o trânsito da informação desde a extração bruta das coordenadas orbitais até a exposição em Dashboards Analíticos:

```mermaid
flowchart TD
    %% Ingestao Bruta
    subgraph ACQUISITION [Camada Bronze: Data Acquisition / Raw]
        api(API Focos INPE / Carga em Batches)
    end

    %% Processamento Streaming e POO
    subgraph STREAMING [Camada Gold: Streaming Processing Pipeline]
        prod(ProdutorFocosGold: Ingestão Dual-Branch)
        
        proc_focos(Enriquecimento Espacial Atômico)
        motor[(MotorEspacial / SpatialEngineProtocol)]
        payload_focos([FocoFatoPayload: Contrato Pydantic])
        publisher_focos[StreamPublisherBase: KafkaEventProducer]
        topic_focos(Kafka Topic: focos-incendio)

        buffer(Buffer de Janela Espaço-Temporal)
        dbscan(EventizadorIncendios: ST-DBSCAN)
        payload_eventos([EventoFatoPayload: Contrato Pydantic])
        publisher_eventos[StreamPublisherBase: KafkaEventProducer]
        topic_eventos(Kafka Topic: eventos-incendio)

        prod --> proc_focos
        prod --> buffer

        %% Ramo Focos
        proc_focos -->|cruza coordenadas WGS84| motor
        proc_focos -->|valida tipos e FKs| payload_focos
        payload_focos --> publisher_focos
        publisher_focos --> topic_focos

        %% Ramo Eventos
        buffer --> dbscan
        dbscan -->|cruza polígonos e infra| motor
        dbscan -->|rejeita NaN e tipa| payload_eventos
        payload_eventos --> publisher_eventos
        publisher_eventos --> topic_eventos
    end

    %% Armazenamento Analítico
    subgraph OLAP [Armazenamento Analítico: Apache Druid]
        mid_focos(Kafka Indexing Service: Supervisor)
        mid_eventos(Kafka Indexing Service: Supervisor)
        
        fato_focos[(Datasource: fato_focos_incendio)]
        fato_eventos[(Datasource: fato_eventos_incendio)]

        topic_focos --> mid_focos
        topic_eventos --> mid_eventos

        mid_focos --> fato_focos
        mid_eventos --> fato_eventos
    end

    %% Visualização
    subgraph PRESENTATION [Camada de Apresentação: Apache Superset]
        superset(Apache Superset)
        dash_risco[Dashboards de Risco ONS / SIN]
        dash_terr[Análise de Territórios e Terras Indígenas]
        dash_hosp[Impacto em Redes Hospitalares CNES]

        fato_focos -.->|SQL via Lookups Silver| superset
        fato_eventos -.->|SQL via Lookups Silver| superset
        
        superset --> dash_risco
        superset --> dash_terr
        superset --> dash_hosp
    end

    api -->|Ingestão Contínua / Partições| prod
```

---

## 2. Pilares do Fluxo de Dados

A arquitetura não possui processamento intermediário ocioso ou persistência de tópicos brutos redundantes. A ingestão executa o *enriquecimento espacial* e a *eventização* no momento da leitura, publicando as Fatos prontas diretamente em tópicos consumíveis por sistemas OLAP.

### 2.1 Streaming Dual-Branch
Ao capturar dados, o [`ProdutorFocosGold`](../../src/gold/streaming/produtor_focos.py) bifurca as responsabilidades paralelamente:
- **Ramo dos Focos (Streaming Atômico)**: Processa cada coordenada individualmente, consultando o [`SpatialEngineProtocol`](../../src/core/contracts/contracts.py) para identificar distâncias mínimas até linhas de transmissão, subestações, rodovias federais, hospitais e terras indígenas. A latência é na ordem de milissegundos.
- **Ramo dos Eventos (Micro-batching Espaço-Temporal)**: Acumula pontos observacionais em buffer. Ao completar o ciclo de janela, invoca o [`EventizadorIncendios`](../../src/gold/science/dbscan/eventizador.py). Este componente agrupa anomalias térmicas correlacionadas no espaço e tempo via **ST-DBSCAN**, gera a envoltória convexa (*Convex Hull*) via [`EventGeometryBuilder`](../../src/gold/science/dbscan/event_geometry_builder.py), serializa o polígono em `path_json` e computa agregações matemáticas de área ($km^2$), FRP total e índices de ameaça.

### 2.2 Contratos Estritos (Pydantic) e Regra Snowflake
A preservação da arquitetura **Snowflake** é estritamente garantida por código:
- Os contratos [`FocoFatoPayload`](../../src/core/domain/foco_fato_payload.py) e [`EventoFatoPayload`](../../src/core/domain/evento_fato_payload.py) possuem configuração `extra="forbid"`.
- Nenhuma string textual decorativa (como nomes literais de municípios, estados ou concessionárias) transita pelo Kafka ou é persistida nas tabelas fato do Druid. Apenas identificadores inteiros/hashes (Foreign Keys) e métricas numéricas compõem os registros.
- O validador `rejeitar_nan_inf` impede que valores indefinidos de ponto flutuante corrompam o parser JSON dos Supervisors do Druid.

### 2.3 Resolução em Tempo de Consulta via Lookups
No Apache Druid, as dimensões estáticas geradas na camada Silver (`dim_municipios`, `dim_hospitais`, `dim_ons_linhas_transmissao`, etc.) são carregadas em memória RAM como **Lookups**. Quando uma consulta SQL é disparada pelo **Apache Superset**, o Druid resolve as Foreign Keys em nomes, concessionárias e regiões instantaneamente, poupando a rede do fardo de transmitir strings repetidas em milhões de mensagens de streaming.
