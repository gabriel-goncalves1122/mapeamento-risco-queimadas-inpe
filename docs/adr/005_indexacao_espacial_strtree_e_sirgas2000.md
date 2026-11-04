# ADR 005: Indexação Espacial Vetorial (STRtree) e Reprojeção SIRGAS 2000

* **Status:** Aprovado
* **Data:** 2026-10-25
* **Decisores:** Engenharia de Dados CCO-DataOps

---

## 1. Contexto

O enriquecimento de focos de queimada exige cruzar simultaneamente coordenadas pontuais de anomalias térmicas contra 7 camadas de infraestruturas críticas:
* 5.564 municípios (polígonos detalhados);
* Mais de 600 Terras Indígenas (polígonos extensos e complexos);
* Centenas de milhares de quilômetros de Linhas de Transmissão e Rodovias Federais (`LineStrings`);
* Milhares de Subestações e Estabelecimentos Hospitalares do CNES (`Points`).

Abordagens ingênuas (como iteração linha a linha ou loops aninhados $O(N \times M)$) tornavam a latência de processamento impraticável para streaming de tempo real ($> 10\text{ segundos}$ por micro-batch). Além disso, calcular distâncias em graus decimais WGS84 (`EPSG:4326`) gera erros inaceitáveis de escala métrica devido à curvatura da Terra e convergência dos meridianos.

---

## 2. Decisão

Implementar o **Motor Espacial de Alta Performance (`MotorEspacial`)** na Camada Silver baseado em duas decisões fundamentais:

1. **Reprojeção Métrica Oficial Brasileira**:
   - Todas as geometrias vetoriais são convertidas para o sistema de projeção cartográfica **SIRGAS 2000 Brasil Policônica (`EPSG:5880`)**.
   - As distâncias euclidianas são calculadas com exatidão geodésica em metros/quilômetros, eliminando distorções de graus decimais.
2. **Indexação Espacial Vetorial (*STRtree*)**:
   - As geometrias de cada camada são carregadas em árvores espaciais R-Tree baseadas no algoritmo *Sort-Tile-Recursive* (`shapely.strtree.STRtree`).
   - A complexidade de busca do vizinho mais próximo (*Nearest Neighbor*) e consultas de interseção ponto-polígono (*Point-in-Polygon*) é reduzida de linear $O(N)$ para **ordem logarítmica $O(\log N)$**.
3. **Pré-construção de Buffers Métricos**:
   - As faixas de servidão de linhas de transmissão (buffers de 3 km e 10 km) e zonas de amortecimento de Terras Indígenas são pré-calculadas e cacheadas em memória na inicialização do serviço.

---

## 3. Consequências

### Positivas
* **Throughput Extremo**: O enriquecimento espacial atômico de cada foco de queimada é executado em **$< 2\text{ milissegundos}$**.
* **Precisão Tática**: As distâncias em quilômetros até hospitais, subestações e rodovias refletem a geografia real do território brasileiro.

### Negativas / Trade-offs
* O tempo de inicialização (*cold start*) do `MotorEspacial` consome aproximadamente 5 a 10 segundos para carregar as 7 camadas e indexar as árvores em memória RAM.
