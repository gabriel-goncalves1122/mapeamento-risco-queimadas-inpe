# Dicionário de Dados - Camada Silver (Dimensões Conformadas)

A **Camada Silver (Prata)** recebe os dados geográficos e tabulares brutos da Camada Bronze, resolve inconsistências espaciais, trata valores ausentes, executa cruzamentos topológicos em memória via *R-Tree* (GeoPandas) e serializa as geometrias em formato `path_json` para o Apache Druid e Apache Superset (Deck.gl).

Essas 7 tabelas de dimensão residem em `src/silver/data/dimensions/` e são carregadas nos nós do Apache Druid via mecanismos de *Lookup* para realizar *JOINs* em tempo de execução sem penalizar a performance analítica. Para entender a arquitetura de classes e o motor espacial da camada, consulte o [README da Camada Silver](README.md).

---

## Princípios de Modelagem (Camada Silver)
1. **Nulos Estritamente Tratados:** Valores nulos de texto são padronizados como `"NAO INFORMADO"`, `"DESCONHECIDO"` ou `"NI"` (UF), evitando falhas de serialização no Druid.
2. **Contrato de Geometria `path_json`:** Coordenadas complexas de polígonos e linhas são compactadas e codificadas via `PathJsonCodec` para renderização vetorial no Apache Superset.
3. **Chaves Padronizadas (PKs):** As chaves primárias são strings ou inteiros normalizados (ex: Código IBGE de 6 dígitos para cruzamento com DATASUS/CNES, código CNES de 7 dígitos, identificadores ONS).
4. **Enriquecimento Polimórfico:** Classes de dimensão herdam de `BaseETL` e `ExecutablePipelineStep`, garantindo rastreabilidade e telemetria uniforme.

---

## 1. Dimensão Municípios (`dim_municipios_coordenadas.csv`)
* **Classe Responsável:** `ETLDimMunicipios` (`src/silver/etl/etl_dim_municipios.py`)
* **Fonte:** Malha Geodésica Municipal do IBGE.
* **Descrição:** Base territorial dos 5.564 municípios brasileiros com centroides e geometrias de limite.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `codigo_ibge` | String (6 dígitos) | **Primary Key**. Código IBGE padrão sem dígito verificador (chave de join com CNES). |
| `codigo_ibge_7digitos` | String (7 dígitos) | Código IBGE oficial completo com dígito verificador. |
| `chave_localidade` | String | Chave composta normalizada (`ESTADO_MUNICIPIO`, ex: `MINAS GERAIS_ITAJUBA`). |
| `estado_nome` | String | Nome do estado por extenso em maiúsculas sem acentuação. |
| `estado_sigla` | String (2 caracteres) | Sigla da Unidade Federativa (ex: `MG`, `SP`, `TO`). |
| `regiao_brasil` | String | Macrorregião geográfica (`NORTE`, `NORDESTE`, `CENTRO-OESTE`, `SUDESTE`, `SUL`). |
| `municipios_nome` | String | Nome oficial do município normalizado para o Apache Druid. |
| `latitude` | Float | Latitude do centroide municipal. |
| `longitude` | Float | Longitude do centroide municipal. |
| `path_json` | String (JSON) | Vetor de coordenadas do polígono municipal codificado para Deck.gl. |

---

## 2. Dimensão Estabelecimentos de Saúde (`dim_hospitais_cnes.csv`)
* **Classe Responsável:** `ETLDimHospitais` (`src/silver/etl/etl_dim_hospitais.py`)
* **Fonte:** DATASUS / Cadastro Nacional de Estabelecimentos de Saúde (CNES).
* **Descrição:** Unidades hospitalares e de pronto atendimento para planejamento de evacuação e pressão respiratória.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `codigo_cnes` | String (7 dígitos) | **Primary Key**. Identificador único nacional do estabelecimento no CNES. |
| `nome_hospital` | String | Nome fantasia do estabelecimento normalizado. |
| `tipo_unidade` | String | Descrição da tipologia assistencial (ex: Hospital Geral, Pronto Socorro). |
| `categoria_unidade` | String | Categoria hierárquica (`HOSPITAL`, `URGENCIA`, `POSTO_BASICO`, `OUTROS`). |
| `tipo_unidade_critica` | String | Indicador de criticidade (`CRITICA`, `AMBULATORIAL`). |
| `categoria_atendimento` | String | Nível assistencial (`ALTA_COMPLEXIDADE`, `MEDIA_COMPLEXIDADE`, `BASICA`). |
| `classe_capacidade_saude` | String | Capacidade de suporte (`GRANDE_PORTE`, `MEDIO_PORTE`, `PEQUENO_PORTE`). |
| `funciona_24h` | String (`SIM`/`NAO`) | Indicador de operação ininterrupta. |
| `codigo_ibge` | String (6 dígitos) | Chave estrangeira para o município gestor. |
| `codigo_ti_proxima` | String | Código da Terra Indígena mais próxima (se houver). |
| `distancia_ti_km` | Float | Distância em km até o limite da Terra Indígena mais próxima. |
| `dentro_terra_indigena` | String (`SIM`/`NAO`) | Flag indicando se a unidade hospitalar situa-se dentro de território demarcado. |
| `latitude` | Float | Latitude da unidade de saúde (EPSG:4326). |
| `longitude` | Float | Longitude da unidade de saúde (EPSG:4326). |
| `path_json` | String (JSON) | Coordenada pontual codificada para visualização. |

