# Camada Gold (Ouro) - CCO DataOps

Bem-vindo à camada Gold da arquitetura Medallion. Esta camada é o destino final dos dados no pipeline antes de serem consumidos pelo Druid, Apache Superset, ou aplicações externas. 

Diferente da camada Silver (focada em limpeza, padronização atômica e cruzamentos geoespaciais básicos), a camada Gold é **orientada a produtos de dados e modelos complexos**.

## Estrutura da Camada Gold

```text
pipelines/gold/
├── src/
│   ├── science/               # Algoritmos avançados e Inteligência Analítica
│   │   ├── dbscan/            # Modelos de Machine Learning Espaço-Temporal
│   │   └── networkx/          # Ciência de Redes e Grafos de Infraestrutura
│   │
│   └── streaming/             # Ingestão e "Última Milha" para o Data Lakehouse
│       ├── kafka_client.py    
│       ├── produtor_focos.py  # Publicador da tabela atômica
│       └── produtor_eventos.py# Publicador da tabela agregada
│
├── data/
│   ├── fatos/                 # Tabelas Fato resultantes das agregações (ex: stdbscan)
│   └── results/               # Saídas de benchmark de ingestão
└── tests/                     # Testes Unitários e de Contrato
```

## Diretrizes da Camada Gold

1. **Modelos de Ciência de Dados (`src/science`)**:
   - Qualquer algoritmo que exija iteração de estado, grafos, agrupamentos (clustering) ou predições reside aqui.
   - O `eventizador.py` (DBSCAN) é um modelo de ML que agrupa os focos atômicos da Silver em eventos de maior escala e duração.
   - O `network_builder.py` (NetworkX) cria a topologia do Sistema Interligado Nacional para medir grau, centralidade e cascatas.

2. **Última Milha de Streaming (`src/streaming`)**:
   - Estes produtores são os "clientes Kafka" que encapsulam a lógica de enviar o dado enriquecido para a rede.
   - Não devem conter lógica de limpeza ou padronização de dados brutos (isso pertence à Silver).

3. **Contratos e Domínio Compartilhado**:
   - Os payloads Pydantic (`FocoFatoPayload`, `EventoFatoPayload`) residem globalmente em `config/domain/models.py`, pois representam o contrato que transita entre todas as camadas até o Druid.

4. **Tabelas Fatos**:
   - A Gold gera (ou consolida) as Fatos que respondem às perguntas de negócio. 
   - A persistência efêmera ou cache de ML para essas Fatos vai para `data/fatos/`.
