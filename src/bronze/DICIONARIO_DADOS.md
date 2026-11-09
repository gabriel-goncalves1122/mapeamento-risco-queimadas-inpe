# Dicionário de Dados Estrutural: Camada Bronze (`src/bronze/data/`)

> **Trilha Modular — Etapa 04 de 18 (Ciclo 1.3 — Dicionário de Dados Brutos (`src/bronze/`))**: [Anterior: Ciclo 1.2 — Fontes Governamentais e APIs (`src/bronze/`)](FONTES_E_APIS.md) | [Portal Geral (`docs/README.md`)](../../docs/README.md) | [Próximo: Ciclos 2 e 3 — Hub da Camada Silver (`src/silver/`)](../silver/README.md)

Este documento especifica os esquemas exatos de todos os arquivos brutos (GeoJSON, CSV e Parquet) armazenados ou consumidos pela Camada Bronze (`src/bronze/data/`). Todos os nomes de campos, tipos nativos e exemplos refletem literalmente a estrutura física retornada pelas APIs e dumps governamentais antes do processamento pela Camada Silver.

---

## 1. Infraestrutura Elétrica — ANEEL / ONS (`src/bronze/data/aneel/`)

Os arquivos da ANEEL são objetos GeoJSON do tipo `FeatureCollection` extraídos do servidor ArcGIS REST MapServer (`outSR=4326`). Devido à origem KML/KMZ do banco do SIGEL, os atributos técnicos de engenharia encontram-se serializados em HTML dentro da propriedade `PopupInfo`.

### 1.1 `linhas_transmissao_ons.geojson` (Layer 1 — 1.817 feições)
* **Tipo Geométrico (`geometry.type`):** `LineString` / `MultiLineString` (`EPSG:4326`).

| Propriedade (`properties`) | Tipo Nativo | Nulável | Exemplo Real | Especificação e Uso no Pipeline |
|:---|:---:|:---:|:---|:---|
| `OID` | `int` | Não | `1` | Identificador sequencial único da feição no ArcGIS Server. Convertido para `id_linha_transmissao` (`str`). |
| `Name` | `str` | Sim | `'Linha LT  230 kV SCHARLAU 2           / CHARQUEADAS          C 1  RS'` | Denominação da linha de transmissão, contendo nível de tensão, subestações terminais, circuito e sigla da UF no sufixo. Possui múltiplos espaços consecutivos que são colapsados por `limpar_codigo()`. |
| `FolderPath` | `str` | Sim | `'Document/folderLTR1/Linha LT  230 kV...'` | Hierarquia de diretórios original do documento KML exportado pelo ONS. |
| `PopupInfo` | `str` (HTML) | Sim | `'<b>Tensão: </b>230 Kv<br/><b>Extensão: </b>72,96 Km'` | String HTML semiestruturada. A Camada Silver extrai `tensao_kv` (rótulo `"Tensão"`) e `extensao_km` (rótulo `"Extensão"`) via `extrair_popup_valor()`. |
| `Shape_Length` | `float` | Sim | `6.8985039` | Comprimento vetorial bruto em graus decimais calculado pelo banco Esri. |
| `SymbolID`, `AltMode`, `Base`, `Clamped`, `Extruded` | `int` | Sim | `0`, `-1` | Metadados visuais de renderização 3D do formato KML (ignorados pelo ETL analítico). |
| `Snippet` | `str` | Sim | `''` | Resumo textual KML (vazio na origem). |

---

### 1.2 `subestacoes_ons.geojson` (Layer 3 — 627 feições)
* **Tipo Geométrico (`geometry.type`):** `Point` (`EPSG:4326`).

| Propriedade (`properties`) | Tipo Nativo | Nulável | Exemplo Real | Especificação e Uso no Pipeline |
|:---|:---:|:---:|:---|:---|
| `OID` | `int` | Não | `1` | Identificador único da subestação no MapServer (`id_subestacao`). |
| `Name` | `str` | Sim | `'Subestação B. FLUMINENSE'` | Nome cadastral da subestação de energia elétrica. |
| `PopupInfo` | `str` (HTML) | Sim | `'<b>Nome: </b>B. FLUMINENSE<br/><b>Capacidade: </b>0 MW<br/><b>Agente: </b>Furnas...'` | Contém as tags HTML `<b>Nome: </b>`, `<b>Capacidade: </b>` (potência instalada em MW) e `<b>Agente: </b>` (concessionária transmissora). |
| `FolderPath` | `str` | Sim | `'Document/folderSUBR'` | Caminho de pasta KML de origem. |
| `SymbolID`, `AltMode`, `Base`, `HasLabel`, `LabelID` | `int` | Sim | `0`, `-1` | Atributos gráficos de simbologia KML/Esri. |
| `Snippet` | `str` | Sim | `''` | Resumo textual KML. |

