# Processamento Geoespacial (ETL Batch)

Os dutos de Extração, Transformação e Carga (ETL) constituem a fundação estática sobre a qual a semântica dos dados temporais será apoiada. Tais processos lidam primariamente com objetos cartográficos oriundos de repositórios federais e estaduais, os quais manifestam alta heterogeneidade e variados Sistemas de Referência de Coordenadas (CRS).

## 1. Padronização Topológica
Os scripts hospedados em `src/etl/pipelines/` aplicam correções topológicas por meio da intersecção das bibliotecas `pandas`, `geopandas` e `shapely`. O pipeline impõe uniformidade rigorosa sobre a base vetorial através das seguintes diretrizes:

- **Processamento Vetorizado em C**: Evitamos laços iterativos (`for loops` no Python puro) que analisariam linha a linha. Ao invés disso, o uso do `GeoPandas` permite aplicar transformações em matrizes inteiras simultaneamente. Esta abordagem matricial otimizada garante escalabilidade na extração massiva.
- **Projeção Cilíndrica (EPSG:4326)**: Todo polígono projetado, LineString ou ponto coordenado é submetido à reprojeção mandatória para *WGS 84* (Datum geodésico universal), viabilizando interoperabilidade espacial absoluta no momento de junção cruzada.
- **Construção de Primitivas Geométricas**:
  - `path_json`: A conversão obrigatória da matemática complexa do `Shapely` num texto `path_json` leve (`[[-45.1, -22.2]]`) é fundamental. Isso preserva a integridade topológica para visualização no Superset/Deck.gl e viabiliza a reconstrução interna sem sobrecarregar a memória RAM do Druid com strings geométricas pesadas e difíceis de parsear.
  - `latitude` e `longitude`: Derivativos flutuantes explícitos padronizados.

O contrato vigente elimina WKT dos CSVs destinados ao Druid: `path_json` é o formato público para mapas, dashboards e reconstrução interna. Se uma etapa futura precisar preservar topologia perfeita, o artefato deve viver fora do Druid, em formato geoespacial próprio.

## 2. Saneamento Semântico
A heurística de dados não admite inconsistência por valores nulos matemáticos não-intencionais (`NaN`). Métricas contínuas ausentes são interpretadas e preenchidas via processos de imputação estritos, enquanto valores literais desprovidos de registro são normalizados para variáveis latentes nulas explicitadas (e.g., `"NAO INFORMADO"`).

Essa etapa atua como um escudo profilático: elimina artefatos corrompidos antes da indexação, prevenindo degradações de performance severas ou interrupções (*Out-Of-Memory*) no cluster analítico final durante as varreduras geoespaciais em larga escala.
