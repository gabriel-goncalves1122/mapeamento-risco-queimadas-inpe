# 4. Catálogo Completo das Queries (Workload Base)

Este documento inventaria o conjunto exato de consultas SQL (*workload*) submetido aos nós do Apache Druid durante os testes de carga. O objetivo não é apenas listar o código, mas documentar **por que** cada agrupamento foi desenhado e qual métrica de estresse analítico ele visa capturar. 

Cada *query* pertence a uma família metodológica específica, desenhada para medir os limites verticais ou horizontais do banco de dados (por exemplo, forçar agregação, testar leitura do sistema de arquivos, ou cruzar chaves primárias).

## O Dicionário do Workload

Ao total, foram executados ciclos englobando diversas famílias. Abaixo, estão listadas as famílias principais avaliadas no escopo do *benchmark* de dimensões:

### 1. Família: Latência Simples
**Objetivo Metodológico**: Funcionam como o "grupo de controle". Medem a latência de comunicação da rede e do roteamento interno do *Broker* até o *Historical* em consultas triviais. Se essas *queries* sofrerem oscilação ou quebra de *timeout*, significa que o gargalo estrutural é conectividade ou saturação de *thread* básica, e não complexidade da operação SQL.

- **01_latency_simple/00_count_hospitais**
  - *Datasource*: `dim_hospitais_cnes`
  - *Objetivo*: Medir latência mínima de leitura e bloqueio (*count_scan*) numa dimensão densa.
- **01_latency_simple/01_count_dimensoes_catalogo**
  - *Datasource*: `todas_dimensoes`
  - *Objetivo*: Medir a latência do planejador SQL ao processar operações `UNION ALL` entre variadas tabelas de catálogo.
- **01_latency_simple/02_filtro_hospitais_uf**
  - *Datasource*: `dim_hospitais_cnes`
  - *Objetivo*: Avaliar filtro seletivo de baixa cardinalidade (simulando que o painel filtrou apenas um Estado/UF).

### 2. Família: OLAP Pesado (Agregações)
**Objetivo Metodológico**: Simular painéis macroeconômicos no Superset, exigindo varredura completa da base de dados e agrupamento por chaves (sem *joins* ainda). Pressiona as *threads* de agregação do *Historical*.

- **02_olap_pesado/00_hospitais_groupby_multidimensional**
  - *Objetivo*: Forçar agrupamento multidimensional e `COUNT(DISTINCT)` agressivo na dimensão mais volumosa (Cnes).
- **02_olap_pesado/01_terras_indigenas_area_regularizacao**
  - *Objetivo*: Medir agrupamentos numéricos e varredura de dados tabulares (esquivando geometrias), focando em *SUM* e *AVG* em TIs.
- **02_olap_pesado/03_ons_linhas_tensao_extensao**
  - *Objetivo*: Operações de agregação numéricas sobre as linhas de transmissão, segmentadas por classificação elétrica (Média e Alta Tensão).

### 3. Família: Joins Dimensionais (O Teste de Estresse Central)
**Objetivo Metodológico**: Este é o principal indutor de erros (OOM e Timeouts) em configurações com pouca memória. O Apache Druid distribui os dados em segmentos esparsos. O *join* entre tabelas dimensionalmente grandes exige que o cluster mova chaves candidatas e aloque *Merge Buffers* custosos. 

- **03_joins_dimensionais/00_hospitais_municipios_join**
  - *Datasources*: `dim_hospitais_cnes` + `dim_municipios_coordenadas`.
  - *Objetivo*: Simula o painel de "Defesa Civil", cruzando equipamentos logísticos (hospitais) contra as geometrias limítrofes dos municípios (`left_join_groupby`).
- **03_joins_dimensionais/02_ti_municipio_principal_join**
  - *Datasources*: `dim_terras_indigenas` + `dim_municipios_coordenadas`.
  - *Objetivo*: Usar `dimension_lookup_join` para simular os filtros hierárquicos laterais do Superset (selecionar TI e retornar o município intersecionado).
- **03_joins_dimensionais/03_municipio_saude_ti_join**
  - *Datasources*: `municípios`, `hospitais`, e `TIs`.
  - *Objetivo*: *Multi-join aggregate*. A pior *query* metodológica: testa a exaustão da memória direta do *Broker* ao unir e agrupar resultados de 3 fontes primárias simultaneamente.

### 4. Família: Payload Espacial (Serialização Geo)
**Objetivo Metodológico**: Bancos de dados tradicionais quebram ao transportar GeoJSONs densos (Milhões de pontos, multipolígonos gigantes) do disco para a memória e da memória para a placa de rede do cliente. Essa família mensura a capacidade do canal HTTP do Druid.

- **04_payload_espacial/00_path_json_municipios** (e equivalentes de TIs/Rodovias)
  - *Objetivo*: Solicitar via `SELECT` o retorno da coluna que contém a *String* serializada pesada (`path_json`), atestando que os *arrays* não sofrem truncamento nem derrubam a latência de transferência para o cliente (Superset renderizando mapas vectoriais brutos).

## O Impacto Teórico do Catálogo
Para testar a infraestrutura de forma holística, a execução desse catálogo ocorre de maneira rotativa durante os ciclos. Ao misturar requisições levíssimas (`COUNT`) com requisições devastadoras (`Multi-joins`), induz-se concorrência assimétrica. O *Broker* é forçado a gerir enfileiramento: queries curtas aguardando *buffers* ocupados pelas longas. O *hardware* ideal (*Query Heavy*) é o único esperado a escoar as *queries* simples mesmo enquanto os grandes agrupamentos ocupam a JVM.