---

### 1.3 `sistemas_isolados_ons.geojson` (Layer 5 — 120 feições)
* **Tipo Geométrico (`geometry.type`):** `Point` (`EPSG:4326`).

| Propriedade (`properties`) | Tipo Nativo | Nulável | Exemplo Real | Especificação e Uso no Pipeline |
|:---|:---:|:---:|:---|:---|
| `OID` | `int` | Não | `1` | Identificador único do sistema isolado (`id_sistema_isolado`). |
| `Name` | `str` | Sim | `'Afuá'` | Nome da localidade ou município atendido por geração isolada (não conectada ao SIN). |
| `PopupInfo` | `str` | Sim | `'Afuá - PA'` | String no formato `'LOCALIDADE - UF'`, processada por `extrair_uf_popup()` para obter a sigla do estado. |
| `FolderPath` | `str` | Sim | `'Document/Folder_SISOL'` | Diretório KML de origem. |
| `SymbolID`, `AltMode`, `Base`, `HasLabel`, `LabelID` | `int` | Sim | `0`, `-1` | Atributos gráficos de simbologia KML/Esri. |

---

## 2. Detecções Orbitais de Queimadas — INPE (`src/bronze/data/inpe/`)

### 2.1 `focos_incendio_brutos.csv` / `focos_diario_br_*.csv`
* **Formato:** CSV delimitado por vírgula (`,`), codificação `UTF-8`.
* **Sistema de Coordenadas:** WGS84 (`EPSG:4326`).

| Coluna Nativa | Tipo Pandas | Nulável / Sentinela | Exemplo Real | Especificação Técnica e Tratamento |
|:---|:---:|:---:|:---|:---|
| `DataHora` | `object` (`str`) | Não | `'2025/01/01 00:00:00'` | Data e hora UTC da passagem do satélite (`YYYY/MM/DD HH:MM:SS` ou `YYYY-MM-DD HH:MM:SS`). Normalizada por `extrair_data()` para ISO `YYYY-MM-DD HH:MM:SS`. |
| `Satelite` | `object` (`str`) | Não | `'GOES-16'` | Identificador do satélite/sensor (`AQUA_M-T`, `TERRA_M-T`, `NOAA-20`, `NPP-375`, `GOES-16`). Convertido em `fk_satelite_sensor`. |
| `Pais` | `object` (`str`) | Não | `'Brasil'` | País de ocorrência reportado pelo INPE (`pais_origem`). |
| `Estado` | `object` (`str`) | Não | `'MATO GROSSO'` | Nome por extenso da Unidade Federativa segundo a grade do INPE. |
| `Municipio` | `object` (`str`) | Não | `'VILA BELA DA SANTÍSSIMA TRINDADE'` | Nome do município segundo o INPE. Concatenado com `Estado` para formar `fk_municipio` (`UF_MUNICIPIO`). |
| `Bioma` | `object` (`str`) | Sim | `'Amazônia'` | Bioma brasileiro (`Amazônia`, `Cerrado`, `Mata Atlântica`, `Caatinga`, `Pampa`, `Pantanal`). Normalizado para `fk_bioma`. |
| `DiaSemChuva` | `int64` / `float64` | Sim (`<= -900`) | `3` | Número de dias consecutivos sem precipitação no pixel. Valores `-999` indicam ausência de grade meteorológica e são convertidos em `None` por `limpar_valor_numerico_nullable()`. |
| `Precipitacao` | `float64` | Sim (`<= -900`) | `1.97` | Precipitação acumulada no dia da detecção em milímetros (`mm`). |
| `RiscoFogo` | `float64` | Sim (`-999.0`) | `0.63` | Índice de Risco de Fogo do INPE no intervalo $[0.0, 1.0]$. Recebe `-999.0` em corpos d'água ou áreas urbanas sem vegetação mapeada. |
| `FRP` | `float64` | Sim (`NaN` / `<= -900`) | `84.8` | *Fire Radiative Power* (Potência Radiativa do Fogo) em Megawatts (`MW`). Mede a taxa de emissão de energia radiante térmica. |
| `Latitude` | `float64` | Não | `-15.253` | Coordenada geográfica de latitude em graus decimais (`EPSG:4326`). |
| `Longitude` | `float64` | Não | `-60.2095` | Coordenada geográfica de longitude em graus decimais (`EPSG:4326`). |

