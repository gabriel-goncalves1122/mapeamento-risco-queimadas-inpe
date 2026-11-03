# Dicionário de Dados - Camada Gold (Facts & Metrics)

A Camada Gold (Ouro) consolida os fluxos analíticos e operacionais do projeto. Nela residem os eventos observacionais atômicos (ingestão contínua Kafka) e os macroeventos espaço-temporais calculados via algoritmo ST-DBSCAN com análise de impacto em infraestruturas críticas.

**Regra Arquitetural da Camada Gold**: As Tabelas Fato contêm **estritamente** Identificadores de Dimensão (FKs), Métricas Quantitativas (valores físicos e geográficos contínuos), Categorias Degeneradas padronizadas e Chaves Temporais (`ISO 8601`). Strings textuais descritivas ou decorativas (como nomes de municípios, nomes de hospitais ou descrições de linhas) são terminantemente proibidas no payload de streaming. No Apache Druid e Apache Superset, essas strings são resolvidas em tempo de consulta através de *Lookups* indexados nas tabelas de dimensão Silver, preservando banda de rede e performance de agregação.

Ambas as tabelas fato possuem contratos Pydantic estritos com `extra="forbid"` em `src/core/domain/`:
- `FocoFatoPayload` em `src/core/domain/foco_fato_payload.py`
- `EventoFatoPayload` em `src/core/domain/evento_fato_payload.py`

---

## 1. Tabela Fato: `FATO_FOCOS_INCENDIO`
- **Contrato Pydantic**: [`FocoFatoPayload`](../../src/core/domain/foco_fato_payload.py)
- **Tópico Kafka**: `focos-incendio`
- **Datasource Druid**: `fato_focos_incendio`
- **Granularidade**: Registro atômico de detecção por pixel de satélite (1 foco observacional).

| Campo | Tipo | Nullable | Descrição Técnica e Regra de Domínio |
|---|---|:---:|---|
| `data_hora` | String (ISO-8601) | Não | Timestamp exato da detecção do sensor orbital. Mapeado para a partição temporal `__time` no Apache Druid. |
| `pais_origem` | String | Não | País de abrangência da medição (`Brasil`). |
| `fk_bioma` | String | Não | Identificador do bioma (ex: `Cerrado`, `Amazonia`, `Mata Atlantica`). |
| `fk_satelite_sensor` | String | Não | Identificador do satélite/sensor de sensoriamento remoto (ex: `AQUA_M-T`, `TERRA_M-T`, `NOAA-20`). |
| `fk_municipio` | String | Não | Código IBGE (7 dígitos) do município de ocorrência do foco. Join com `dim_municipios_coordenadas`. |
| `fk_municipio_espacial` | String | Não | Código IBGE validado via junção espacial exata (Polígono IBGE). Join com `dim_municipios_coordenadas`. |
| `fk_terra_indigena` | String | Não | Código FUNAI caso o foco esteja contido no interior de uma TI; caso contrário string vazia ou `"0"`. Join com `dim_terras_indigenas`. |
| `fk_terra_indigena_proxima` | String | Não | Código FUNAI da Terra Indígena com menor distância euclidiana ao foco. Join com `dim_terras_indigenas`. |
| `fk_trecho_rodoviario` | String | Não | Código identificador do trecho rodoviário federal DNIT mais próximo. Join com `dim_rodovias_federais`. |
| `fk_linha_transmissao` | String | Não | Código da Linha de Transmissão ONS mais próxima. Join com `dim_ons_linhas_transmissao`. |
| `fk_subestacao` | String | Não | Código da Subestação ONS mais próxima. Join com `dim_ons_subestacoes`. |
| `fk_sistema_isolado` | String | Não | Código da localidade de Sistema Isolado ONS mais próxima. Join com `dim_ons_sistemas_isolados`. |
| `fk_hospital_proximo` | String | Não | Código CNES do estabelecimento hospitalar mais próximo. Join com `dim_hospitais_cnes`. |
| `latitude` | Float | Sim | Coordenada Y WGS84 (`EPSG:4326`) informada pelo INPE. |
| `longitude` | Float | Sim | Coordenada X WGS84 (`EPSG:4326`) informada pelo INPE. |
| `coordenada_valida` | Integer | Não | Flag binária (`1` para coordenadas dentro dos limites territoriais do Brasil, `0` caso contrário). |
| `foco_point` | String (WKT) | Não | Ponto geométrico textual WKT (`POINT(lon lat)`). |
| `dias_sem_chuva` | Float | Sim | Quantidade de dias consecutivos sem precipitação pluviométrica no pixel. |
| `precipitacao_mm` | Float | Sim | Precipitação acumulada em milímetros registrada pelo satélite meteorológico. |
| `risco_fogo_inpe` | Float | Sim | Índice oficial de risco de fogo calculado pelo INPE (escala contínua de 0.0 a 1.0). |
| `potencia_radiativa_fogo` | Float | Sim | FRP (*Fire Radiative Power*) em Megawatts (MW). Mede a intensidade energética instantânea do fogo. |
| `indice_condicao_ambiental` | Float | Sim | Métrica ponderada de vulnerabilidade climática local (dias sem chuva, seca e risco). |
| `indice_queimada_evento` | Float | Sim | Indicador unificado de severidade do foco atômico. |
| `distancia_rodovia_km` | Float | Sim | Menor distância euclidiana calculada em projeção métrica SIRGAS 2000 (`EPSG:5880`) até a rodovia mais próxima. |
| `distancia_linha_km` | Float | Sim | Menor distância euclidiana (km) até a linha de transmissão do SIN (ONS). |
| `distancia_subestacao_km` | Float | Sim | Menor distância euclidiana (km) até a subestação do SIN (ONS). |
| `distancia_sistema_isolado_km` | Float | Sim | Menor distância euclidiana (km) até o sistema elétrico isolado mais próximo. |
| `distancia_hospital_km` | Float | Sim | Menor distância euclidiana (km) até o hospital CNES com leitos ou UTI mais próximo. |
| `distancia_terra_indigena_km` | Float | Sim | Menor distância euclidiana (km) até a fronteira da Terra Indígena mais próxima. |

