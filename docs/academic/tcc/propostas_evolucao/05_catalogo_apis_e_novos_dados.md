# Catálogo de Dados, Especificação de APIs e Protocolos de Ingestão (`SIRDA 2.0`)

> **Navegação no TCC**: [Portal TCC (`../README.md`)](../README.md) | [00. Visão Geral e Roadmap](00_visao_geral_roadmap_tcc.md) | [03. Novas Bases de Dados](03_novas_bases_dados_e_modelagem_fisica.md) | [04. Indexação H3](04_novas_tecnologias_h3_e_duckdb_spatial.md)

Este documento consolida a especificação técnica formal, os protocolos de rede, as regras de autenticação, as quotas operacionais, os esquemas tabulares e os exemplos de requisição para todas as novas fontes de dados propostas para a evolução do **SIRDA 2.0** no Trabalho de Conclusão de Curso (UNIFEI).

---

## 1. Matriz Geral de Fontes e Tecnologias de Ingestão

| Provedor | Conjunto de Dados / Domínio | Protocolo & Formato de Transporte | Mecanismo de Acesso / Armazenamento | Frequência de Atualização | Autenticação / Licença | Papel Analítico no SIRDA 2.0 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ONS** | `INTERRUPCAO_CARGA` (Desligamentos forçados) | HTTP GET / **Apache Parquet** (`sa-east-1`) | AWS S3 Open Data (`read_parquet`) | Mensal / Diária | Pública (Sem chave) / `CC-BY 4.0` | **Ground-Truth de Validação**: Validação empírica (*Backtesting* ROC/AUC) de desligamentos por fogo. |
| **ONS** | `LINHA_TRANSMISSAO` (Cadastro do SIN $\ge 230\text{ kV}$) | HTTP GET / **Apache Parquet** (`sa-east-1`) | AWS S3 Open Data (`read_parquet`) | Diária (12h e 19h) | Pública (Sem chave) / `CC-BY 4.0` | **Infraestrutura Crítica**: Atributos elétricos (tensão, extensão, agente, código). |
| **Open-Meteo** | Vento ($\vec{W}$ a 10m) e Umidade do Ar (2m) | REST HTTP GET / **FlatBuffers** & JSON | API Nuvem (`openmeteo-requests`) | Horária (Reanálise 1940+ e Forecast 16d) | Pública (Sem chave para acadêmico) / `CC-BY 4.0` | **Modelagem Física**: Elipses anisotrópicas de propagação e cálculo de dessecação de combustível. |
| **INMET** | Avisos de Perigo Meteorológico Ativos | REST HTTP GET / **GeoJSON** | `apiprevmet3.inmet.gov.br` | Contínua (Emissão de alertas) | Pública (Exige *User-Agent*) / Domínio Público | **Prontidão Operacional**: Gatilho para elevação de nível de alerta da Defesa Civil e CCO. |
| **MapBiomas** | Coleção 11 (LULC 30m) & Coleção 5.1 (Fogo) | **Google Earth Engine (GEE)** & GeoTIFF | GEE Asset ID / GeoServer WMS | Anual / Monitor Mensal | Pública com cadastro GEE / `CC-BY-SA 4.0` | **Carga Combustível**: Fator de inflamabilidade vegetal (Pastagem 15, Campo 12, Savana 4). |
| **NASA FIRMS** | Sensores VIIRS (NOAA-20/21 375m) & GOES-16/19 ABI | REST HTTP GET / **CSV** & GeoJSON | `firms.modaps.eosdis.nasa.gov` | NRT (30 min a 3 horas) | `MAP_KEY` Gratuita (5.000 req/dia) | **Detecção Fina**: Focos com resolução espacial de 375m para amarração com torres e vãos de LTs. |
| **INPE** | BDQueimadas (Satélites de Referência & 10 min) | HTTP File Server / **CSV** & GeoPackage | `dataserver-coids.inpe.br` | A cada 10 min e Diário | Pública (Sem chave) / Domínio Público | **Detecção Ampla Nacional**: Série histórica de focos, FRP e índice institucional de Risco de Fogo. |

