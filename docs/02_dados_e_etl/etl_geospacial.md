# Processamento Geoespacial (ETL Batch)

Os dutos de Extração, Transformação e Carga (ETL) constituem a fundação estática sobre a qual a semântica dos dados temporais será apoiada. Tais processos lidam primariamente com objetos cartográficos oriundos de repositórios federais e estaduais, os quais manifestam alta heterogeneidade e variados Sistemas de Referência de Coordenadas (CRS).

## 1. Padronização Topológica
Os scripts hospedados em `src/etl/pipelines/` aplicam correções topológicas por meio da intersecção das bibliotecas `pandas`, `geopandas` e `shapely`. O pipeline impõe uniformidade rigorosa sobre a base vetorial através das seguintes diretrizes:

- **Projeção Cilíndrica (EPSG:4326)**: Todo polígono projetado, LineString ou ponto coordenado é submetido à reprojeção mandatória para *WGS 84* (Datum geodésico universal), viabilizando interoperabilidade espacial absoluta no momento de junção cruzada.
- **Construção de Primitivas Geométricas**:
  - `path_json`: representação primária para visualização no Superset/Deck.gl, gerada por `geometry_para_path_json`.
  - `geometria_wkt`: artefato técnico permitido somente quando necessário para reconstrução geométrica interna, como `SpatialLayer`, cálculo de proximidade e modelagem de grafos.
  - `latitude` e `longitude`: Derivativos flutuantes explícitos padronizados.

O contrato vigente separa visualização de processamento: `path_json` é o formato público para mapas e dashboards; `geometria_wkt` pode existir nas dimensões como coluna técnica, mas nunca deve entrar no payload da tabela fato de streaming.

## 2. Saneamento Semântico
A heurística de dados não admite inconsistência por valores nulos matemáticos não-intencionais (`NaN`). Métricas contínuas ausentes são interpretadas e preenchidas via processos de imputação estritos, enquanto valores literais desprovidos de registro são normalizados para variáveis latentes nulas explicitadas (e.g., `"NAO INFORMADO"`).

Essa etapa elimina artefatos que poderiam causar degradações de performance (Out-Of-Memory) no cluster Druid ao ler vetores geoespaciais defeituosos.
