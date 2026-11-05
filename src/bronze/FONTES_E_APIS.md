# Especificação Técnica: Fontes de Dados, APIs e Particularidades Operacionais (`src/bronze/`)

> **Trilha Modular — Etapa 03 de 18 (Ciclo 1.2 — Fontes Governamentais e APIs (`src/bronze/`))**: [Anterior: Ciclo 1.1 — Hub da Camada Bronze e Extratores (`src/bronze/`)](README.md) | [Portal Geral (`docs/README.md`)](../../docs/README.md) | [Próximo: Ciclo 1.3 — Dicionário de Dados Brutos (`src/bronze/`)](DICIONARIO_DADOS.md)

Este documento especifica os protocolos de comunicação, parâmetros de requisição HTTP, mecanismos de paginação, codificações de caracteres e particularidades técnicas de cada provedor governamental integrado à Camada Bronze.

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

O método [`AneelArcGisExtractor.extrair_camada`](extractors/ingestao_aneel.py) envia os seguintes parâmetros em cada requisição HTTP GET:

| Parâmetro | Tipo | Valor Enviado | Comportamento no Servidor ArcGIS |
|:---|:---:|:---|:---|
| `where` | `str` | `"1=1"` | Predicado SQL avaliado pelo banco geográfico da ANEEL para selecionar 100% dos registros ativos da camada. |
| `outFields` | `str` | `"*"` | Solicita a inclusão de todas as colunas da tabela de atributos dentro do objeto `properties` de cada feição. |
| `f` | `str` | `"geojson"` | Determina a serialização de saída no padrão aberto GeoJSON (em substituição ao formato proprietário Esri JSON). |
| `resultOffset` | `int` | `0, 1000, 2000, ...` | Índice do primeiro registro a ser retornado na página atual (incrementado em blocos de `page_size`). |
| `resultRecordCount` | `int` | `1000` | Quantidade máxima de feições por página (`MaxRecordCount` configurado no MapServer da ANEEL). |
| `outSR` | `str` | `"4326"` | Instrui o motor do ArcGIS a reprojetar as coordenadas para o datum WGS84 (`EPSG:4326`) antes de transmitir o payload. |

### 2.3 Particularidades Técnicas e Anomalias da Fonte ANEEL

1. **Encapsulamento de Atributos em HTML (`PopupInfo`)**:
   - O MapServer do SIGEL/ANEEL foi originalmente povoado a partir de arquivos KML/KMZ. Como consequência, variáveis de engenharia (tensão nominal em kV, extensão em km, potência instalada em MW e concessionária) **não estão expostas como campos JSON tipados**, mas concatenadas em uma string HTML dentro da propriedade `PopupInfo` (ex.: `<b>Tensão: </b>230 Kv<br/><b>Extensão: </b>72,96 Km`).
   - O parsing desses atributos ocorre na Camada Silver por meio da função [`extrair_popup_valor`](../silver/utils/string_helpers.py).
2. **Grafia Não-Padrão de Casas Decimais (`"13P8"`)**:
   - Nos campos `Name` e `PopupInfo` de linhas e subestações, tensões fracionárias como `13,8 kV` ou `34,5 kV` são frequentemente grafadas com a letra `P` no lugar do separador decimal (ex.: `"13P8 KV"`). Os extratores numéricos da Camada Silver aplicam a substituição via expressão regular `re.sub(r"(\d+)P(\d+)", r"\1.\2", t)` antes da conversão para `float`.
3. **Vértices Duplicados e Ciclos Periódicos em `LineString`**:
   - A conversão interna KML $\rightarrow$ GeoJSON da ANEEL duplica sequências inteiras de coordenadas (ida e volta sobre o mesmo traçado). A função [`GeometryService.remover_repeticoes_periodicas`](../silver/utils/geo_helpers.py) detecta e elimina esses ciclos na Camada Silver.
4. **Controle de Throttling (`rate_limit_s`)**:
   - Requisições sequenciais sem intervalo podem acionar bloqueios temporários de firewall ou respostas HTTP 429/503. O extrator aplica `time.sleep(1.0)` entre páginas consecutivas.

---

## 3. Dataserver COIDS — INPE (Programa Queimadas / BDQueimadas)

