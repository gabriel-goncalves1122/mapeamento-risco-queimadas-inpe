# Arquitetura Orientada a Objetos (POO) e Princípios SOLID

Este documento formaliza o design arquitetural de software do projeto, demonstrando a aplicação dos princípios **SOLID**, padrões de projeto (*Design Patterns*) e tipagem estrita na orquestração da **Arquitetura Medalhão** (Bronze, Silver, Gold).

A transição de scripts isolados e procedurais para uma base orientada a objetos (POO) estruturada garante manutenibilidade, testabilidade com mocks, rastreabilidade de telemetria e desacoplamento das camadas analíticas.

---

## 1. Mapeamento dos Princípios SOLID

### 1.1 S — Single Responsibility Principle (SRP)
Cada módulo, classe e arquivo possui uma única responsabilidade de domínio bem delineada, respeitando a regra de **1 Classe = 1 Arquivo** em nomenclatura `snake_case`:
- **Contratos de Dados**: `src/core/domain/foco_fato_payload.py` e `src/core/domain/evento_fato_payload.py` definem exclusivamente contratos Pydantic imutáveis para serialização Kafka/Druid.
- **Motor Espacial**: O antigo bloco monolítico foi decomposto em:
  - [`SpatialLayerSpec`](../../src/silver/spatial/spatial_layer_spec.py): Especificação pura e imutável de metadados de uma camada geoespacial (caminho, CRS, colunas, buffers).
  - [`SpatialLayerLoader`](../../src/silver/spatial/spatial_layer_loader.py): Leitura física de GeoDataFrames do disco e reprojeção métrica para SIRGAS 2000 (`EPSG:5880`).
  - [`SpatialLayerCatalog`](../../src/silver/spatial/spatial_layer_catalog.py): Catálogo e registro desacoplado de todas as camadas do sistema.
  - [`DistanceClassifier`](../../src/silver/spatial/distance_classifier.py): Cálculo puro de faixas e scores de proximidade a infraestruturas.
  - [`MotorEspacial`](../../src/silver/spatial/motor_espacial.py): Motor de consulta geoespacial otimizado com STRtree e buffers indexados.
- **Data Science (ST-DBSCAN)**: Segregado em:
  - [`EventoConfig`](../../src/gold/science/dbscan/evento_config.py): Dataclass imutável de hiperparâmetros espaciais e temporais ($\varepsilon_{km}$, $\varepsilon_{dias}$, $min\_samples$).
  - [`EventGeometryBuilder`](../../src/gold/science/dbscan/event_geometry_builder.py): Cálculo geométrico puro de Convex Hull, baricentro e serialização `path_json`.
  - [`EventizadorIncendios`](../../src/gold/science/dbscan/eventizador.py): Execução do algoritmo de clusterização e enriquecimento estatístico.
- **Utilitários e Auditoria**:
  - [`PathJsonCodec`](../../src/silver/utils/path_json_codec.py): Conversão determinística de geometrias Shapely para coordenadas GeoJSON / Deck.gl.
  - [`StreamingAuditLogger`](../../src/gold/streaming/streaming_audit_logger.py): Registro e estatísticas de auditoria de mensagens publicadas no Kafka, isolando logging da lógica de rede.

### 1.2 O — Open/Closed Principle (OCP)
O sistema é aberto para extensão e fechado para modificação:
- **Catálogo de Camadas Espaciais**: O [`SpatialLayerCatalog`](../../src/silver/spatial/spatial_layer_catalog.py) permite registrar novas infraestruturas críticas (ex: gasodutos ou ferrovias) através do método `register()`, sem alterar nenhuma linha do [`MotorEspacial`](../../src/silver/spatial/motor_espacial.py).
- **Extensões de Dimensões Silver**: Novas dimensões geográficas herdam de [`ETLDimBase`](../../src/silver/etl/base_etl_dim.py), implementando apenas os ganchos abstratos `_extract()` e `_transform()`. O fluxo de gravação, validação e integridade permanece inalterado.

### 1.3 L — Liskov Substitution Principle (LSP)
Subtipos podem substituir seus tipos base sem alterar a corretude do sistema:
- Todos os componentes operacionais das camadas Bronze, Silver e Gold herdam do contrato base [`ExecutablePipelineStep`](../../src/core/contracts/contracts.py).
- O orquestrador Dagster ([`repo.py`](../../src/orchestration/dagster/repo.py)) e os orquestradores CLI executam qualquer etapa chamando `step.execute()`, recebendo telemetria padronizada independente de ser uma extração ArcGIS da ANEEL, uma transformação espacial Silver ou o modelo de Centralidade de Grafos NetworkX da Gold.
- Implementações de mensageria baseadas em [`StreamPublisherBase`](../../src/core/contracts/contracts.py) podem ser substituídas por mocks em memória nos testes unitários sem impactar os produtores de eventos.