---

## 3. Terras Indígenas — FUNAI (`src/bronze/data/funai/`)

### 3.1 `mapa_terras_indigenas.geojson` (650 feições)
* **Tipo Geométrico (`geometry.type`):** `Polygon` / `MultiPolygon` (`EPSG:4326`).

| Propriedade (`properties`) | Tipo Nativo | Nulável | Exemplo Real | Especificação Técnica |
|:---|:---:|:---:|:---|:---|
| `codigo_ti` | `int` | Não | `101` | Código numérico oficial da Terra Indígena na FUNAI (chave primária na dimensão Silver). |
| `nome_terra_indigena` | `str` | Não | `'ACAPURI DE CIMA'` | Nome oficial da Terra Indígena. |
| `etnia` | `str` | Sim | `'Kokama'` | Etnia ou povos originários habitantes da reserva. |
| `municipios` | `str` | Sim | `'Fonte Boa'` | Lista de municípios abrangidos (separados por vírgula quando multimunicipal). |
| `estado` | `str` | Sim | `'AM'` | Sigla(s) da(s) Unidade(s) Federativa(s) de localização. |
| `area_hectares` | `float` | Sim | `18393.9411` | Superfície oficial demarcada em hectares (`ha`). |
| `estagio_regularizacao` | `str` | Sim | `'Regularizada'` | Fase do procedimento demarcatório (`Em Estudo`, `Delimitada`, `Declarada`, `Homologada`, `Regularizada`, `Encaminhada RI`). |
| `modalidade` | `str` | Sim | `'Tradicionalmente ocupada'` | Classificação jurídica da posse indígena. |
| `em_faixa_fronteira` | `str` | Sim | `'Não'` | Indicador (`'Sim'` / `'Não'`) de inserção na faixa de fronteira internacional (150 km). |

### 3.2 `tis_poligonais.csv` (Catálogo Administrativo — 20 colunas)
* **Formato:** CSV delimitado por vírgula (`,`), codificação `UTF-8`.

| Coluna Nativa | Tipo Pandas | Exemplo Real | Equivalência / Descrição |
|:---|:---:|:---|:---|
| `FID` / `gid` | `object` / `int64` | `'tis_poligonais.fid-...'` / `1` | Identificadores internos do servidor GeoServer da FUNAI. |
| `terrai_codigo` | `int64` | `101` | Código oficial da Terra Indígena (equivalente a `codigo_ti`). |
| `terrai_nome` | `object` | `'Acapuri de Cima'` | Nome oficial da Terra Indígena. |
| `etnia_nome` | `object` | `'Kokama'` | Nome da(s) etnia(s). |
| `municipio_nome` | `object` | `'Fonte Boa'` | Municípios interceptados. |
| `uf_sigla` | `object` | `'AM'` | Sigla da UF. |
| `superficie_perimetro_ha` | `float64` | `18393.9411` | Área oficial em hectares. |
| `fase_ti` / `modalidade_ti` | `object` | `'Regularizada'` | Estágio demarcatório e modalidade jurídica. |
| `reestudo_ti` | `float64` / `object` | `nan` | Indicador de procedimento de revisão de limites. |
| `cr` / `undadm_codigo` / `undadm_nome` / `undadm_sigla` | `object` / `int64` | `'COORDENACAO REGIONAL DO ALTO SOLIMOES'` / `'CR-AS'` | Dados da Coordenação Regional da FUNAI responsável pela tutela administrativa. |
| `faixa_fronteira` / `dominio_uniao` | `object` | `'Não'` / `'t'` | Indicadores booleanos de fronteira e patrimônio da União. |
| `data_atualizacao` / `epsg` | `object` / `int64` | `'05/09/2023'` / `0` | Metadados de atualização cadastral. |
| `the_geom` | `object` (`str`) | `'POLYGON ((-66.8835...))'` | Geometria do polígono serializada em *Well-Known Text* (WKT). |

