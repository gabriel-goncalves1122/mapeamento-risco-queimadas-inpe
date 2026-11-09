# Especificação Técnica: Fontes de Dados, APIs e Particularidades Operacionais (`src/bronze/`)

> **Trilha Modular — Etapa 03 de 18 (Ciclo 1.2 — Fontes Governamentais e APIs (`src/bronze/`))**: [Anterior: Ciclo 1.1 — Hub da Camada Bronze e Extratores (`src/bronze/`)](README.md) | [Portal Geral (`docs/README.md`)](../../docs/README.md) | [Próximo: Ciclo 1.3 — Dicionário de Dados Brutos (`src/bronze/`)](DICIONARIO_DADOS.md)

Este documento especifica os protocolos de comunicação, parâmetros de requisição HTTP, mecanismos de paginação, codificações de caracteres e particularidades técnicas de cada provedor governamental e internacional integrado à Camada Bronze do SIRDA.

---

## 1. Visão Comparativa dos Provedores e Protocolos

| Provedor / Sistema | Domínio | Protocolo / Formato de Origem | Modo de Coleta | Codificação / Separador | Projeção Nativa |
|:---|:---|:---|:---|:---|:---|
| **ANEEL / ONS (SIGEL)** | Infraestrutura Elétrica (SIN) | API REST Esri ArcGIS MapServer (`GeoJSON`) | Automatizado (`AneelArcGisExtractor`) | `UTF-8` (JSON RFC 7946) | `EPSG:4326` (forçado via `outSR`) |
| **INPE (BDQueimadas / COIDS)** | Detecções Orbitais de Focos de Calor | HTTP File Server (`CSV` tabular) | Automatizado (`InpeQueimadasExtractor`) / Batch | `UTF-8`, separador `,` | `EPSG:4326` (WGS84) |
| **FUNAI (Geoportal)** | Terras Indígenas Demarcadas | Geoportal WFS / Dump Estático (`GeoJSON` + `CSV`) | Periódico (Sob atualização de portarias) | `UTF-8`, separador `,` | `EPSG:4674` / `EPSG:4326` |
| **IBGE (Malha Territorial)** | Limites Político-Administrativos Municipais | Repositório Geodésico (`GeoJSON`) | Anual (Malha Municipal 1:250.000) | `UTF-8` (JSON) | `EPSG:4674` (SIRGAS 2000) |
| **DNIT (SNV / BIT)** | Malha Rodoviária Federal | Banco de Informações de Transportes (`GeoJSON` / `Shapefile`) | Periódico (Revisões do SNV) | `UTF-8` (JSON) | `EPSG:4326` (WGS84) |
| **DATASUS (CNES)** | Estabelecimentos e Leitos de Saúde | FTP / OpenDataSUS (`CSV` relacional) | Mensal (Competência CNES `YYYYMM`) | `UTF-8` / `Latin-1`, separador `;`, quoting `"` | Coordenadas escalares (`NU_LATITUDE`, `NU_LONGITUDE`) |
| **ONS (Open Data AWS S3)** | Interrupções de Carga e Linhas SIN | HTTPS / **Apache Parquet** (`read_parquet`) | Batch / Automatizado (`OnsOpenDataExtractor`) | Binário Colunar Parquet | Tabular / Atributos Elétricos |
| **Open-Meteo** | Vento ($\vec{W}$ 10m) e Umidade (2m) | REST HTTP GET / **FlatBuffers** & JSON | Sob demanda / Automatizado (`OpenMeteoExtractor`) | Binário FlatBuffers / JSON `UTF-8` | Grade Global contínua (ERA5) |
| **INMET (PrevMet)** | Avisos de Perigo Meteorológico Ativos | REST HTTP GET / **GeoJSON** | Contínua / Webhook trigger | `UTF-8` (JSON) | `EPSG:4326` (Polígonos de Alerta) |
| **MapBiomas (GEE)** | Cobertura do Solo (LULC) & Cicatrizes Fogo | Google Earth Engine Asset / GeoTIFF | Anual / Monitor Mensal | Raster 30m (Landsat) | `EPSG:4326` |
| **NASA FIRMS** | Detecções Orbitais (VIIRS NOAA-20/21) | REST HTTP GET / **CSV** | Quase-tempo-real (NRT) | `UTF-8`, separador `,` | `EPSG:4326` (WGS84 375m) |

---

## 2. API ArcGIS REST — ANEEL / ONS (SIGEL)

O Sistema de Informações Geográficas do Setor Elétrico (SIGEL), mantido pela ANEEL em conjunto com o Operador Nacional do Sistema Elétrico (ONS), expõe a malha do Sistema Interligado Nacional por meio de um servidor Esri ArcGIS MapServer.

