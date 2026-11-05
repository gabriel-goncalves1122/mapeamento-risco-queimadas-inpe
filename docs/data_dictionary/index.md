# Índice Geral de Dicionários de Dados e Especificações de Fontes

Este documento centraliza o acesso aos dicionários de dados físicos e catálogos de APIs das camadas **Bronze**, **Silver** e **Gold** da arquitetura Medallion. Cada dicionário está co-localizado junto ao respectivo pacote de código-fonte e reflete os esquemas reais verificados contra os arquivos gerados e os contratos Pydantic de produção.

---

## 1. Camada Bronze — Insumos Brutos e APIs Externas (`src/bronze/`)

Especifica os endpoints, protocolos HTTP, limites de paginação, formatos de arquivo e esquemas originais não mutados extraídos dos 6 provedores governamentais (INPE, ANEEL/ONS, FUNAI, IBGE, DNIT e CNES/DATASUS):

- **[Catálogo de Fontes, APIs e Parâmetros (`src/bronze/FONTES_E_APIS.md`)](../../src/bronze/FONTES_E_APIS.md)**:
  - Parâmetros HTTP GET da API ArcGIS REST da ANEEL (`where=1=1`, `outSR=4326`, `resultOffset`, `resultRecordCount=1000`), diretórios ZIP do INPE/COIDS, WFS Geoserver da FUNAI e shapefiles do IBGE/DNIT.
  - Particularidades operacionais dos dados brutos: valores sentinela `-999` do INPE, notação decimal `13P8` e tabelas HTML embutidas (`PopupInfo`) na ANEEL, e cabeçalhos legados Oracle no CSV do CNES.
- **[Dicionário de Dados Brutos (`src/bronze/DICIONARIO_DADOS.md`)](../../src/bronze/DICIONARIO_DADOS.md)**:
  - Esquema completo das tabelas e feições brutas em `src/bronze/data/` antes das etapas de sanitização.

---

## 2. Camada Silver — Dimensões Conformadas e Lookups (`src/silver/`)

Especifica as 7 tabelas de dimensão do modelo Snowflake persistidas em `src/silver/data/dimensions/`, enriquecidas espacialmente em projeção policônica SIRGAS 2000 (`EPSG:5880`) e carregadas como *Lookups* em memória no Apache Druid:

- **[Dicionário de Dados das 7 Dimensões (`src/silver/DICIONARIO_DADOS.md`)](../../src/silver/DICIONARIO_DADOS.md)**:
  - Colunas, tipos, chaves primárias, chaves estrangeiras e contagem de registros de `dim_municipios_coordenadas.csv`, `dim_terras_indigenas.csv`, `dim_rodovias_federais.csv`, `dim_ons_linhas_transmissao.csv`, `dim_ons_subestacoes.csv`, `dim_ons_sistemas_isolados.csv` e `dim_hospitais_cnes.csv`.
- **[Catálogo dos 23 Lookups URI do Apache Druid (`src/silver/validators/README.md`)](../../src/silver/validators/README.md)**:
  - Mapeamento `keyColumn -> valueColumn` registrado pelo `DruidLookupRegistrar` no namespace `cachedNamespace` do Apache Druid Coordinator.

---

## 3. Camada Gold — Tabelas Fato e Payloads de Streaming (`src/gold/`)

Especifica os esquemas estritos das tabelas fato publicadas no Apache Kafka e ingeridas no Apache Druid, governadas pelos contratos Pydantic [`FocoFatoPayload`](../../src/core/domain/foco_fato_payload.py) e [`EventoFatoPayload`](../../src/core/domain/evento_fato_payload.py):

- **[Dicionário de Dados das Tabelas Fato (`src/gold/DICIONARIO_DADOS.md`)](../../src/gold/DICIONARIO_DADOS.md)**:
  - **`FATO_FOCOS_INCENDIO`** (`29` colunas, tópico `streaming_focos_incendio`, datasource `fato_focos_incendio`): registro observacional atômico enriquecido com 9 FKs, coordenadas validadas e 6 distâncias euclidianas em quilômetros.
  - **`FATO_EVENTOS_INCENDIO`** (`52` atributos, tópico `streaming_eventos_incendio`, datasource `fato_eventos_incendio`): macroevento espaço-temporal clusterizado via ST-DBSCAN com polígono `path_json`, listas multivaloradas de territórios interceptados e 6 índices sintéticos de ameaça/pressão.
