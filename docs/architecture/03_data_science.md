# Ciência de Dados e Preditiva (A Camada Gold)

A ingestão bruta (Bronze/Prata) nos fornece satélites apontando pixels quentes e linhas elétricas cruzando o mapa. No entanto, para um tomador de decisão num CCO (Centro de Controle e Operações), 10.000 pixels soltos no mapa é apenas "ruído visual".

O ecossistema utiliza scripts avançados de Matemática e Machine Learning na Camada Gold (`pipelines/gold/src/science`) para transformar Dados Puros em **Inteligência Preditiva**.

## 1. Machine Learning: O Algoritmo ST-DBSCAN
O *Spatio-Temporal Density-Based Spatial Clustering of Applications with Noise* é a evolução do famoso DB-SCAN (Machine Learning Não-Supervisionado). 

**Por que o usamos?** 
Um incêndio florestal raramente é um "pixel isolado", mas sim uma mancha orgânica que evolui e se espalha com o vento através dos dias.
- O DB-SCAN agrupa milhares de coordenadas próximas (Fator Espacial - Raio em km) que aconteceram num período coeso de dias (Fator Temporal).
- Retiramos o ruído (outliers/falsos positivos).
- Convertemos Focos (Pixels isolados do satélite) em **Eventos**. Isso permite à Defesa Civil visualizar não apenas onde pegou fogo, mas a Área do desastre (Polygon Convex Hull) e quanto tempo durou.

## 2. Teoria dos Grafos: Risco de Cascata no ONS (NetworkX)
Temos a malha de centenas de Linhas de Transmissão de Alta Tensão da ANEEL/ONS.

**O Problema:** Se um grande incêndio florestal derreter uma linha e derrubar uma subestação de alta relevância, a energia excedente flui para as linhas vizinhas. Se as vizinhas não suportarem, temos um efeito cascata que causa apagões regionais enormes (como o de 2023).

**A Solução (NetworkX):** 
1. Mapeamos as subestações como "Nós" (Nodes) e as Linhas como "Arestas" (Edges).
2. Calculamos uma métrica de Grafos chamada *Betweenness Centrality* (Centralidade de Intermediação).
3. Isso pontua o quão vital uma subestação é para encurtar caminhos na malha nacional.
4. Ao cruzar esse "Risco de Cascata" com a proximidade dos "Eventos de Incêndio" do ST-DBSCAN, criamos uma pontuação de alerta. O Superset ranqueia imediatamente os maiores focos de incêndio com as subestações de maior criticidade, priorizando despachos de viaturas preventivas.