### 1.4 I — Interface Segregation Principle (ISP)
Interfaces enxutas e focadas substituem interfaces monolíticas:
- [`SpatialEngineProtocol`](../../src/core/contracts/contracts.py): Exponibiliza aos consumidores exclusivamente os métodos de consulta (`analisar_todas_ameacas` e `intersecoes_camada`). Consumidores da Gold não tomam conhecimento de geometrias internas, STRtrees ou métodos de carregamento de camadas.
- [`StreamPublisherBase`](../../src/core/contracts/contracts.py): Define unicamente operações essenciais de envio e drenagem de buffer (`enviar`, `flush`, `flush_and_close`).
- [`DataValidatorBase`](../../src/core/contracts/contracts.py): Exige apenas o método `validate()`, retornando o dataclass imutável `ValidationReport`.

### 1.5 D — Dependency Inversion Principle (DIP)
Módulos de alto nível dependem de abstrações, não de implementações concretas:
- O orquestrador Dagster ([`src/orchestration/dagster/repo.py`](../../src/orchestration/dagster/repo.py)) depende da abstração [`ExecutablePipelineStep`](../../src/core/contracts/contracts.py).
- O produtor streaming ([`ProdutorFocosGold`](../../src/gold/streaming/produtor_focos.py)) recebe por Injeção de Dependência (DI) instâncias de [`SpatialEngineProtocol`](../../src/core/contracts/contracts.py) e [`StreamPublisherBase`](../../src/core/contracts/contracts.py), desacoplando a lógica de enriquecimento analítico do driver concreto de Kafka e da instância de disco do motor espacial.

---

## 2. Padrões de Projeto (Design Patterns) Implementados

| Padrão | Onde é Aplicado | Benefício Técnico |
|---|---|---|
| **Template Method** | [`ExecutablePipelineStep`](../../src/core/contracts/contracts.py) | O método `execute()` controla medição de latência em milissegundos e logging padronizado, invocando o gancho protegido `_run()` implementado pelas subclasses. |
| **Context Manager** | [`StreamPublisherBase`](../../src/core/contracts/contracts.py) | Permite o uso do bloco `with` na publicação Kafka (`KafkaEventProducer`), garantindo flush obrigatório e encerramento determinístico de conexões de rede mesmo sob exceções. |
| **Protocol / Duck Typing** | [`SpatialEngineProtocol`](../../src/core/contracts/contracts.py) | Decorado com `@runtime_checkable`, permite desacoplamento total e teste com mocks rápidos sem herança forçada. |
| **Catalog / Specification** | [`SpatialLayerCatalog`](../../src/silver/spatial/spatial_layer_catalog.py) e [`SpatialLayerSpec`](../../src/silver/spatial/spatial_layer_spec.py) | Parametriza carregamento de arquivos vetoriais e regras de buffer sem acoplar o carregador à lógica de negócio. |
| **Façade** | [`src/core/domain/models.py`](../../src/core/domain/models.py) | Reexporta os contratos segregados `FocoFatoPayload` e `EventoFatoPayload`, preservando compatibilidade retroativa para imports externos legados. |

---

## 3. Diagramas Arquiteturais

### 3.1 Diagrama de Classes (Hierarquia POO & SOLID)