---

## 2. ONS — Operador Nacional do Sistema Elétrico (AWS S3 Open Data)

### 2.1 Particularidades de Acesso e Endpoints
O portal `dados.ons.org.br` utiliza a plataforma CKAN versão 2.9+, mas **não** disponibiliza a extensão DataStore (`datastore_search`). Os arquivos de dados brutos são hospedados diretamente em buckets públicos do **Amazon S3** sob o programa *AWS Open Data Sponsorship*.

*   **Bucket S3**: `arn:aws:s3:::ons-aws-prod-opendata` (Região `sa-east-1`, São Paulo).
*   **Acesso Direto**: Totalmente aberto via HTTPS, dispensando credenciais ou chaves da AWS.

#### URLs Oficiais dos Artefatos em Formato Apache Parquet:
1.  **Interrupção de Carga (`INTERRUPCAO_CARGA`)**:
    ```text
    https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/interrupcao_carga/INTERRUPCAO_CARGA.parquet
    ```
2.  **Linhas de Transmissão (`LINHA_TRANSMISSAO`)**:
    ```text
    https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.parquet
    ```
3.  **Indicadores de Disponibilidade de Função Transmissão (`IND_DISPONIBILIDADE_FT_TRLT`)**:
    ```text
    https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ind_disponibilidade_ft_trlt_me/IND_DISPONIBILIDADE_FT_TRLT_2026.parquet
    ```

### 2.2 Dicionário de Dados e Esquema de Colunas Verificado em Produção

#### Tabela: `INTERRUPCAO_CARGA` (Critérios da Norma `RO-AO.BR.03` — 8.395 registros apurados de 2007 a Nov/2026)
| Campo | Tipo Parquet | Tipo Polars / Pandas | Descrição Semântica e Regra de Domínio |
| :--- | :--- | :--- | :--- |
| `cod_perturbacao` | `STRING` | `Utf8` | Código oficial da perturbação no ONS (ex.: `'0413/2007'`, `'0123/2024'`). Chave de ligação com os Relatórios de Análise de Perturbação (RAP). |
| `din_interrupcaocarga` | `TIMESTAMP_NTZ` | `Datetime` | Data e hora exata do início do desligamento com corte de carga (UTC-3). Amostrado de 01/01/2007 a 06/11/2026. |
| `id_subsistema` | `STRING` | `Utf8` | Código do subsistema elétrico de origem (`'SE'`, `'S'`, `'NE'`, `'N'`). |
| `nom_subsistema` | `STRING` | `Utf8` | Nome por extenso do subsistema (`'SUDESTE'`, `'SUL'`, `'NORDESTE'`, `'NORTE'`). |
| `id_estado` | `STRING` | `Utf8` | Sigla da Unidade Federativa da ocorrência (Líderes históricos: RS 1.027, GO 928, PA 851, RR 597, SP 552). |
| `nom_agente` | `STRING` | `Utf8` | Agente concessionário afetado (ex.: `'EQUATORIAL GOIÁS'`, `'EQUATORIAL PARÁ'`, `'NEOENERGIA COELBA'`, `'RGE SUL'`). |
| `val_cargainterrompida_mw` | `DOUBLE` | `Float64` | Montante instantâneo de potência ativa interrompida em Megawatts (Acumulado histórico: **717.448 MW**). |
| `val_tempomedio_minutos` | `DOUBLE` | `Float64` | Duração média em minutos da interrupção até restabelecimento. |
| `val_energianaosuprida_mwh` | `DOUBLE` | `Float64` | Energia Não Suprida (ENS) estimada em Megawatt-hora (MWh). |
| `flg_envolveuredebasica` | `STRING` | `Utf8` | Indicador binário (`'S'` ou `'N'`) se o evento impactou instalações da Rede Básica ($\ge 230\text{ kV}$). |
| `flg_envolveuredeoperacao` | `STRING` | `Utf8` | Indicador binário (`'S'` ou `'N'`) se o distúrbio envolveu a Rede de Operação supervisionada pelo ONS. |

