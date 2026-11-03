# Catálogo Técnico de Fontes e APIs - Camada Bronze

Este documento consolida as especificações técnicas, métodos de coleta, endpoints de APIs governamentais, limitações de taxa (*rate limiting*), frequências de atualização e formatos de entrega de todos os dados consumidos na **Camada Bronze**.

As referências bibliográficas oficiais dos provedores governamentais estão alinhadas com o referencial teórico e a bibliografia do Relatório Final de Iniciação Científica ([`docs/academic/relatorio_final/referencias.bib`](../../docs/academic/relatorio_final/referencias.bib)).

---

## 1. ANEEL / ONS (Sistema de Informações Geográficas do Setor Elétrico - SIGEL)

A infraestrutura de transmissão de energia do Sistema Interligado Nacional (SIN) é extraída de forma automatizada através da API ArcGIS Server REST mantida pela Agência Nacional de Energia Elétrica (ANEEL).

* **Órgão Responsável:** Agência Nacional de Energia Elétrica (ANEEL) / Operador Nacional do Sistema Elétrico (ONS).
* **Referência Oficial:** `aneel_sigel_2026` ([SIGEL ANEEL Portal](https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/)) e `ons_mapa_2026` ([Mapas do SIN - ONS](http://www.ons.org.br/paginas/sobre-o-sin/mapas)).
* **Tipo de Acesso:** API REST pública (serviço ESRI ArcGIS Server MapServer).
* **URL Base do Serviço:**
  ```text
  https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmiss%C3%A3o/MapServer/{id}/query
  ```
* **Camadas Mapeadas ({id}):**
  - **Layer `1`**: Linhas de Transmissão (`linhas_transmissao_ons.geojson`).
  - **Layer `3`**: Subestações de Energia Elétrica (`subestacoes_ons.geojson`).
  - **Layer `5`**: Sistemas Elétricos Isolados da Amazônia Legal (`sistemas_isolados_ons.geojson`).

### 1.1 Parâmetros Técnicos da Consulta HTTP GET

| Parâmetro | Valor Configurado | Justificativa Técnica |
|---|---|---|
| `where` | `1=1` | Cláusula SQL para retornar todo o conjunto de feições sem filtro preliminar de atributos. |
| `outFields` | `*` | Retorna todos os atributos originais do MapServer (código, tensão, concessionária, extensão). |
| `f` | `geojson` | Serializa o resultado no formato GeoJSON padrão IETF RFC 7946. |
| `resultOffset` | Variável (0, 1000, 2000...) | Ponteiro de paginação para varredura do cursor de feições. |
| `resultRecordCount` | `1000` | Limite máximo de registros permitidos por requisição pelo ArcGIS Server da ANEEL. |
| `outSR` | `4326` | Força a reprojeção na origem do servidor para coordenadas geográficas WGS84 (`EPSG:4326`). |

### 1.2 Regras de Resiliência e Throttling
- **Rate Limiting:** A classe [`AneelArcGisExtractor`](src/ingestao_aneel.py) introduz uma pausa configurável (`rate_limit_s = 1.0` segundo) entre requisições consecutivas para mitigar bloqueios de IP (*HTTP 429 Too Many Requests*).
- **Validação de Payload:** Caso o serviço retorne código HTTP diferente de 200 ou uma lista vazia de *features*, a iteração é interrompida com log explícito.
- **Formato Final em Disco:** `src/bronze/data/aneel/{camada}_ons.geojson`.

---

## 2. INPE / NASA (BDQueimadas - Programa Queimadas)

O monitoramento de focos de incêndio e anomalias térmicas é fornecido pelo Instituto Nacional de Pesquisas Espaciais (INPE) através do banco de dados BDQueimadas, consolidando detecções de sensores orbitais óticos e infravermelhos termais.

* **Órgão Responsável:** Instituto Nacional de Pesquisas Espaciais (INPE) e NASA.
* **Referência Oficial:** `inpe_bdqueimadas_2026` ([BDQueimadas - Dados Abertos](https://data.inpe.br/queimadas/bdqueimadas/)) e `inpe_queimadas` ([Portal do Programa Queimadas](http://queimadas.dgi.inpe.br/queimadas/portal)).
* **Algoritmo de Sensoriamento:** Giglio et al. (2016) - *Collection 6 MODIS Active Fire Detection Algorithm* ([DOI: 10.1016/j.rse.2016.02.054](https://doi.org/10.1016/j.rse.2016.02.054)).
* **Satélites e Sensores Utilizados:**
  - `AQUA_M-T` e `TERRA_M-T` (Sensor MODIS): Satélites de referência histórica para contagem estatística oficial.
  - `NOAA-20` e `S-NPP` (Sensor VIIRS): Resolução espacial aprimorada (pixels de 375 m).
  - Satélites geoestacionários (`GOES-16`): Monitoramento contínuo em alta frequência temporal.
* **Formato de Entrega:** Arquivos tabulares CSV (estruturados por dia ou mês) e Web Service de dados abertos.
* **Frequência de Atualização:**
  - *Quase Tempo Real (NRT):* Pacotes incrementais atualizados a cada 3 horas.
  - *Consolidação Diária:* Fechamento com aplicação de filtros de qualidade e cálculo retroativo de FRP (*Fire Radiative Power*).
* **Destino na Bronze:** `src/bronze/data/inpe/focos_*.csv`.

---

## 3. FUNAI (Fundação Nacional dos Povos Indígenas)

Informações de delimitação, situação jurídica e caracterização demográfica das Terras Indígenas no Brasil.

* **Órgão Responsável:** Fundação Nacional dos Povos Indígenas (FUNAI) / Ministério dos Povos Indígenas.
* **Referência Oficial:** `funai_terras_2026` ([FUNAI: Geoprocessamento e Mapas](https://www.gov.br/funai/pt-br/atuacao/terras-indigenas/geoprocessamento-e-mapas)).
* **Portal de Origem:** Geoportal da FUNAI e Catálogo de Dados Abertos Governamentais.
* **Arquivos Ingeridos na Camada Bronze:**
  - `mapa_terras_indigenas.geojson`: Vetores poligonais georreferenciados de todas as TIs em projeção WGS84.
  - `tis_poligonais.csv`: Tabela complementar com atributos de fase de demarcação (*Homologada*, *Regularizada*, *Delimitada*, *Em Estudo*), superfície em hectares e etnias predominantes.
* **Frequência de Atualização:** Atualizações sob emissão de Decretos Presidenciais e Portarias Declaratórias do Ministério da Justiça / FUNAI.
* **Destino na Bronze:** `src/bronze/data/funai/`.

---

## 4. IBGE (Instituto Brasileiro de Geografia e Estatística)

Malha político-administrativa de referência de todos os 5.564 municípios da Federação Brasileira.

* **Órgão Responsável:** Instituto Brasileiro de Geografia e Estatística (IBGE) - Diretoria de Geociências.
* **Referência Oficial:** `ibge_malha_2022` ([IBGE: Malha Territorial Brasileira](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/)) e `brugz_geodata_2026` ([GeoData-BR](https://github.com/tbrugz/geodata-br)).
* **Fonte de Origem:** Malha Municipal Digital do Brasil (escala 1:250.000).
* **Formato do Arquivo:** `municipios_br.geojson`.
* **Características Geodésicas:**
  - Projeção nativa oficial: SIRGAS 2000 Geográfico (`EPSG:4674`), compatível com WGS84 (`EPSG:4326`) para efeitos de cálculo planar.
  - Chave Primária Oficial: Código IBGE de 7 dígitos (`CD_MUN`), indispensável para a modelagem relacional Snowflake do ecossistema.
* **Destino na Bronze:** `src/bronze/data/ibge/`.

---

## 5. DNIT / SNV (Sistema Nacional de Viação)

Mapeamento geométrico e cadastral da malha viária brasileira.

* **Órgão Responsável:** Departamento Nacional de Infraestrutura de Transportes (DNIT) / Ministério dos Transportes.
* **Referência Oficial:** SNV - Sistema Nacional de Viação do DNIT e repositório `brugz_geodata_2026` ([GeoData-BR Rodovias](https://github.com/tbrugz/geodata-br)).
* **Fonte de Origem:** Portal de Dados Abertos de Transportes do DNIT (Camada de Rodovias Federais e Coincidentes).
* **Formato do Arquivo:** `rodovias_federais.geojson`.
* **Estrutura Geométrica:** Feições do tipo `LineString` e `MultiLineString` segmentadas por marcos quilométricos (`km_inicial` a `km_final`) e código de rodovia federal (`vl_br`, ex: `BR-116`, `BR-101`, `BR-153`).
* **Destino na Bronze:** `src/bronze/data/dnit/`.

---

## 6. DATASUS / CNES (Cadastro Nacional de Estabelecimentos de Saúde)

Infraestrutura hospitalar e capacidade assistencial de saúde pública e privada no território nacional.

* **Órgão Responsável:** Ministério da Saúde / Departamento de Informática do SUS (DATASUS).
* **Referência Oficial:** `datasus_cnes_2026` ([Portal CNES - DATASUS](https://cnes.datasus.gov.br/)).
* **Fonte de Origem:** OpenDataSUS / Base de Dados Disseminável do CNES.
* **Arquivos Auxiliares Ingeridos em `cnes_aux/`:**
  - `tbEstabelecimento*.csv`: Dados cadastrais da unidade (Código CNES, Nome Fantasia, Razão Social, Latitude, Longitude, Município Gestor).
  - `tbLeito*.csv`: Contagem física de leitos operacionais de internação clínica, cirúrgica e leitos complementares.
  - `tbTipoUnidade*.csv`: Classificação da tipologia do estabelecimento (Hospital Geral, Hospital Especializado, Pronto-Socorro).
* **Especificações Técnicas de Leitura:**
  - Codificação de Caracteres: `latin-1` (ISO-8859-1).
  - Delimitador de Colunas: Ponto e vírgula (`;`).
  - Coordenadas Geográficas: Extraídas com tratamento de separador decimal e validação de quadrante brasileiro.
* **Destino na Bronze:** `src/bronze/data/datasus/cnes_aux/`.