### 2.1 Endpoint e Identificadores de Camada (`layer_id`)

```text
GET https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmiss%C3%A3o/MapServer/{layer_id}/query
```

| `layer_id` | Nome da Camada no Servidor | Tipo Geométrico | Arquivo de Saída na Bronze | Volume de Referência |
|:---:|:---|:---:|:---|:---:|
| `1` | Linhas de Transmissão | `LineString` / `MultiLineString` | `src/bronze/data/aneel/linhas_transmissao_ons.geojson` | 1.817 feições |
| `3` | Subestações de Energia | `Point` | `src/bronze/data/aneel/subestacoes_ons.geojson` | 627 feições |
| `5` | Sistemas Isolados | `Point` | `src/bronze/data/aneel/sistemas_isolados_ons.geojson` | 120 feições |

### 2.2 Parâmetros de Query String (`params`)

O método `AneelArcGisExtractor.extrair_camada` envia os seguintes parâmetros em cada requisição HTTP GET:

| Parâmetro | Tipo | Valor Enviado | Comportamento no Servidor ArcGIS |
|:---|:---:|:---|:---|
| `where` | `str` | `"1=1"` | Predicado SQL avaliado pelo banco geográfico da ANEEL para selecionar 100% dos registros ativos da camada. |
| `outFields` | `str` | `"*"` | Solicita a inclusão de todas as colunas da tabela de atributos dentro do objeto `properties` de cada feição. |
| `f` | `str` | `"geojson"` | Determina a serialização de saída no padrão aberto GeoJSON (em substituição ao formato proprietário Esri JSON). |
| `resultOffset` | `int` | `0, 1000, 2000, ...` | Índice do primeiro registro a ser retornado na página atual (incrementado em blocos de `page_size`). |
| `resultRecordCount` | `int` | `1000` | Quantidade máxima de feições por página (`MaxRecordCount` configurado no MapServer da ANEEL). |
| `outSR` | `str` | `"4326"` | Instrui o motor do ArcGIS a reprojetar as coordenadas para o datum WGS84 (`EPSG:4326`) antes de transmitir o payload. |

---

## 3. Dataserver COIDS — INPE (Programa Queimadas / BDQueimadas)

As detecções de focos ativos de fogo geradas por satélites polares (`AQUA`, `TERRA`, `NOAA-20`, `NPP-375`) e geoestacionários (`GOES-16`, `GOES-19`) são distribuídas pelo Centro de Dados do Programa Queimadas (COIDS/INPE).

```text
Base URL: https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv
```

| Modo (`modo`) | Padrão de Endpoint Relativo | Formato de `data_ref` | Exemplo de Arquivo Remoto |
|:---:|:---|:---:|:---|
| `"diario"` | `/diario/Brasil/focos_diario_br_{YYYYMMDD}.csv` | `YYYYMMDD` | `focos_diario_br_20261108.csv` |
| `"mensal"` | `/mensal/Brasil/focos_mensal_br_{YYYYMM}.csv` | `YYYYMM` | `focos_mensal_br_202611.csv` |
| `"10min"` | `/10min/focos_10min_{YYYYMMDD_HHMM}.csv` | `YYYYMMDD_HHMM` | `focos_10min_20261108_1400.csv` |

---

## 4. Geoportal FUNAI — Terras Indígenas

Fornece os limites territoriais e o estágio administrativo das áreas indígenas demarcadas no Brasil.

* **URL de Referência:** `https://www.gov.br/funai/pt-br/atuacao/terras-indigenas/geoprocessamento-e-mapas`
* **Artefatos na Camada Bronze (`src/bronze/data/funai/`):**
  1. `mapa_terras_indigenas.geojson`: Malha poligonal contendo 650 feições georreferenciadas.
  2. `tis_poligonais.csv`: Catálogo estendido com 20 atributos administrativos e geometria em formato WKT (`the_geom`).

---

## 5. Malha Municipal Digital — IBGE

Base cartográfica oficial dos 5.564 municípios brasileiros utilizada para geocodificação reversa e agregação regional.

* **URL de Referência:** `https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/` e repositório derivado `geodata-br`.
* **Artefato na Camada Bronze:** `src/bronze/data/ibge/municipios_br.geojson` (5.564 feições `Polygon`/`MultiPolygon`).

---

## 6. Sistema Nacional de Viação (SNV) — DNIT

Fornece o traçado linear das rodovias federais brasileiras para avaliação de risco de interdição viária por fumaça ou fogo na faixa de domínio.

* **URL de Referência:** `https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/bit-mapas`
* **Artefato na Camada Bronze:** `src/bronze/data/dnit/mapa_rodovias_federais.geojson` (14.255 feições `LineString`).