---

## 3. Dimensão Terras Indígenas (`dim_terras_indigenas.csv`)
* **Classe Responsável:** `ETLDimTerrasIndigenas` (`src/silver/etl/etl_dim_terras_indigenas.py`)
* **Fonte:** Fundação Nacional dos Povos Indígenas (FUNAI).
* **Descrição:** Polígonos de reservas demarcadas e em estudo, com mapeamento de sobreposição municipal.
* **Caso de Estudo de Referência:** [Terra Indígena Parque do Araguaia e Aldeia Canoanã](../../docs/domain/ti_parque_araguaia_canoana.md) (1,35 milhão de hectares na Ilha do Bananal/TO, abrangendo Formoso do Araguaia, Lagoa da Confusão e Pium, coabitada pelos povos Javaé, Karajá, Avá-Canoeiro e Apyãwa).

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `codigo_ti` | String | **Primary Key**. Identificador oficial da Terra Indígena na FUNAI. |
| `nome_terra_indigena` | String | Nome oficial da demarcação (ex: `PARQUE DO ARAGUAIA`, `YANOMAMI`). |
| `etnia` | String | Povo ou etnia predominante (ex: `JAVAÉ`, `KARAJÁ`, `AVÁ-CANOEIRO`). |
| `estado_sigla` | String | Sigla do estado onde a reserva está sediada. |
| `area_hectares` | Float | Extensão territorial em hectares. |
| `classe_area_ti` | String | Porte territorial (`MUITO_GRANDE`, `GRANDE`, `MEDIA`, `PEQUENA`). |
| `estagio_regularizacao` | String | Situação jurídica (`REGULARIZADA`, `DECLARADA`, `DELIMITADA`, `EM_ESTUDO`). |
| `modalidade` | String | Modalidade de destinação da terra indígena. |
| `coordenacao_regional` | String | Unidade administrativa regional responsável da FUNAI. |
| `em_faixa_fronteira` | String (`SIM`/`NAO`) | Indicador de localização na faixa de segurança nacional de fronteira. |
| `prioridade_funai` | String | Nível de prioridade de vigilância (`ALTA_PRIORIDADE`, `MEDIA_PRIORIDADE`, `MONITORAMENTO`). |
| `codigos_ibge_interceptados` | String (Lista) | Códigos IBGE de todos os municípios sobrepostos pela TI. |
| `codigo_ibge_principal` | String (6 dígitos) | Município com maior fração de sobreposição territorial. |
| `qtd_municipios_interceptados` | Int | Quantidade total de municípios interceptados pelo polígono. |
| `percentual_area_interceptada` | Float | Proporção territorial sobreposta. |
| `latitude` | Float | Latitude do centroide da reserva. |
| `longitude` | Float | Longitude do centroide da reserva. |
| `path_json` | String (JSON) | Polígono territorial codificado para o Apache Superset. |

---

