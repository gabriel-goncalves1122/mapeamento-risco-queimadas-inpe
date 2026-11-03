# Dicionário de Dados - Camada Bronze (Raw Ingestion)

Este documento descreve as estruturas de dados, nomes de atributos, tipos nativos e formatos brutos de todos os dados adquiridos e armazenados na **Camada Bronze**.

Na Bronze, os dados são **representações literais da fonte**, preservando a nomenclatura original dos provedores antes de qualquer higienização, reprojeção para SIRGAS 2000 (`EPSG:5880`) ou cálculo espacial efetuado pela Camada Silver.

---

## 1. Infraestrutura do Setor Elétrico (ANEEL / SIGEL MapServer)

### 1.1 Linhas de Transmissão (`linhas_transmissao_ons.geojson`)
- **Origem:** ANEEL MapServer Layer 1.
- **Formato:** GeoJSON (`FeatureCollection`).
- **Geometria Nativa:** `LineString` ou `MultiLineString` (WGS84 / `EPSG:4326`).

| Campo Bruto (Property) | Tipo | Nullable | Descrição Original do Provedor |
|---|---|:---:|---|
| `OBJECTID` | Integer | Não | Identificador primário numérico interno do ArcGIS Server. |
| `COD_LINHA` | String | Sim | Código operacional alfanumérico da linha de transmissão (ONS). |
| `NOMELINHA` | String | Não | Denominação oficial da linha (ex: `LT 500 kV Xingu / Estreito`). |
| `TENS_KV` | Float | Sim | Nível nominal de tensão operacional em quilovolts (ex: `230.0`, `500.0`, `800.0`). |
| `CONCESSION` | String | Sim | Razão social ou sigla da concessionária titular da concessão (ex: `FURNAS`, `CHESF`, `TAESA`). |
| `EXTENSAO` | Float | Sim | Comprimento linear do traçado em quilômetros (`km`). |
| `DATA_ENTRADA` | String | Sim | Data formal de início da operação comercial do ativo. |
| `geometry` | Geometry | Não | Vetor de coordenadas geográficas `[lon, lat]` em `EPSG:4326`. |

---

### 1.2 Subestações de Energia (`subestacoes_ons.geojson`)
- **Origem:** ANEEL MapServer Layer 3.
- **Formato:** GeoJSON (`FeatureCollection`).
- **Geometria Nativa:** `Point` (WGS84 / `EPSG:4326`).

| Campo Bruto (Property) | Tipo | Nullable | Descrição Original do Provedor |
|---|---|:---:|---|
| `OBJECTID` | Integer | Não | Identificador primário do ArcGIS Server. |
| `COD_SUB` | String | Sim | Código mnemônico oficial da subestação no ONS (ex: `SE-EST`, `SE-XNG`). |
| `NOMESUB` | String | Não | Nome por extenso da subestação de energia elétrica. |
| `TENS_KV` | Float | Sim | Tensão máxima de transformação/barramento em quilovolts. |
| `CONCESSION` | String | Sim | Concessionária de transmissão responsável pela subestação. |
| `MUNICIPIO` | String | Sim | Nome descritivo do município de localização conforme cadastro ANEEL. |
| `UF` | String | Sim | Sigla do Estado da Federação (ex: `SP`, `MG`, `PA`). |
| `geometry` | Geometry | Não | Ponto geográfico `[lon, lat]` em `EPSG:4326`. |

---

### 1.3 Sistemas Elétricos Isolados (`sistemas_isolados_ons.geojson`)
- **Origem:** ANEEL MapServer Layer 5.
- **Formato:** GeoJSON (`FeatureCollection`).
- **Geometria Nativa:** `Point` (WGS84 / `EPSG:4326`).

| Campo Bruto (Property) | Tipo | Nullable | Descrição Original do Provedor |
|---|---|:---:|---|
| `OBJECTID` | Integer | Não | Identificador primário do ArcGIS Server. |
| `COD_SIST` | String | Sim | Identificador cadastral da localidade isolada. |
| `NOMELOCAL` | String | Não | Nome da comunidade, vila ou município não conectado ao SIN. |
| `CONCESSION` | String | Sim | Concessionária de distribuição local (ex: `EQUATORIAL`, `ENERGISA`). |
| `POPULACAO` | Integer | Sim | Estimativa de habitantes atendidos pela geração térmica local. |
| `geometry` | Geometry | Não | Ponto geográfico `[lon, lat]` em `EPSG:4326`. |