---

## 7. Cadastro Nacional de Estabelecimentos de Saúde (CNES) — DATASUS

Base relacional oficial do Ministério da Saúde contendo o cadastro, endereço, localização geográfica e tipologia de todas as unidades de saúde do território nacional.

* **URL de Referência:** `https://cnes.datasus.gov.br/` e `ftp://ftp.datasus.gov.br/cnes/`
* **Artefatos na Camada Bronze (`src/bronze/data/datasus/cnes_aux/`):**
  1. `tbEstabelecimento202603.csv` (~288 MB, 55 colunas).
  2. `tbMunicipio202603.csv` (13 colunas).
  3. `tbTipoUnidade202603.csv` (2 colunas).

---

## 8. ONS Open Data (AWS S3 Parquet — `sa-east-1`)

Conjunto de dados abertos do Operador Nacional do Sistema Elétrico mantido sob o programa AWS Open Data. O acesso é direto e não exige credenciais.

* **Bucket:** `arn:aws:s3:::ons-aws-prod-opendata` (Região `sa-east-1`).
* **Endpoints HTTPS Diretos:**
  - Interrupção de Carga: `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/interrupcao_carga/INTERRUPCAO_CARGA.parquet` (8.395 ocorrências de 2007 a Nov/2026).
  - Linhas de Transmissão: `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.parquet` (2.346 linhas cadastradas com parâmetros elétricos de impedância $R, X, B$).
  - Disponibilidade: `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ind_disponibilidade_ft_trlt_me/IND_DISPONIBILIDADE_FT_TRLT_2026.parquet`.
* **Particularidade Técnica:** O portal CKAN (`dados.ons.org.br`) serve apenas metadados; a extensão `datastore_search` está inativa. O consumo deve ser realizado lendo o arquivo Parquet em bloco via `pyarrow` ou `duckdb.read_parquet()`.

---

## 9. Open-Meteo Weather API (Vento e Umidade Relativa)

Provedor de dados meteorológicos globais em grade contínua baseados em reanálise ERA5/ERA5-Land e modelos operacionais (GFS/ICON).

* **Endpoints:**
  - Histórico: `https://archive-api.open-meteo.com/v1/archive`
  - Previsão: `https://api.open-meteo.com/v1/forecast`
* **Parâmetros Essenciais:** `latitude`, `longitude`, `hourly=wind_speed_10m,wind_direction_10m,wind_gusts_10m,relative_humidity_2m`, `wind_speed_unit=kmh`, `timezone=America/Sao_Paulo`.
* **Particularidade Técnica:** Suporte a serialização binária *FlatBuffers* via SDK `openmeteo-requests` (reduz tráfego em 90%). Uso não comercial gratuito até 10.000 requisições/dia.

---

## 10. INMET PrevMet — Avisos Meteorológicos Ativos

Alertas geográficos oficiais emitidos pelo Instituto Nacional de Meteorologia para eventos severos em território nacional.

* **Endpoint:** `GET https://apiprevmet3.inmet.gov.br/avisos/ativos`
* **Particularidade Técnica:** Exige cabeçalho `User-Agent` de navegador válido na requisição HTTP GET para evitar bloqueio por TCP reset no servidor governamental.

---

## 11. MapBiomas — Cobertura do Solo e Frequência de Queimadas

Mapeamento de alta resolução (30 metros) baseado em imagens Landsat com classificação de uso da terra e cicatrizes de queimadas de 1985 até o presente.

* **Google Earth Engine Asset IDs:**
  - Cobertura da Terra (Coleção 11): `projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3`
  - Frequência de Fogo (Coleção 5.1): `projects/mapbiomas-public/assets/brazil/fire/collection5_1/mapbiomas_fire_collection51_fire_frequency_v1`
* **Classes de Maior Risco de Combustível:** Pastagem (código 15), Formação Campestre (12) e Formação Savânica (4).

---

## 12. NASA FIRMS API — VIIRS NOAA-20 / NOAA-21 (375m)

Sistema de detecção de calor da NASA voltado à localização de alta precisão espacial de focos ativos.

* **Endpoint:** `https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{WEST,SOUTH,EAST,NORTH}/{DAY_RANGE}/{DATE}`
* **Fontes Recomendadas:** `VIIRS_NOAA20_NRT` e `VIIRS_NOAA21_NRT` (resolução espacial de 375m).
* **Particularidade Técnica:** O satélite Suomi NPP foi descontinuado pela NASA em **02 de novembro de 2026**. O pipeline deve utilizar estritamente os satélites NOAA-20 e NOAA-21.
