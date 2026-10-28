# CCO DataOps - Spatial Context (Agent Guide)

Bem-vindo ao Motor Espacial. Responsável por agilizar o processamento vetorial geoespacial para os eventos de streaming.

## 🗺️ Regras de Sistemas de Coordenadas (CRS)
Agentes lidando com dados geográficos costumam errar sistemas de coordenadas. Respeite as leis:
1. **EPSG:4326 (Geográfico)**: Utilizado em todas as Entradas e Saídas. É o CRS padrão do mundo real, GPS e Apache Superset.
2. **EPSG:5880 (Plano/Métrico Brasil)**: Utilizado **exclusivamente** no processamento interno quando é necessário calcular distâncias contínuas (ex: "Qual a distância em KM entre o fogo e o hospital?"). Projete os pontos temporariamente para 5880, calcule a distância e depois descarte.
3. **Warnings do GeoPandas**: O GeoPandas emitirá warnings `UserWarning: Geometry is in a geographic CRS...` ao extrair o `.centroid` ou calcular `.distance` em 4326. Para centróides rápidos, este erro é ignorável e tolerado em prol da velocidade computacional (uma margem de erro pequena é aceitável para o nosso caso de uso de escala nacional). Não crie lógicas complexas de re-projeção apenas para calar este warning.

## ⚡ Regras de Performance
- O motor não pode ser um gargalo. As camadas devem fazer cache do seu GeoDataFrame internamente e devem, obrigatoriamente, montar o Spatial Index (`.sindex`).
- Ao varrer o motor de regras espaciais (`MotorEspacial.analisar_todas_ameacas`), retorne APENAS métricas contínuas e identificadores numéricos ou codes (FKs) dos recursos cruzados. Deixe a junção de Nomes e Tipos textuais para a Tabela de Dimensão correspondente no servidor OLAP.
- Novas camadas (ex: biomas, satélites) devem seguir a assinatura abstrata do `SpatialLayer` e serem injetadas no construtor do `MotorEspacial`.

## 📝 Comentários no Motor Espacial
- Comente decisões de CRS sempre que projetar entre EPSG:4326 e EPSG:5880, deixando explícito se a operação é para visualização, interseção ou distância.
- Documente o motivo de usar índice espacial, nearest ou intersects quando a escolha afetar performance ou semântica geográfica.
- Ao normalizar geometria inválida, WKT ou coordenadas, explique se o objetivo é proteger o GeoPandas, o Druid/Superset ou o cálculo vetorial.
- Evite comentários que apenas repetem chamadas Shapely/GeoPandas; o valor está em registrar a hipótese espacial.