---

## 2. Detecções de Focos de Queimada (INPE / BDQueimadas)

- **Origem:** Instituto Nacional de Pesquisas Espaciais (INPE).
- **Formato:** Arquivo tabular CSV (`focos_*.csv`).
- **Codificação:** UTF-8. Separador: Vírgula (`,`).

| Coluna Bruta | Tipo | Nullable | Descrição da Variável Meteorológica / Orbital |
|---|---|:---:|---|
| `lat` | Float | Não | Latitude decimal do baricentro do pixel quente (WGS84). |
| `lon` | Float | Não | Longitude decimal do baricentro do pixel quente (WGS84). |
| `data_hora_gmt` | String | Não | Data e horário UTC no padrão ISO `YYYY-MM-DD HH:MM:SS`. |
| `satelite` | String | Não | Identificação do satélite sensor (ex: `AQUA_M-T`, `NOAA-20`, `TERRA_M-T`). |
| `pais` | String | Não | Nome do país (`Brasil`). |
| `estado` | String | Não | Nome por extenso do estado de detecção informado pelo INPE. |
| `municipio` | String | Não | Nome por extenso do município segundo referência geográfica do INPE. |
| `bioma` | String | Não | Bioma de ocorrência (ex: `Cerrado`, `Amazonia`, `Mata Atlantica`, `Pantanal`). |
| `dias_sem_chuva` | Float | Sim | Número estimado de dias consecutivos sem precipitação hídrica no pixel. |
| `precipitacao` | Float | Sim | Volume de chuva acumulada recente em milímetros (`mm`). |
| `risco_fogo` | Float | Sim | Índice contínuo de risco de fogo calculado pelo INPE (escala de 0.0 a 1.0). |
| `frp` | Float | Sim | *Fire Radiative Power* em Megawatts (`MW`). Mede a energia térmica liberada instantaneamente pela combustão. |

---

## 3. Terras Indígenas (FUNAI)

- **Origem:** Geoportal da Fundação Nacional dos Povos Indígenas.
- **Formato:** Vetor GeoJSON (`mapa_terras_indigenas.geojson`) e Tabela CSV (`tis_poligonais.csv`).
- **Geometria Nativa:** `Polygon` ou `MultiPolygon` (WGS84 / `EPSG:4326`).

| Campo Bruto | Tipo | Nullable | Descrição Cadastral e Jurídica FUNAI |
|---|---|:---:|---|
| `cod_ti` / `codigo_ti` | String/Int | Não | Código oficial numérico de identificação da Terra Indígena perante a FUNAI. |
| `nome_ti` | String | Não | Nome oficial demarcado da Terra Indígena (ex: `Parque do Araguaia`, `Yanomami`). |
| `etnia_predominante`| String | Sim | Povos originários habitantes (ex: `Javaé`, `Karajá`, `Avá-Canoeiro`, `Kayapó`). |
| `fase_ti` | String | Não | Situação jurídica formal (ex: `Regularizada`, `Homologada`, `Declarada`, `Delimitada`). |
| `superficie_ha` | Float | Sim | Extensão territorial oficial calculada em hectares (`ha`). |
| `geometry` | Geometry | Não | Polígono delimitador da reserva indígena. |

---

## 4. Malha Municipal do Brasil (IBGE)

- **Origem:** Instituto Brasileiro de Geografia e Estatística (Malha Municipal 1:250.000).
- **Formato:** GeoJSON (`municipios_br.geojson`).
- **Geometria Nativa:** `Polygon` ou `MultiPolygon` (SIRGAS 2000 Geográfico / `EPSG:4674`).