```mermaid
classDiagram
    direction TB

    class ExecutablePipelineStep~TResult~ {
        <<abstract>>
        +step_name: str
        +execute(*args, **kwargs) TResult
        #_run(*args, **kwargs)* TResult
    }

    class SpatialEngineProtocol {
        <<protocol>>
        +analisar_todas_ameacas(lat: float, lon: float) dict
        +intersecoes_camada(nome_camada: str, coords: list) list
    }

    class StreamPublisherBase {
        <<abstract>>
        +enviar(topico: str, payload: dict)* Any
        +flush()* void
        +flush_and_close()* void
        +__enter__() StreamPublisherBase
        +__exit__(exc_type, exc_val, exc_tb) bool
    }

    class AneelArcGisExtractor {
        #_run() dict
    }

    class ETLDimBase {
        <<abstract>>
        #_extract()* DataFrame
        #_transform(df: DataFrame)* DataFrame
        #_run() DataFrame
    }

    class ETLDimMunicipios {
        #_extract() DataFrame
        #_transform(df: DataFrame) DataFrame
    }

    class ETLDimHospitais {
        #_extract() DataFrame
        #_transform(df: DataFrame) DataFrame
    }

    class ETLDimLinhasTransmissao {
        #_extract() DataFrame
        #_transform(df: DataFrame) DataFrame
    }

    class EventizadorIncendios {
        -config: EventoConfig
        -spatial_engine: SpatialEngineProtocol
        #_run() DataFrame
    }

    class SINNetworkCentralityModel {
        +construir_grafo(df_sub, df_lin) tuple
        +calcular_centralidade(G, df_sub) DataFrame
        #_run() DataFrame
    }

    class MotorEspacial {
        -catalog: SpatialLayerCatalog
        -loader: SpatialLayerLoader
        +analisar_todas_ameacas(lat: float, lon: float) dict
        +intersecoes_camada(nome_camada: str, coords: list) list
    }

    class KafkaEventProducer {
        -producer: KafkaProducer
        +enviar(topico: str, payload: dict) Any
        +flush() void
        +flush_and_close() void
    }

    class ProdutorFocosGold {
        -spatial_engine: SpatialEngineProtocol
        -publisher: StreamPublisherBase
        +processar_streaming() void
    }

    ExecutablePipelineStep <|-- AneelArcGisExtractor : LSP
    ExecutablePipelineStep <|-- ETLDimBase : LSP
    ETLDimBase <|-- ETLDimMunicipios
    ETLDimBase <|-- ETLDimHospitais
    ETLDimBase <|-- ETLDimLinhasTransmissao
    ExecutablePipelineStep <|-- EventizadorIncendios : LSP
    ExecutablePipelineStep <|-- SINNetworkCentralityModel : LSP

    SpatialEngineProtocol <|.. MotorEspacial : implements (DIP)
    StreamPublisherBase <|-- KafkaEventProducer : implements (DIP)

    ProdutorFocosGold --> SpatialEngineProtocol : DIP
    ProdutorFocosGold --> StreamPublisherBase : DIP
```

---

### 3.2 Diagrama de Sequência: Execução de Asset no Dagster via POO

O Dagster invoca as etapas de pipeline em memória, eliminando a inicialização lenta de subprocessos e capturando a medição de tempo fornecida pelo *Template Method*.

```mermaid
sequenceDiagram
    autonumber
    actor DagsterDaemon as Dagster Daemon / Engine
    participant Repo as repo.py (execute_pipeline_step)
    participant Context as AssetExecutionContext
    participant Step as ExecutablePipelineStep (ex: ETLDimMunicipios)
    participant Domain as Regra de Negócio (_run)
    participant Disk as Camada Silver (Parquet/CSV)

    DagsterDaemon ->> Repo: Executar Asset (dim_municipios)
    Repo ->> Context: log.info("Executando componente POO: ETLDimMunicipios")
    Repo ->> Step: execute()
    activate Step
    Note over Step: Inicia cronômetro (perf_counter)
    Step ->> Domain: _run()
    activate Domain
    Domain ->> Disk: Leitura de insumos Bronze e Geometrias
    Domain ->> Domain: Reprojeção SIRGAS 2000 & path_json
    Domain ->> Disk: Escrita de dim_municipios_coordenadas.csv
    Domain -->> Step: Retorna DataFrame processado
    deactivate Domain
    Note over Step: Finaliza cronômetro e calcula duração (ms)
    Step -->> Repo: Retorna DataFrame final
    deactivate Step
    Repo ->> Context: log.info("Componente concluído em X ms (registros: N)")
    Repo -->> DagsterDaemon: Asset Materialization Sucesso
```

---

### 3.3 Diagrama Entidade-Relacionamento (Modelo Analítico Snowflake)

A modelagem de dados preserva integridade referencial rígida entre as Tabelas Fato da Camada Gold e as Tabelas de Dimensão da Camada Silver:

