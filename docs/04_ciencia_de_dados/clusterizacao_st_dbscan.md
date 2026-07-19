# Clusterização de Densidade Espaço-Temporal: ST-DBSCAN

Uma detecção satelital isolada de calor constitui um mero *pixel quente* com baixa acurácia contextual para a Defesa Civil. Incêndios florestais reais manifestam-se pela propagação contígua em extensos ecossistemas, regidos por vetores estocásticos (vento e relevo). Destarte, a análise agrupada em densidade física desvenda de forma precisa o real escopo das catástrofes ambientais contínuas.

## 1. A Lógica Matemática do Algoritmo ST-DBSCAN
O modelo *Spatio-Temporal Density-Based Spatial Clustering of Applications with Noise* (ST-DBSCAN) atua como um heurístico não-supervisionado (`src/science/st_dbscan_clustering.py`). Em contraposição a técnicas espaciais singulares (e.g. K-Means), o DBSCAN submete o vetor topológico a um agrupamento paramétrico em múltiplas dimensões, incluindo nativamente a linha temporal.

- **Diferencial (Espaço vs Tempo)**: Um fogo detectado no mesmo hectare no inverno e no verão deve denotar Eventos Distintos. Ao instanciar `STDBSCAN_EPS_KM` e `STDBSCAN_EPS_DIAS`, o algoritmo correlaciona explicitamente focos que coexistem espacialmente num raio restrito *E* simultaneamente numa janela cronológica exígua.
- **Vizinhança Condicional e Mitigação de Ruído**: Somente coalescências térmicas que atingem limiares críticos simultâneos em densidade (e.g. MinPts > 3) evoluem a um *Cluster* Genuíno. As demais fendas ruidosas assumem caráter isolado e recebem `Label = -1`.

## 2. Geração da Entidade Poligonal (Convex Hull)
Ao isolar de forma analítica que milhares de detecções pertencem, matematicamente, à mesma anomalia macroscópica (*Incêndio 42*), o processo transiciona para a modelagem tangível.

Bibliotecas geofísicas como a `shapely` englobam os registros dispersos usando formulações de *Convex Hull* (Envoltória Convexa). Em uma metáfora intuitiva: o cálculo constrói os limites topológicos como se "esticasse um elástico" circundando os focos periféricos mais extremos do grupo térmico, forjando uma "Mancha Contínua" validada cientificamente.

O registro, materializado por uma geometria de polígono serializada no array `path_json`, adentra o Superset evidenciando aos comandantes da mitigação climática variáveis globais imponentes: Área Devastada Total, Tempo Integral da Ocorrência e Magnitude Térmica Somada.
