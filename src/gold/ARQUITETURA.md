# Arquitetura e Engenharia de Software - Camada Gold (Ouro)

Este documento aprofunda as diretrizes arquiteturais, o design orientado a objetos (POO), os princípios SOLID e as estratégias de micro-batching e streaming implementadas na **Camada Gold**.

A Camada Gold consolida a inteligência analítica do CCO-DataOps. Ao contrário da Camada Silver (focada em limpeza, padronização e cruzamentos geoespaciais em árvores R-Tree), a Gold é **orientada a produtos de dados, teoria dos grafos e modelos preditivos/agregados**.

---

## 1. Estrutura Modular da Camada

A estrutura de código respeita estritamente o princípio de responsabilidade única (1 Classe = 1 Arquivo em `snake_case`):

```text
src/gold/
├── README.md                      # Visão geral da Camada Gold e guia operacional
├── ARQUITETURA.md                 # Este documento de engenharia e padrões
├── DICIONARIO_DADOS.md            # Esquemas físicos das Tabelas Fato
├── data/
│   ├── fatos/                     # Tabelas Fato resultantes das agregações (ex: stdbscan)
│   └── results/                   # Saídas de benchmarks de capacidade
├── src/
│   ├── science/                   # Inteligência Analítica e Ciência de Redes
│   │   ├── dbscan/                # Clusterização Espaço-Temporal ST-DBSCAN
│   │   │   ├── evento_config.py          # Dataclass imutável de hiperparâmetros (SRP)
│   │   │   ├── event_geometry_builder.py # Cálculo de Convex Hull e centroides (SRP)
│   │   │   └── eventizador.py            # Executável do algoritmo ST-DBSCAN (LSP)
│   │   └── networkx/              # Ciência de Redes e Grafos do Setor Elétrico
│   │       └── network_builder.py        # Modelo de Centralidade SIN (ExecutablePipelineStep)
│   └── streaming/                 # Ingestão e Última Milha para o Data Lakehouse
│       ├── kafka_client.py               # KafkaEventProducer implementando StreamPublisherBase (DIP)
│       ├── streaming_audit_logger.py     # Registro e auditoria isolada de mensagens (SRP)
│       ├── produtor_focos.py             # Publicador da tabela fato atômica
│       └── produtor_eventos.py           # Publicador da tabela fato agregada
└── tests/                         # Suíte de testes unitários e de contratos
```

---

## 2. Princípios SOLID Aplicados na Camada Gold

### 2.1 Single Responsibility Principle (SRP)
- **ST-DBSCAN Decomposto**:
  - `EventoConfig`: Dataclass pura que armazena e valida os hiperparâmetros espaciais e temporais ($\varepsilon_{km} = 50$, $\varepsilon_{dias} = 1.0$, $min\_samples = 3$).
  - `EventGeometryBuilder`: Módulo de geometria pura que calcula envoltória convexa (*Convex Hull*), baricentro ponderado e formatação de polígonos `path_json`.
  - `EventizadorIncendios`: Orquestrador analítico que executa o DBSCAN multidimensional via Scikit-Learn e enriquece os clusters com métricas agregadas.
- **Auditoria Desacoplada**:
  - `StreamingAuditLogger`: Centraliza métricas de taxa de envio, volumetria e falhas, isolando o logging da lógica de rede de `KafkaEventProducer`.

### 2.2 Liskov Substitution Principle (LSP)
- As classes `EventizadorIncendios` e `SINNetworkCentralityModel` herdam de `ExecutablePipelineStep`, garantindo que orquestradores (como o Apache Dagster) possam executá-las de forma homogênea via `step.execute()`, usufruindo da telemetria uniforme do *Template Method*.

### 2.3 Dependency Inversion Principle (DIP)
- Os produtores de streaming (`ProdutorFocosGold` e `ProdutorEventosGold`) não criam diretamente instâncias de conexões com o Kafka ou motores de disco. Em vez disso, recebem abstrações via injeção de dependência:
  - `StreamPublisherBase`: Permite o uso de clientes mock em memória para testes unitários ultrarrápidos em CI/CD sem dependência de um cluster Kafka ativo.
  - `SpatialEngineProtocol`: Permite simular consultas de infraestrutura sem carregar centenas de megabytes de GeoDataFrames do disco.

---

## 3. Gestão de Recursos via Context Manager

O driver de publicação `KafkaEventProducer` estende `StreamPublisherBase`, implementando o protocolo de gerenciamento de contexto (`__enter__` e `__exit__`). Isso assegura que:
- O buffer local de mensagens seja obrigatoriamente descarregado (`flush()`).
- As conexões TCP/sockets com o cluster Kafka sejam encerradas deterministicamente, mesmo diante de exceções ou cancelamento do processo:

```python
with KafkaEventProducer(broker="localhost:29092") as producer:
    producer.enviar(topico="focos-incendio", payload=payload_dict)
# O socket é fechado e o buffer esvaziado automaticamente ao sair do bloco
```

---

## 4. Governança do Modelo Snowflake nas Tabelas Fato

A Camada Gold é terminantemente proibida de persistir colunas puramente textuais ou redundantes no payload de streaming (`nome_municipio`, `sigla_uf`, `classe_ameaca`).

As Tabelas Fato contêm **exclusivamente**:
1. **Chaves Temporais:** `data_hora` ou `data_inicio` / `data_fim` (mapeadas para `__time` no Apache Druid).
2. **Chaves Estrangeiras (FKs):** `fk_municipio`, `fk_linha_transmissao`, `fk_subestacao`, `fk_terra_indigena`, `fk_trecho_rodoviario`, `fk_hospital_proximo`, `fk_sistema_isolado`.
3. **Métricas Físicas e Contínuas:** Coordenadas (`lat`, `lon`), FRP (`MW`), Risco de Fogo (`0.0 a 1.0`), distâncias em quilômetros (`EPSG:5880`), áreas em $km^2$ e índices de severidade.
4. **Geometrias Serializadas:** Polígonos de envoltória em formato técnico `path_json`.

> No Apache Druid, todas as descrições textuais são resolvidas em tempo de execução via **Lookups** indexados em memória, otimizando drasticamente a banda de rede e a velocidade de compressão LZ4 nos segmentos do banco colunar.