---

## 4. Malha Municipal Brasileira — IBGE (`src/bronze/data/ibge/`)

### 4.1 `municipios_br.geojson` (5.564 feições)
* **Tipo Geométrico (`geometry.type`):** `Polygon` / `MultiPolygon` (`EPSG:4674` / `EPSG:4326`).

| Propriedade (`properties`) | Tipo Nativo | Nulável | Exemplo Real | Especificação Técnica e Tratamento |
|:---|:---:|:---:|:---|:---|
| `id` | `str` | Não | `'1100015'` | Código IBGE completo de 7 dígitos. No ETL Silver (`ETLDimMunicipios`), os 2 primeiros dígitos determinam a UF (`11` $\rightarrow$ `RO`) e os 6 primeiros dígitos formam `codigo_ibge` (`'110001'`). |
| `name` | `str` | Não | `"Alta Floresta D'Oeste"` | Nome oficial do município com acentuação e apóstrofos originais. |
| `description` | `str` | Sim | `"Alta Floresta D'Oeste"` | Repetição descritiva do nome municipal no catálogo GeoData-BR. |

---

## 5. Malha Rodoviária Federal — DNIT (`src/bronze/data/dnit/`)

### 5.1 `mapa_rodovias_federais.geojson` (14.255 feições)
* **Tipo Geométrico (`geometry.type`):** `LineString` / `MultiLineString` (`EPSG:4326`).

| Propriedade (`properties`) | Tipo Nativo | Nulável | Exemplo Real | Especificação Técnica |
|:---|:---:|:---:|:---|:---|
| `id_trecho_rodoviario` | `int` | Não | `28` | Identificador único do segmento no Sistema Nacional de Viação (SNV). |
| `codigo_rodovia` | `str` | Não | `'BR-324'` | Designação oficial da rodovia federal (`BR-XXX`). |
| `jurisdicao` | `str` | Sim | `'Federal'` | Esfera administrativa responsável (`Federal`, `Estadual`, `Distrital`). |
| `revestimento` | `str` | Sim | `'Pavimentado'` | Condição macro da via (`Pavimentado`, `Não Pavimentado`, `Planejado`). |
| `tipo_pavimento` | `str` | Sim | `'Desconhecido'` | Especificação do material de rolamento. |
| `situacao_fisica` | `str` | Sim | `'Construída'` | Estado físico de implantação do segmento. |
| `status_operacional` | `str` | Sim | `'Sim'` | Indicador de tráfego aberto (`'Sim'` / `'Não'`). |
| `geometria_wkt` | `str` | Sim | `'LINESTRING (-42.8928 -8.2584, ...)'` | Representação WKT de backup da geometria linear do trecho. |

---

## 6. Estabelecimentos de Saúde — DATASUS / CNES (`src/bronze/data/datasus/cnes_aux/`)

### 6.1 `tbEstabelecimento202603.csv` (Tabela Principal — 55 colunas)

