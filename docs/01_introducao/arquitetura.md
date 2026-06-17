# Fundamentação e Topologia Arquitetural

A estrutura do projeto baseia-se nos pilares de DataOps e Big Data, promovendo o encapsulamento do ciclo de vida dos dados desde a aquisição primária até a visualização analítica, com extrema latência reduzida e alta disponibilidade.

## 1. Justificativa Científica e Problema de Pesquisa
O monitoramento contínuo de focos de calor identificados por satélites (e.g., MODIS, VIIRS) sobre o território nacional exige capacidade de ingestão em larga escala e cálculos analíticos complexos on-the-fly. A ausência de um framework que correlacione, em tempo real, estes vetores térmicos com malhas de infraestrutura sensível (como linhas de transmissão de ultra-alta tensão ou perímetros de proteção indígena) compromete o tempo de resposta e a formulação de políticas públicas preditivas. 

## 2. Visão Sistêmica da Arquitetura
A plataforma foi desenhada em uma arquitetura Lambda/Kappa híbrida adaptada, caracterizada pela separação entre as camadas de *Batch* (para atualização de características topográficas estáticas) e *Streaming* (para análise de variáveis estocásticas).

Os cinco macrocomponentes da topologia consistem em:
- **Camada de Produtores (Data Acquisition)**: Módulos desenvolvidos em Python responsáveis pela captação dos vetores de telemetria orbital junto às bases governamentais (INPE, ONS, CNES, IBGE).
- **Camada de Processamento de Fluxos (Stream Processor)**: Intercepta o sinal bruto do produtor, calculando tensores de distâncias euclidianas e aplicando modelos heurísticos de pressão ambiental e risco em tempo real antes da serialização.
- **Message Broker (Apache Kafka)**: Provê durabilidade, particionamento geométrico e tolerância a falhas na transferência de *payloads* em altíssimas taxas de vazão (throughput).
- **Data Store Analítico (Apache Druid)**: Banco de dados OLAP (Online Analytical Processing) baseado em séries temporais (Time-Series Database), que emprega estruturas de árvore (Bitmaps) para varredura e agregação de terabytes de telemetrias em subsegundos.
- **Camada de Apresentação Viso-Analítica (Apache Superset)**: Motor de exploração acoplado diretamente ao Apache Druid, especializado em renderização geométrica avançada (Scatterplots, Hexbins, Polígonos GeoJSON).