As detecções de focos ativos de fogo geradas por satélites polares (`AQUA`, `TERRA`, `NOAA-20`, `NPP-375`) e geoestacionários (`GOES-16`) são distribuídas pelo Centro de Dados do Programa Queimadas (COIDS/INPE).

### 3.1 Estrutura de URLs do Dataserver

 implementada em [`InpeQueimadasExtractor`](extractors/inpe_queimadas_extractor.py):

```text
Base URL: https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv
```

| Modo (`modo`) | Padrão de Endpoint Relativo | Formato de `data_ref` | Exemplo de Arquivo Remoto |
|:---:|:---|:---:|:---|
| `"diario"` | `/diario/Brasil/focos_diario_br_{YYYYMMDD}.csv` | `YYYYMMDD` | `focos_diario_br_20260818.csv` |
| `"mensal"` | `/mensal/Brasil/focos_mensal_br_{YYYYMM}.csv` | `YYYYMM` | `focos_mensal_br_202608.csv` |
| `"10min"` | `/10min/focos_10min_{YYYYMMDD_HHMM}.csv` | `YYYYMMDD_HHMM` | `focos_10min_20260818_1400.csv` |

### 3.2 Parâmetros de Transporte e Particularidades do INPE

1. **Streaming HTTP em Blocos (`chunk_size = 65536`)**:
   - A requisição utiliza `requests.get(url, stream=True, timeout=30.0)`, lendo o corpo da resposta em blocos de 64 KB via `resp.iter_content(chunk_size=65536)`.
2. **Valores Sentinela (`-999` e `<= -900`)**:
   - Quando um sensor orbital (como o GOES-16) não consegue estimar a Potência Radiativa do Fogo (`FRP`) ou quando a grade meteorológica não dispõe de leitura para `DiaSemChuva` / `RiscoFogo`, o INPE preenche o campo numérico com `-999.0` ou deixa a célula vazia.
   - As funções [`limpar_valor_numerico`](../silver/utils/cleaners.py) e [`limpar_valor_numerico_nullable`](../silver/utils/cleaners.py) interceptam qualquer valor $\le -900$, convertendo-o respectivamente para `0.0` ou `None`.
3. **Divergência Nominal de Municípios**:
   - O atributo `Municipio` reportado no CSV do INPE pode divergir da grafia oficial atualizada do IBGE ou apresentar variações de acentuação. Por esse motivo, o pipeline mantém tanto a chave nominal normalizada (`fk_municipio`) quanto a chave obtida por geocodificação reversa ponto-em-polígono sobre a malha oficial do IBGE (`fk_municipio_espacial`).

---

## 4. Geoportal FUNAI — Terras Indígenas

Fornece os limites territoriais e o estágio administrativo das áreas indígenas demarcadas no Brasil.

* **URL de Referência:** `https://www.gov.br/funai/pt-br/atuacao/terras-indigenas/geoprocessamento-e-mapas`
* **Artefatos na Camada Bronze (`src/bronze/data/funai/`):**
  1. `mapa_terras_indigenas.geojson`: Malha poligonal contendo 650 feições georreferenciadas.
  2. `tis_poligonais.csv`: Catálogo estendido com 20 atributos administrativos e geometria em formato WKT (`the_geom`).
* **Particularidades Técnicas:**
  - **Fragmentação de Reservas em Múltiplas Feições**: Uma mesma Terra Indígena (mesmo `codigo_ti`) pode aparecer dividida em múltiplos polígonos no GeoJSON. Na Camada Silver, os polígonos de mesmo `codigo_ti` são consolidados via `shapely.ops.unary_union`.
  - **Atributo `municipios` / `estados` Multivalorado**: Terras indígenas extensas abrangem múltiplos municípios concatenados por vírgula (ex.: `"Formoso do Araguaia, Lagoa da Confusão, Pium"`). O relacionamento exato com municípios na modelagem analítica é resolvido por intersecção geométrica espacial (`STRtree`), e não por split textual.

---

## 5. Malha Municipal Digital — IBGE

Base cartográfica oficial dos 5.564 municípios brasileiros utilizada para geocodificação reversa e agregação regional.