| Coluna Nativa | Tipo Pandas | Nulável | Exemplo Real | Especificação Técnica e Tratamento |
|:---|:---:|:---:|:---|:---|
| `CO_UNIDADE` | `object` (`str`) | Não | `'2609602569302'` | Identificador composto interno do DATASUS (código IBGE 6 dígitos + código CNES 7 dígitos). |
| `CO_CNES` | `object` (`str`) | Não | `'2569302'` | Código Nacional de Estabelecimento de Saúde (7 dígitos). Chave primária na dimensão Silver (`codigo_cnes`). |
| `NO_RAZAO_SOCIAL` | `object` (`str`) | Sim | `'PREFEITURA MUNICIPAL DE OLINDA'` | Razão social da entidade mantenedora ou hospital. |
| `NO_FANTASIA` | `object` (`str`) | Sim | `'USF BULTRINS MONTE II'` | Nome público do estabelecimento (`nome_estabelecimento`). |
| `NO_LOGRADOURO`, `NU_ENDERECO`, `NO_BAIRRO`, `CO_CEP` | `object` (`str`) | Sim | `'RUA DO SOL'`, `'120'`, `'CENTRO'`, `'53000000'` | Dados de endereço postal do estabelecimento. |
| `TP_UNIDADE` / `CO_TIPO_UNIDADE` | `object` (`str`) | Sim | `'02'`, `'05'` | Código numérico da tipologia da unidade (chave estrangeira para `tbTipoUnidade`). |
| `CO_ESTADO_GESTOR` | `object` (`str`) | Sim | `'26'` | Código numérico IBGE de 2 dígitos da Unidade Federativa gestora. |
| `CO_MUNICIPIO_GESTOR` | `object` (`str`) | Não | `'260960'` | Código IBGE de **6 dígitos** do município gestor. |
| `NU_LATITUDE` | `object` / `float64` | Sim (`NaN`) | `-8.0089` | Latitude cadastrada manualmente. Sujeita a inversão com longitude ou erro de sinal, tratada por `normalizar_par_coordenadas()`. |
| `NU_LONGITUDE` | `object` / `float64` | Sim (`NaN`) | `-34.8553` | Longitude cadastrada manualmente. |
| `TP_ESTAB_SEMPRE_ABERTO` | `object` (`str`) | Sim | `'S'` / `'N'` | Indica se o estabelecimento opera em regime ininterrupto de 24 horas (`funciona_24h`). |
| `TP_GESTAO` | `object` (`str`) | Sim | `'M'` / `'E'` / `'D'` | Modalidade de gestão do SUS (`M` = Municipal, `E` = Estadual, `D` = Dupla). |
| `CO_NATUREZA_JUR` | `object` (`str`) | Sim | `'1244'` | Código CONCLA da natureza jurídica da instituição. |

---

## 7. ONS — Interrupção de Carga (`INTERRUPCAO_CARGA.parquet`)

Base consolidada do Operador Nacional do Sistema Elétrico contendo 8.395 registros de ocorrências com corte de carga severo ($\ge 100\text{ MW}$) apuradas entre 2007 e Novembro de 2026.

* **Origem:** `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/interrupcao_carga/INTERRUPCAO_CARGA.parquet`
* **Formato:** Apache Parquet (Snappy).

| Coluna Nativa | Tipo Parquet | Tipo Pandas | Exemplo Real | Especificação Técnica e Domínio |
|:---|:---:|:---:|:---|:---|
| `cod_perturbacao` | `string` | `object` | `'0413/2007'` | Código oficial de registro do distúrbio no ONS. |
| `din_interrupcaocarga` | `timestamp[ns]` | `datetime64[ns]` | `2024-09-14 15:20:00` | Data e hora de início do evento com corte de suprimento. |
| `id_subsistema` | `string` | `object` | `'SE'` | Código do subsistema elétrico (`SE`, `S`, `NE`, `N`). |
| `nom_subsistema` | `string` | `object` | `'SUDESTE'` | Nome por extenso da região eletroenergética. |
| `id_estado` | `string` | `object` | `'GO'` | Sigla da Unidade Federativa da ocorrência. |
| `nom_agente` | `string` | `object` | `'EQUATORIAL GOIÁS'` | Concessionária ou agente de transmissão/distribuição afetado. |
| `val_cargainterrompida_mw` | `double` | `float64` | `185.4` | Montante instantâneo de carga cortada em Megawatts (MW). |
| `val_tempomedio_minutos` | `double` | `float64` | `45.0` | Duração média em minutos da interrupção. |
| `val_energianaosuprida_mwh` | `double` | `float64` | `139.05` | Energia Não Suprida (ENS) estimada em Megawatt-hora. |
| `flg_envolveuredebasica` | `string` | `object` | `'S'` | Indicador (`'S'`/`'N'`) de envolvimento da Rede Básica ($\ge 230\text{ kV}$). |
| `flg_envolveuredeoperacao` | `string` | `object` | `'S'` | Indicador (`'S'`/`'N'`) de envolvimento da Rede de Operação. |

---

## 8. ONS — Cadastro Físico e Elétrico de Linhas de Transmissão (`LINHA_TRANSMISSAO.parquet`)

Cadastro técnico contendo 2.346 linhas de transmissão em operação comercial no Sistema Interligado Nacional.

* **Origem:** `https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.parquet`
* **Formato:** Apache Parquet (Snappy, 37 colunas).