```mermaid
erDiagram
    FATO_FOCOS_INCENDIO ||--o{ DIM_MUNICIPIOS : "fk_municipio"
    FATO_FOCOS_INCENDIO ||--o{ DIM_HOSPITAIS : "fk_hospital_proximo"
    FATO_FOCOS_INCENDIO ||--o{ DIM_TERRAS_INDIGENAS : "fk_terra_indigena"
    FATO_FOCOS_INCENDIO ||--o{ DIM_LINHAS_TRANSMISSAO : "fk_linha_transmissao"
    FATO_FOCOS_INCENDIO ||--o{ DIM_SUBESTACOES : "fk_subestacao"
    FATO_FOCOS_INCENDIO ||--o{ DIM_SISTEMAS_ISOLADOS : "fk_sistema_isolado"
    FATO_FOCOS_INCENDIO ||--o{ DIM_RODOVIAS_FEDERAIS : "fk_trecho_rodoviario"

    FATO_EVENTOS_INCENDIO ||--o{ DIM_MUNICIPIOS : "fk_municipio_principal"
    FATO_EVENTOS_INCENDIO ||--o{ DIM_HOSPITAIS : "fk_hospital"
    FATO_EVENTOS_INCENDIO ||--o{ DIM_TERRAS_INDIGENAS : "fk_terra_indigena"
    FATO_EVENTOS_INCENDIO ||--o{ DIM_LINHAS_TRANSMISSAO : "fk_linha_transmissao"
    FATO_EVENTOS_INCENDIO ||--o{ DIM_SUBESTACOES : "fk_subestacao"
    FATO_EVENTOS_INCENDIO ||--o{ DIM_SISTEMAS_ISOLADOS : "fk_sistema_isolado"
    FATO_EVENTOS_INCENDIO ||--o{ DIM_RODOVIAS_FEDERAIS : "fk_trecho_rodoviario"

    FATO_FOCOS_INCENDIO {
        string data_hora PK "__time"
        string fk_bioma
        string fk_satelite_sensor
        string fk_municipio FK
        string fk_hospital_proximo FK
        string fk_terra_indigena FK
        string fk_linha_transmissao FK
        string fk_subestacao FK
        string fk_sistema_isolado FK
        string fk_trecho_rodoviario FK
        float latitude
        float longitude
        float potencia_radiativa_fogo
        float risco_fogo_inpe
        float dias_sem_chuva
        float precipitacao_mm
        float distancia_linha_km
        float distancia_hospital_km
        float distancia_terra_indigena_km
        float distancia_rodovia_km
    }

    FATO_EVENTOS_INCENDIO {
        string fire_event_id PK
        string data_inicio PK "__time"
        string data_fim
        string fk_municipio_principal FK
        string fk_hospital FK
        string fk_terra_indigena FK
        string fk_linha_transmissao FK
        string fk_subestacao FK
        string fk_sistema_isolado FK
        string fk_trecho_rodoviario FK
        float latitude_centroide
        float longitude_centroide
        string path_json
        int total_focos
        float duracao_dias
        float area_evento_km2
        float soma_frp
        float max_frp
        float max_risco_fogo
        float indice_ameaca_linha
        float indice_pressao_saude
        float indice_pressao_terra_indigena
    }

    DIM_MUNICIPIOS {
        string codigo_ibge PK
        string municipios_nome
        string estado_sigla
        string regiao_brasil
        float latitude
        float longitude
        string path_json
    }

    DIM_HOSPITAIS {
        string codigo_cnes PK
        string nome_hospital
        string tipo_unidade
        string tipo_unidade_critica
        string funciona_24h
        string codigo_ibge FK
    }

    DIM_TERRAS_INDIGENAS {
        string codigo_ti PK
        string nome_terra_indigena
        string etnia
        string estado_sigla
        float area_hectares
        string path_json
    }

    DIM_LINHAS_TRANSMISSAO {
        string id_linha_transmissao PK
        string nome_linha
        float tensao_kv
        string classe_tensao
        float extensao_km
        string path_json
    }

    DIM_SUBESTACOES {
        string id_subestacao PK
        string nome_subestacao
        float capacidade_mw
        float betweenness_score_norm
        string risco_cascata
        string codigo_ibge FK
    }

    DIM_SISTEMAS_ISOLADOS {
        string id_sistema_isolado PK
        string nome_sistema_isolado
        string estado_sigla
        string concessionaria
    }

    DIM_RODOVIAS_FEDERAIS {
        string id_trecho_rodoviario PK
        string codigo_rodovia
        string criticidade_rodovia
        string jurisdicao
        float extensao_km
    }
```

---

## 4. Testabilidade e Isolamento Arquitetural

Com o desacoplamento via contratos e protocolos em `src/core/contracts/contracts.py`:
1. **Testes Unitários Rápidos**: Testes em `src/silver/tests` e `src/gold/tests` utilizam implementações simuladas de `SpatialEngineProtocol` e `StreamPublisherBase`, dispensando dependência de conexões de rede ativas com Apache Kafka ou subida de serviços Docker durante testes de CI/CD.
2. **Validação de Invariantes em Tempo de Execução**: `ExecutablePipelineStep` impede a instanciação de etapas sem a implementação do método de negócio `_run()`, enquanto contratos Pydantic barram valores `NaN` ou `Inf` antes do despacho para as portas de mensageria.
3. **Compatibilidade com o Ecossistema `uv`**: Toda a suíte de testes é executada com alta velocidade através do comando padrão do repositório:
   ```bash
   uv run pytest src/silver/tests src/gold/tests
   ```