## 4. Dimensão Linhas de Transmissão ONS (`dim_ons_linhas_transmissao.csv`)
* **Classe Responsável:** `ETLDimLinhasTransmissao` (`src/silver/etl/etl_dim_ons_linhas_transmissao.py`)
* **Fonte:** ANEEL / Operador Nacional do Sistema Elétrico (ONS).
* **Descrição:** Circuitos e troncos da Rede Básica do Sistema Interligado Nacional (SIN).

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_linha_transmissao` | String | **Primary Key**. Identificador único do vão/circuito de transmissão. |
| `nome_linha` | String | Denominação operacional da linha (ex: `LT 440 kV Assis - Londrina`). |
| `tensao_kv` | Float | Nível de tensão de operação em quilovolt (kV) (ex: `500.0`, `440.0`, `230.0`). |
| `classe_tensao` | String | Faixa de tensão (`EXTRA_ALTA`, `ALTA`, `MEDIA`, `BAIXA`). |
| `extensao_km` | Float | Comprimento geodésico do circuito em quilômetros. |
| `classe_extensao` | String | Classificação de porte (`MUITO_LONGA`, `LONGA`, `MEDIA`, `CURTA`). |
| `estado_sigla_estimado` | String | Estado estimado de localização do vão. |
| `classe_criticidade_linha` | String | Índice de criticidade (`CRITICA`, `ALTA`, `MEDIA_ALTA`, `MEDIA`, `BAIXA`). |
| `latitude` | Float | Latitude do ponto médio/centroide do vão. |
| `longitude` | Float | Longitude do ponto médio/centroide do vão. |
| `path_json` | String (JSON) | Trajetória vetorial (`LineString`) codificada para renderização no Superset. |

---

## 5. Dimensão Subestações ONS (`dim_ons_subestacoes.csv`)
* **Classe Responsável:** `ETLDimSubestacoes` (`src/silver/etl/etl_dim_ons_subestacoes.py`)
* **Fonte:** ANEEL / ONS.
* **Descrição:** Nós conectores da malha elétrica de alta tensão.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_subestacao` | String | **Primary Key**. Identificador único da subestação. |
| `nome_subestacao` | String | Nome oficial da subestação (ex: `ASSIS`, `BANDEIRANTES`, `RIO VERDE NORTE`). |
| `capacidade_mw` | Float | Capacidade instalada de transformação/escoamento em Megawatts (MW). |
| `classe_capacidade` | String | Faixa de potência (`EXTREMA`, `MUITO_ALTA`, `ALTA`, `MEDIA`, `BAIXA`). |
| `criticidade_subestacao` | String | Grau de importância intrínseca (`CRITICA`, `ALTA`, `MEDIA`, `BAIXA`). |
| `agente_responsavel` | String | Concessionária de transmissão proprietária (ex: `ISA CTEEP`, `FURNAS`, `CHESF`). |
| `codigo_ibge` | String (6 dígitos) | Chave estrangeira para o município onde a instalação está situada. |
| `latitude` | Float | Latitude da subestação (EPSG:4326). |
| `longitude` | Float | Longitude da subestação (EPSG:4326). |
| `path_json` | String (JSON) | Coordenada pontual serializada para o mapa tático. |

---

## 6. Dimensão Rodovias Federais (`dim_rodovias_federais.csv`)
* **Classe Responsável:** `ETLDimRodoviasFederais` (`src/silver/etl/etl_dim_rodovias_federais.py`)
* **Fonte:** Departamento Nacional de Infraestrutura de Transportes (DNIT).
* **Descrição:** Malha rodoviária federal para análise de rotas de socorro e risco de interdição por fumaça.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_trecho_rodoviario` | String | **Primary Key**. Identificador unívoco do trecho rodoviário. |
| `codigo_rodovia` | String | Sigla da rodovia federal (ex: `BR-101`, `BR-153`, `BR-365`). |
| `jurisdicao` | String | Esfera de jurisdição (`FEDERAL`, `ESTADUAL`). |
| `classe_revestimento` | String | Condição de revestimento da pista (`PAVIMENTADA`, `NAO_PAVIMENTADA`). |
| `tipo_pavimento` | String | Tipo estrutural da superfície (ex: Asfalto, Concreto, Terra). |
| `classe_situacao_fisica` | String | Situação operacional (`DUPLICADA`, `PISTA_SIMPLES`, `EM_OBRAS`). |
| `classe_status_operacional` | String | Status de trafegabilidade (`OPERACIONAL`, `PLANEJADA`). |
| `criticidade_rodovia` | String | Risco logístico (`CRITICA`, `ALTA`, `MEDIA`, `BAIXA`). |
| `latitude` | Float | Latitude do centroide do trecho. |
| `longitude` | Float | Longitude do centroide do trecho. |
| `path_json` | String (JSON) | Trajetória vetorial do segmento de rodovia. |

---

## 7. Dimensão Sistemas Isolados ONS (`dim_ons_sistemas_isolados.csv`)
* **Classe Responsável:** `ETLDimSistemasIsolados` (`src/silver/etl/etl_dim_ons_sistemas_isolados.py`)
* **Fonte:** ONS / ANEEL.
* **Descrição:** Centros de geração e distribuição que não possuem interligação síncrona com o SIN (predominantes na Amazônia Legal).

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id_sistema_isolado` | String | **Primary Key**. Código do sistema isolado. |
| `nome_sistema_isolado` | String | Nome da localidade/sistema suprido de forma isolada. |
| `estado_sigla` | String | Estado da federação. |
| `regiao_eletrica` | String | Enquadramento elétrico (`AMAZONIA_LEGAL`, `OUTRAS_REGIOES`). |
| `prioridade_sistema_isolado` | String | Vulnerabilidade energética (`ALTA_PRIORIDADE`, `MEDIA_PRIORIDADE`, `BAIXA_PRIORIDADE`). |
| `codigo_ibge` | String (6 dígitos) | Chave estrangeira do município atendido. |
| `latitude` | Float | Latitude da usina/centro distribuidor. |
| `longitude` | Float | Longitude da usina/centro distribuidor. |
| `path_json` | String (JSON) | Coordenada pontual para Deck.gl. |