| Campo Bruto (Property) | Tipo | Nullable | Descrição Geopolítica IBGE |
|---|---|:---:|---|
| `CD_MUN` | String | Não | Código territorial oficial de 7 dígitos do município (Chave Primária Nacional). |
| `NM_MUN` | String | Não | Nome formal do município (ex: `Formoso do Araguaia`, `São Paulo`). |
| `SIGLA_UF` | String | Não | Sigla da Unidade Federativa de pertencimento (`TO`, `SP`, `MG`, etc.). |
| `AREA_KM2` | Float | Sim | Área territorial calculada oficialmente pelo IBGE em quilômetros quadrados. |
| `geometry` | Geometry | Não | Polígono ou multipolígono dos limites municipais. |

---

## 5. Malha Rodoviária Nacional (DNIT - SNV)

- **Origem:** Departamento Nacional de Infraestrutura de Transportes.
- **Formato:** GeoJSON (`rodovias_federais.geojson`).
- **Geometria Nativa:** `LineString` ou `MultiLineString` (WGS84 / `EPSG:4326`).

| Campo Bruto (Property) | Tipo | Nullable | Descrição do Sistema Nacional de Viação |
|---|---|:---:|---|
| `id_trecho` | String/Int | Não | Identificador determinístico do segmento da malha rodoviária. |
| `vl_br` | String | Não | Código de designação da rodovia federal (ex: `BR-116`, `BR-153`, `BR-242`). |
| `sg_uf` | String | Não | Sigla da Unidade Federativa onde o trecho rodoviário está implantado. |
| `vl_km_inicial` | Float | Sim | Quilômetro inicial do trecho rodoviário demarcado. |
| `vl_km_final` | Float | Sim | Quilômetro final do trecho rodoviário demarcado. |
| `geometry` | Geometry | Não | Traçado linear do trecho rodoviário. |

---

## 6. Estabelecimentos e Capacidade Hospitalar (DATASUS / CNES)

- **Origem:** Ministério da Saúde / Cadastro Nacional de Estabelecimentos de Saúde.
- **Formato:** Arquivos CSV tabulares em `src/bronze/data/datasus/cnes_aux/`.
- **Codificação:** `latin-1`. Separador: Ponto e vírgula (`;`).

### 6.1 `tbEstabelecimento*.csv` (Cadastro)
| Coluna Bruta | Tipo | Nullable | Descrição Cadastral CNES |
|---|---|:---:|---|
| `CO_UNIDADE` | String | Não | Código nacional único de 7 dígitos do estabelecimento de saúde (CNES). |
| `NO_FANTASIA` | String | Não | Nome de fachada comercial do hospital ou pronto-atendimento. |
| `CO_MUNICIPIO_GESTOR` | String | Não | Código IBGE (6 dígitos na fonte, normalizado para 7 na Silver) do município sede. |
| `TP_UNIDADE` | String | Não | Código numérico da tipologia da unidade de saúde. |
| `LATITUDE_ESTABELECIMENTO` | Float | Sim | Coordenada Y de latitude do hospital. |
| `LONGITUDE_ESTABELECIMENTO`| Float | Sim | Coordenada X de longitude do hospital. |

### 6.2 `tbLeito*.csv` (Capacidade de Internação)
| Coluna Bruta | Tipo | Nullable | Descrição dos Leitos |
|---|---|:---:|---|
| `CO_UNIDADE` | String | Não | Código CNES correspondente. |
| `TP_LEITO` | String | Não | Categoria do leito (clínico, cirúrgico, complementar). |
| `QT_EXIST` | Integer | Não | Quantidade física de leitos existentes instalados. |
| `QT_CONTR` | Integer | Sim | Quantidade de leitos conveniados ao Sistema Único de Saúde (SUS). |

### 6.3 `tbTipoUnidade*.csv` (Classificação)
| Coluna Bruta | Tipo | Nullable | Descrição da Tipologia |
|---|---|:---:|---|
| `TP_UNIDADE` | String | Não | Chave primária da tipologia. |
| `DS_TIPO_UNIDADE` | String | Não | Descrição textual (ex: `HOSPITAL GERAL`, `HOSPITAL ESPECIALIZADO`, `PRONTO ATENDIMENTO`). |