* **URL de Referência:** `https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/` e repositório derivado `geodata-br`.
* **Artefato na Camada Bronze:** `src/bronze/data/ibge/municipios_br.geojson` (5.564 feições `Polygon`/`MultiPolygon`).
* **Particularidades Técnicas:**
  - **Omissão da UF nas Propriedades Nativas**: O arquivo `municipios_br.geojson` contém apenas os atributos `id` (código IBGE de 7 dígitos, ex.: `"1100015"`), `name` e `description`, sem coluna explícita de UF. O ETL da Camada Silver deriva a sigla da Unidade Federativa a partir dos **2 primeiros dígitos** do código IBGE (ex.: `11` $\rightarrow$ `RO`, `17` $\rightarrow$ `TO`, `31` $\rightarrow$ `MG`).
  - **Compatibilidade de Chaves 6 vs. 7 Dígitos**: Enquanto o IBGE adota 7 dígitos (incluindo dígito verificador), o Ministério da Saúde (DATASUS/CNES) indexa municípios com apenas 6 dígitos. A dimensão Silver armazena o código normalizado de 6 dígitos (`codigo_ibge`) para permitir junção direta com `dim_hospitais_cnes`.

---

## 6. Sistema Nacional de Viação (SNV) — DNIT

Fornece o traçado linear das rodovias federais brasileiras para avaliação de risco de interdição viária por fumaça ou fogo na faixa de domínio.

* **URL de Referência:** `https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/bit-mapas`
* **Artefato na Camada Bronze:** `src/bronze/data/dnit/mapa_rodovias_federais.geojson` (14.255 feições `LineString`).
* **Particularidades Técnicas:**
  - **Redundância Geométrica (`geometry` + `geometria_wkt`)**: Cada feição possui tanto o objeto GeoJSON `geometry` quanto a propriedade textual `geometria_wkt`, permitindo fallback caso uma geometria necessite de reconstrução via `shapely.wkt.loads`.
  - **Segmentação Quilométrica**: Uma mesma rodovia (ex.: `BR-153` ou `BR-116`) é dividida em centenas de trechos contíguos identificados por `id_trecho_rodoviario`, variando conforme `revestimento`, `tipo_pavimento` e `situacao_fisica`.

---

## 7. Cadastro Nacional de Estabelecimentos de Saúde (CNES) — DATASUS

Base relacional oficial do Ministério da Saúde contendo o cadastro, endereço, localização geográfica e tipologia de todas as unidades de saúde do território nacional.

* **URL de Referência:** `https://cnes.datasus.gov.br/` e `ftp://ftp.datasus.gov.br/cnes/`
* **Artefatos na Camada Bronze (`src/bronze/data/datasus/cnes_aux/`):**
  1. `tbEstabelecimento202603.csv` (~288 MB, 55 colunas).
  2. `tbMunicipio202603.csv` (13 colunas).
  3. `tbTipoUnidade202603.csv` (2 colunas).
* **Particularidades Técnicas:**
  - **Formatação CSV Estrita do DATASUS**: Os arquivos utilizam ponto e vírgula (`;`) como delimitador de colunas e envolvem todos os valores alfanuméricos em aspas duplas (`"`). Além disso, cabeçalhos de colunas de data possuem parênteses e vírgulas internas geradas por dumps Oracle do DATASUS, como `TO_CHAR(DT_ATUALIZACAO,'DD/MM/YYYY')` — o que exige leitura obrigatória com `sep=";"` e `low_memory=False`.
  - **Erros Cadastrais de Coordenadas (`NU_LATITUDE` e `NU_LONGITUDE`)**: Por serem preenchidas manualmente pelos gestores municipais de saúde, as coordenadas apresentam valores ausentes (`NaN`), coordenadas zeradas `(0, 0)`, sinais positivos no hemisfério sul/oeste ou inversão entre latitude e longitude. O pipeline Silver higieniza esses registros por meio de [`GeometryService.normalizar_par_coordenadas`](../silver/utils/geo_helpers.py) e realiza fallback para o centroide do município gestor quando a coordenada do estabelecimento é irrecuperável.

---

> **Trilha Modular — Etapa 03 de 18 (Ciclo 1.2 — Fontes Governamentais e APIs (`src/bronze/`))**: [Anterior: Ciclo 1.1 — Hub da Camada Bronze e Extratores (`src/bronze/`)](README.md) | [Portal Geral (`docs/README.md`)](../../docs/README.md) | [Próximo: Ciclo 1.3 — Dicionário de Dados Brutos (`src/bronze/`)](DICIONARIO_DADOS.md)