#### Tabela: `LINHA_TRANSMISSAO` (2.346 linhas de transmissão ativas no SIN)
A base do ONS disponibiliza 37 colunas de dados elétricos e cadastrais de alta fidelidade:
| Campo | Tipo Parquet | Descrição Semântica e Aplicação em Engenharia |
| :--- | :--- | :--- |
| `nom_linhadetransmissao` | `STRING` | Denominação operacional da LT (ex.: `'LT 500 kV Itumbiara / Rio Verde C1'`). |
| `cod_equipamento` | `STRING` | Código unificado do ativo nos Procedimentos de Rede. |
| `val_niveltensao_kv` | `DOUBLE` | Tensão nominal de operação em quilovolt ($230\text{ kV}$, $345\text{ kV}$, $500\text{ kV}$, $765\text{ kV}$). |
| `val_comprimento` | `DOUBLE` | Extensão física do traçado em quilômetros. |
| `nom_subestacao_de`, `nom_subestacao_para` | `STRING` | Subestações terminais de conexão da linha. |
| `num_barra_de`, `num_barra_para` | `INT64` | Identificadores numéricos das barras elétricas para modelagem de fluxo de potência em grafos (`NetworkX`). |
| `val_resistencia`, `val_reatancia`, `val_shunt` | `DOUBLE` | Parâmetros de linha em p.u. / Ohms ($R, X, B$) para simulação de contingência elétrica $N-1$. |
| `nom_agenteproprietario` | `STRING` | Concessionária transmissora responsável pela manutenção da faixa de servidão. |

### 2.3 Exemplo de Consulta Vetorizada via PyArrow / DuckDB
```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region = 'sa-east-1';")

# Consulta agregada de eventos de queimada por subsistema
df_queimadas = con.execute("""
    SELECT 
        nom_subsistema,
        COUNT(*) as total_desligamentos,
        ROUND(SUM(val_carga_interrompida_mw), 2) as mw_total_perdido
    FROM read_parquet('https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/interrupcao_carga/INTERRUPCAO_CARGA.parquet')
    WHERE dsc_causa ILIKE '%queimada%' 
       OR dsc_causa ILIKE '%incêndio%'
       OR dsc_causa ILIKE '%fogo%'
    GROUP BY nom_subsistema
    ORDER BY total_desligamentos DESC
""").pl()
```

---

## 3. Meteorologia: Open-Meteo & INMET

### 3.1 Open-Meteo Weather API (Vento e Umidade Contínuos)

A Open-Meteo agrega os modelos meteorológicos de reanálise **ERA5 / ERA5-Land** (ECMWF) para séries históricas e modelos operacionais em alta resolução (GFS, ICON, Meso-NH) para previsões.

#### Endpoints Oficiais
*   **Histórico e Reanálise (desde 1940)**:
    `https://archive-api.open-meteo.com/v1/archive`
*   **Previsão Numérica (Horizonte de até 16 dias)**:
    `https://api.open-meteo.com/v1/forecast`

#### Parâmetros de Consulta Obrigatórios para o SIRDA
| Parâmetro | Tipo | Exemplo | Descrição Técnica |
| :--- | :--- | :--- | :--- |
| `latitude`, `longitude` | `float` | `-22.42,-45.45` | Coordenadas WGS84 do centro do vão da LT ou foco de calor. |
| `hourly` | `string` | `wind_speed_10m,wind_direction_10m,wind_gusts_10m,relative_humidity_2m` | Variáveis meteorológicas horárias solicitadas. |
| `wind_speed_unit` | `string` | `kmh` (ou `ms`) | Unidade da velocidade do vento ($\text{km/h}$ ou $\text{m/s}$). |
| `timeformat` | `string` | `iso8601` ou `unixtime` | Padrão dos registros temporais retornados. |
| `timezone` | `string` | `America/Sao_Paulo` | Fuso horário para alinhamento com a operação do SIN. |
| `format` | `string` | `flatbuffers` (ou `json`) | Serialização binária ultrarrápida ou JSON textual. |