| Coluna Nativa | Tipo Parquet | Exemplo Real | Especificação de Engenharia Elétrica |
|:---|:---:|:---|:---|
| `nom_linhadetransmissao` | `string` | `'LT 500 kV Itumbiara / Rio Verde C1'` | Denominação oficial da LT. |
| `cod_equipamento` | `string` | `'LT-ITB-RVD-500-1'` | Código identificador nos Procedimentos de Rede. |
| `val_niveltensao_kv` | `double` | `500.0` | Tensão nominal de operação em kV. |
| `val_comprimento` | `double` | `182.5` | Extensão física do vão em quilômetros. |
| `nom_subestacao_de`, `nom_subestacao_para` | `string` | `'ITUMBIARA'`, `'RIO VERDE'` | Subestações terminais de conexão. |
| `num_barra_de`, `num_barra_para` | `int64` | `6980`, `6950` | Números das barras elétricas para modelagem em grafo (`NetworkX`). |
| `val_resistencia`, `val_reatancia`, `val_shunt` | `double` | `0.0082`, `0.0874`, `1.452` | Parâmetros de sequência positiva ($R, X, B$) para simulação de fluxo e contingência $N-1$. |
| `nom_agenteproprietario` | `string` | `'FURNAS'` | Agente transmissor titular do ativo. |

---

## 9. Open-Meteo — Observações Meteorológicas de Superfície (`clima_horario_openmeteo.parquet`)

* **Origem:** `https://api.open-meteo.com/v1/forecast` e `archive-api.open-meteo.com/v1/archive`
* **Formato:** Apache Parquet gerado a partir do payload JSON/FlatBuffers.

| Coluna | Tipo Polars / Pandas | Exemplo Real | Descrição Técnica |
|:---|:---:|:---|:---|
| `timestamp` | `datetime64[ns]` | `2026-11-09 14:00:00` | Data e hora da leitura horária (fuso local `America/Sao_Paulo`). |
| `latitude`, `longitude` | `float64` | `-22.42`, `-45.45` | Ponto geográfico de consulta WGS84. |
| `wind_speed_10m_kmh` | `float64` | `18.5` | Velocidade do vento a 10 metros da superfície em km/h. |
| `wind_direction_10m_deg` | `float64` | `135.0` | Azimute de origem do vento em graus ($0^\circ$ a $360^\circ$). |
| `wind_gusts_10m_kmh` | `float64` | `32.0` | Velocidade da rajada máxima de vento em km/h. |
| `relative_humidity_2m_pct` | `float64` | `28.0` | Umidade relativa do ar a 2 metros de altura em percentual ($0$ a $100\%$). |

---

## 10. INMET — Avisos Meteorológicos Ativos (`avisos_ativos_inmet.json`)

* **Origem:** `https://apiprevmet3.inmet.gov.br/avisos/ativos`
* **Formato:** JSON RFC 7946 com geometrias GeoJSON.

| Campo | Tipo JSON | Exemplo Real | Aplicação no Sistema de Alerta |
|:---|:---:|:---|:---|
| `id` / `aviso_id` | `int` / `string` | `89412` | Identificador do aviso no Instituto Nacional de Meteorologia. |
| `descricao` | `string` | `'Baixa Umidade'` | Categoria do evento adverso (ex.: `'Baixa Umidade'`, `'Tempestade'`, `'Onda de Calor'`). |
| `severidade` | `string` | `'Perigo Potencial'` | Nível de gravidade (`'Perigo Potencial'`, `'Perigo'`, `'Grande Perigo'`). |
| `inicio`, `fim` | `string` (ISO) | `'2026-11-09T12:00:00-03:00'` | Janela temporal de vigência do alerta. |
| `poligono` | `string` / `geometry` | `'POLYGON((...))'` | Delimitação territorial da área sob risco meteorológico extremo. |

---

> **Trilha Modular — Etapa 04 de 18 (Ciclo 1.3 — Dicionário de Dados Brutos (`src/bronze/`))**: [Anterior: Ciclo 1.2 — Fontes Governamentais e APIs (`src/bronze/`)](FONTES_E_APIS.md) | [Portal Geral (`docs/README.md`)](../../docs/README.md) | [Próximo: Ciclos 2 e 3 — Hub da Camada Silver (`src/silver/`)](../silver/README.md)