---

## 2. Tabela Fato: `FATO_EVENTOS_INCENDIO`
- **Contrato Pydantic**: [`EventoFatoPayload`](../../src/core/domain/evento_fato_payload.py)
- **Tópico Kafka**: `eventos-incendio`
- **Datasource Druid**: `fato_eventos_incendio`
- **Granularidade**: Macroevento espaço-temporal clusterizado via ST-DBSCAN (agrupa múltiplos focos atômicos correlacionados no espaço e tempo).

| Campo | Tipo | Nullable | Descrição Técnica e Regra de Domínio |
|---|---|:---:|---|
| `fire_event_id` | String (UUID/Hash) | Não | Identificador determinístico único do evento clusterizado (ex: `EVT_202409_00123`). |
| `data_inicio` | String (ISO-8601) | Não | Timestamp do foco mais antigo pertencente ao cluster. Mapeado para `__time` no Druid. |
| `data_fim` | String (ISO-8601) | Não | Timestamp do foco mais recente pertencente ao cluster. |
| `pais_origem` | String | Não | País de abrangência da medição (`Brasil`). |
| `fk_bioma` | String | Não | Bioma predominante da área geográfica do evento. |
| `fk_satelite_sensor` | String | Não | Conjunto ou sensor predominante nas detecções do cluster. |
| `fk_municipio_principal` | String | Não | Código IBGE do município com maior incidência de focos ou área no evento. Join com `dim_municipios_coordenadas`. |
| `codigos_ibge_interceptados` | Array[String] | Não | Lista serializada em JSON dos códigos IBGE de todos os municípios interceptados pelo polígono do evento. |
| `qtd_municipios_interceptados` | Integer | Não | Contagem escalar de municípios interceptados pelo evento. |
| `fk_terra_indigena` | String | Não | Código FUNAI caso o evento sobreponha território indígena demarcado. Join com `dim_terras_indigenas`. |
| `codigos_ti_interceptadas` | Array[String] | Não | Lista serializada em JSON dos códigos FUNAI de todas as TIs interceptadas. |
| `qtd_terras_indigenas_interceptadas`| Integer | Não | Contagem de Terras Indígenas interceptadas pelo evento. |
| `fk_terra_indigena_proxima` | String | Não | Código FUNAI da TI mais próxima da borda do evento. |
| `fk_trecho_rodoviario` | String | Não | Código do trecho rodoviário sob maior proximidade ou ameaça. |
| `fk_linha_transmissao` | String | Não | Código da linha de transmissão ONS sob maior proximidade ou risco de contingência. |
| `fk_subestacao` | String | Não | Código da subestação ONS sob maior risco ou proximidade. |
| `fk_sistema_isolado` | String | Não | Código do sistema isolado sob risco. |
| `fk_hospital` | String | Não | Código CNES da unidade hospitalar de referência sob risco de pressão respiratória. |
| `latitude_centroide` | Float | Não | Latitude WGS84 ponderada do baricentro de calor do evento. |
| `longitude_centroide` | Float | Não | Longitude WGS84 ponderada do baricentro de calor do evento. |
| `path_json` | String (JSON Geo) | Não | Lista de anéis de polígono (Convex Hull ou Buffer) formatada para exibição no deck.gl / Superset Polygon Chart. |
| `total_focos` | Integer | Não | Total de focos atômicos agrupados sob este macroevento. |
| `duracao_horas` | Float | Não | Extensão temporal do incêndio em horas (`(data_fim - data_inicio)`). |
| `duracao_dias` | Float | Não | Extensão temporal do incêndio em dias fracionários. |
| `area_evento_km2` | Float | Não | Área calculada do envelope poligonal em projeção métrica SIRGAS 2000 (`km²`). |
| `soma_frp` | Float | Não | Somatório total do FRP (Megawatts) de todos os focos do cluster. |
| `media_frp` | Float | Não | Média aritmética do FRP (MW) do evento. |
| `max_frp` | Float | Não | Pico instantâneo de FRP (MW) registrado em qualquer foco do evento. |
| `media_risco_fogo` | Float | Não | Média do risco de fogo INPE nos focos associados. |
| `max_risco_fogo` | Float | Não | Maior risco de fogo pontual dentro do evento. |
| `media_dias_sem_chuva` | Float | Não | Média de dias de estiagem na mancha do evento. |
| `media_precipitacao_mm` | Float | Não | Média de chuva pluviométrica na mancha do evento. |
| `indice_condicao_ambiental_medio` | Float | Não | Média do índice composto de condição ambiental. |
| `indice_queimada_evento_medio` | Float | Não | Média do índice de severidade de queimada dos pontos. |
| `indice_queimada_evento_max` | Float | Não | Máxima severidade registrada no evento. |
| `distancia_rodovia_km` | Float | Sim | Distância métrica euclidiana da borda do polígono até a rodovia mais próxima. |
| `distancia_linha_km` | Float | Sim | Distância métrica euclidiana da borda do polígono até a linha ONS mais próxima. |
| `distancia_subestacao_km` | Float | Sim | Distância métrica euclidiana da borda do polígono até a subestação ONS mais próxima. |
| `distancia_sistema_isolado_km` | Float | Sim | Distância métrica euclidiana até a rede isolada mais próxima. |
| `distancia_hospital_km` | Float | Sim | Distância métrica euclidiana até a unidade hospitalar mais próxima. |
| `distancia_terra_indigena_km` | Float | Sim | Distância métrica euclidiana até a Terra Indígena mais próxima. |
| `indice_ameaca_rodovia` | Float | Não | Métrica combinada de FRP, área e proximidade à malha viária DNIT. |
| `indice_ameaca_linha` | Float | Não | Métrica combinada de FRP, área e proximidade às Linhas de Transmissão SIN (ONS). |
| `indice_ameaca_subestacao` | Float | Não | Métrica combinada de FRP e proximidade a subestações ONS. |
| `indice_ameaca_sistema_isolado` | Float | Não | Métrica de criticidade para atendimento elétrico isolado. |
| `indice_pressao_saude` | Float | Não | Risco de sobrecarga hospitalar derivado de proximidade, emissão de fumaça e leitos. |
| `indice_pressao_terra_indigena`| Float | Não | Risco de impacto comunitário, ambiental e etnocultural sobre Terras Indígenas. |
| `indice_pressao_maxima` | Float | Não | Valor máximo entre os índices de pressão de infraestrutura e socioambientais. |
| `param_eps_km` | Float | Não | Hiperparâmetro espacial de raio ($\varepsilon_{km}$) utilizado no ST-DBSCAN. |
| `param_eps_dias` | Float | Não | Hiperparâmetro temporal ($\varepsilon_{dias}$) utilizado no ST-DBSCAN. |
| `param_min_samples` | Integer | Não | Número mínimo de focos exigido para formação do cluster. |
| `param_max_duration_days` | Float | Não | Janela temporal máxima de agrupamento de eventos contíguos. |

> **Validação Numérica Rígida**: O validador `rejeitar_nan_inf` do Pydantic impede terminantemente a serialização de valores `NaN`, `+Inf` ou `-Inf` nas métricas de ponto flutuante, assegurando 100% de conformidade com a especificação JSON do parser nativo do Apache Druid.
