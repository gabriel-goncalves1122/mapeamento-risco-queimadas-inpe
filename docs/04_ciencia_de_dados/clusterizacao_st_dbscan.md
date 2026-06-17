# Clusterização de Densidade Espaço-Temporal: ST-DBSCAN

Uma detecção satelital isolada de calor constitui um mero *pixel quente* com baixa acurácia contextual. Incêndios florestais reais propagam-se ativamente por ecossistemas sob a influência de vetores estocásticos (vento, relevo e biomassa). Destarte, a análise puramente estática das ocorrências não mapeia a propagação física de tais fenômenos.

## 1. O Algoritmo ST-DBSCAN
O *Spatio-Temporal Density-Based Spatial Clustering of Applications with Noise* (ST-DBSCAN) atua como um heurístico não-supervisionado. O módulo `st_dbscan_clustering.py` importa o construto DBSCAN tradicional do `scikit-learn` submetendo a matriz de entrada a uma penalidade euclidiana modificada nos tensores `X`, `Y` e `Tempo`.

- **Transformação de Domínio Temporal**: O vetor de *timestamp* dos eventos sofre normalização para garantir correlação escalar com a distância radial (Latitude/Longitude). Dessa forma, eventos distantes geometricamente em 2km recebem peso similar a eventos distantes 2 dias no tempo da detecção.
- **Vizinhança Condicional (Eps/MinPts)**: Se pontos térmicos coalescem simultaneamente no espaço limite de `Eps = 0.02` e sobrevivem na linha do tempo adjacente por múltiplos dias, eles tornam-se parte de um `Cluster Único Dinâmico`.

## 2. Geração da Entidade Poligonal Geométrica (Convex Hull)
Após o rastreio contínuo e a mitigação estatística de falsos positivos (Ruídos com `Label = -1`), os *clusters* processados (compostos amiúde por milhares de pontos em ignição contínua) são convertidos em Polígonos de Área Queimada por envoltórias complexas (*Convex Hulls*) operadas pela biblioteca `geopandas`.

Os registros, doravante agrupados por evento global de Fogo (`fire_event_id`), expõem vetores críticos de pesquisa macroscópica (e.g., área de devastação final, duração contínua em dias da ocorrência, somatória radiativa convectiva da queima), extrapolando a restrição de "pontos discretos no mapa" e conferindo rigor analítico ao rastreamento espacial avançado de desastres climáticos.