#### Exemplo de Requisição via `cURL`
```bash
curl -X GET "https://api.open-meteo.com/v1/forecast?latitude=-22.42&longitude=-45.45&hourly=wind_speed_10m,wind_direction_10m,wind_gusts_10m,relative_humidity_2m&wind_speed_unit=kmh&timezone=America/Sao_Paulo&forecast_days=2" \
     -H "Accept: application/json"
```

#### Quotas e Governança
*   **Sem necessidade de chave** para uso acadêmico e de pesquisa.
*   **Limites do Tier Gratuito**: 600 requisições/minuto, 10.000 requisições/dia.
*   **Otimização FCIS**: Recomenda-se cache local com `requests_cache` de 3.600 segundos (1 hora), pois dados horários não mudam dentro da mesma hora de medição.

---

### 3.2 INMET API — Avisos Meteorológicos Ativos de Risco

O Instituto Nacional de Meteorologia disponibiliza alertas geográficos de eventos meteorológicos adversos vigentes em território nacional.

#### Endpoints
*   **Avisos Ativos (Polígonos de Risco)**:
    `GET https://apiprevmet3.inmet.gov.br/avisos/ativos`
*   **Catálogo de Estações Automáticas**:
    `GET https://apitempo.inmet.gov.br/estacoes/T`
*   **Medição Horária por Estação**:
    `GET https://apitempo.inmet.gov.br/estacao/{data_ini}/{data_fim}/{cd_estacao}`

#### Requisito Crítico de Conexão HTTP (User-Agent)
> [!WARNING]
> O firewall do INMET aplica bloqueio por TCP reset para clientes HTTP que não informem um cabeçalho `User-Agent` de navegador comum. O cliente Python deve obrigatoriamente injetar:
> `headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}`

#### Estrutura do Aviso do INMET
```json
{
  "id": 89412,
  "aviso_id": "AVISO-2026-11-08-01",
  "descricao": "Baixa Umidade",
  "severidade": "Perigo Potencial",
  "riscos": "Umidade relativa do ar variando entre 30% e 20%. Baixo risco de incêndios florestais e à saúde.",
  "inicio": "2026-11-08T12:00:00-03:00",
  "fim": "2026-11-08T19:00:00-03:00",
  "poligono": "POLYGON((-46.5 -22.1, -45.0 -22.1, -45.0 -23.0, -46.5 -23.0, -46.5 -22.1))",
  "municipios": ["Itajubá", "Pouso Alegre", "Santa Rita do Sapucaí"]
}
```

---

## 4. MapBiomas: Cobertura da Terra e Matriz de Inflamabilidade

### 4.1 Coleções e Assets no Google Earth Engine (GEE)
Os dados do MapBiomas são acessados diretamente na nuvem via Google Earth Engine API (`ee.Image`):

| Produto | Versão / Coleção | Identificador de Asset GEE | Resolução Espacial |
| :--- | :--- | :--- | :--- |
| **Cobertura e Uso da Terra (LULC)** | Coleção 11 | `projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3` | **30 metros** (Landsat) |
| **Frequência de Queimadas (1985–2025)** | Coleção 5.1 | `projects/mapbiomas-public/assets/brazil/fire/collection5_1/mapbiomas_fire_collection51_fire_frequency_v1` | **30 metros** |
| **Monitor Mensal de Queimadas** | Quase-tempo-real | `projects/mapbiomas-public/assets/brazil/fire/monitor/mapbiomas_fire_monthly_burned_v1` | **30 metros** |

### 4.2 Matriz de Pesos de Inflamabilidade do Combustível

No modelo de propagação do SIRDA 2.0, as classes da Coleção 11 recebem os seguintes multiplicadores de velocidade de queima e risco de centelhamento sob linhas de transmissão:

| Código da Classe (`class_id`) | Nome da Classe | Nível de Risco de Combustível | Peso Físico ($K_{comb}$) | Comportamento do Fogo |
| :---: | :--- | :---: | :---: | :--- |
| **15** | Pastagem | **Crítico (Muito Alto)** | **1.00** | Combustível fino (1h time-lag); perda imediata de umidade; principal causa de curto-circuito em faixas de servidão. |
| **12** | Formação Campestre | **Crítico (Muito Alto)** | **0.95** | Gramíneas nativas contínuas e secas; altíssima inflamabilidade por faíscas. |
| **4** | Formação Savânica (Cerrado) | **Alto** | **0.80** | Estrato arbustivo-gramíneo adaptado ao fogo; queima sazonal violenta entre agosto e outubro. |
| **11** | Área Úmida / Pantanosa Seca | **Alto (Sazonal)** | **0.75** | Acúmulo maciço de biomassa orgânica; sob estiagem profunda propaga fogo de subsolo. |
| **21** | Mosaico de Usos | **Alto** | **0.70** | Pedaços de pasto, restos de colheita e capoeira; fogo frequente de manejo. |
| **9** | Silvicultura (Eucalipto / Pinus) | **Médio-Alto** | **0.60** | Alta carga combustível no sub-bosque (folhedo seco e cascas soltas). |
| **3** | Formação Florestal (Mata Fechada) | **Baixo a Médio** | **0.30** | Dossel retém umidade; atua como barreira contra ventos rasteiros em condições normais. |
| **33** | Corpo d'Água | **Nulo** | **0.00** | Não combustível (barreira física natural). |

---

## 5. NASA FIRMS API & INPE BDQueimadas (Detecção Térmica Orbital)

### 5.1 NASA FIRMS API (VIIRS 375m & GOES ABI)

#### Endpoints
```text
https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{WEST,SOUTH,EAST,NORTH}/{DAY_RANGE}/{DATE}
```

*   **`MAP_KEY`**: Chave pessoal de 32 caracteres gerada gratuitamente no cadastro da NASA.
*   **Aviso de Descontinuação do Satélite Suomi NPP**:
    > [!IMPORTANT]
    > Em **02 de novembro de 2026**, a NASA encerrou formalmente as operações do sensor VIIRS a bordo do satélite Suomi NPP. O pipeline de ingestão do SIRDA utiliza exclusivamente:
    > - `VIIRS_NOAA20_NRT` (resolução espacial de 375m no nadir).
    > - `VIIRS_NOAA21_NRT` (resolução espacial de 375m no nadir).

#### Exemplo de Requisição REST via `cURL`:
```bash
curl -X GET "https://firms.modaps.eosdis.nasa.gov/api/area/csv/SEU_MAP_KEY_32_CHARS/VIIRS_NOAA21_NRT/-53.0,-25.0,-39.0,-14.0/1/2026-11-08" \
     -o focos_viirs_noaa21.csv
```

---

### 5.2 INPE BDQueimadas (Stream Quase-Tempo-Real e Dump Diário)

*   **Arquivo Diário Nacional (CSV)**:
    `https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/focos_diario_br_{YYYYMMDD}.csv`
*   **Stream Quase-Tempo-Real (10 minutos)**:
    `https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/10min/`
*   **Eventos Agrupados (GeoPackage)**:
    `https://dataserver-coids.inpe.br/queimadas/queimadas/eventos/ativos/eventos_ativos.gpkg`

---

## 6. Próximos Passos de Integração no Código

1.  **Implementação do Conector ONS**: Incorporar a classe `OnsOpenDataExtractor` em `src/bronze/extractors/` usando `pyarrow` e `duckdb`.
2.  **Módulo de Clima**: Construir o conector `OpenMeteoExtractor` com cache de requisições local e suporte aos vetores horários de vento a 10m.
3.  **Contratos de Borda**: Instanciar os schemas Pydantic v2 correspondentes sob `src/core/domain/`.
