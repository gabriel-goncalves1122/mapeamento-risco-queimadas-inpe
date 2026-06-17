# Modelagem Dimensional: Paradigma Snowflake

A normalização do esquema de banco de dados analítico adotado afasta-se de um modelo desnormalizado (*Wide Table* ou *Star Schema* puro) em favor de um **Esquema Floco de Neve (Snowflake)** estrito. O projeto do banco de dados prioriza a mitigação da redundância informacional e a otimização computacional no transporte de dados pela rede (Kafka).

## 1. Restrição Dimensional da Tabela Fato
A Tabela Fato principal (`FATO_FOCOS_INCENDIO`) é projetada para encapsular exclusivamente dados estocásticos e métricas contínuas. Variáveis nominais, descritivas e geolocais secundárias foram metodicamente extraídas do *payload* de evento, mitigando a entropia da informação transmitida a cada registro. 

Sua taxonomia engloba três subconjuntos vetoriais:
- **Chave de Partição Temporal**: Parâmetro `__time` mandatório no Druid para fragmentação eficiente de segmentos.
- **Chaves Estrangeiras (Foreign Keys)**: Inteiros ou strings estritas de baixo cardinalidade (e.g., `fk_municipio`, `fk_subestacao`) que apontam para tabelas-dimensão otimizadas no repositório.
- **Métricas Quantitativas**: Vetores numéricos extraídos ou derivados no instante de stream, como radiação térmica (`potencia_radiativa`), precipitação pluviométrica, e derivativos de distância euclidiana processados (`indice_ameaca_subestacao`, `distancia_linha_km`).

## 2. Resolução de Dimensões via Lookups no Apache Druid
A arquitetura baseada no Apache Druid tira proveito do recurso nativo de **Lookup Arrays** ou **Join Nodes**. A Fato recebe apenas IDs; no momento de consulta no Apache Superset, a matriz dimensional do Druid executa um JOIN vetorial contra as dimensões persistidas (Hospitais, Rodovias, Subestações), restaurando atributos textuais e propriedades geoespaciais de visualização (`path_json`, `latitude`, `longitude`) com penalidade de tempo computacional ínfima.

Quando uma etapa interna precisa recompor uma geometria Shapely/GeoPandas para cálculo de distância, interseção ou grafo, a coluna `geometria_wkt` pode ser mantida como artefato técnico de dimensão. Essa coluna não pertence ao payload da Fato Kafka/Druid.

Essa topologia reduz drásticamente a utilização de memória RAM durante a serialização no Kafka, ao mesmo tempo que mantém a integridade estrutural e tipagem estrita governada via esquemas Pydantic na camada geradora.
