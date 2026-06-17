# Ciência de Redes Aplicada ao Sistema Interligado Nacional (SIN)

A robustez da matriz energética não repousa apenas em atributos individuais das subestações, mas na malha topológica estrita de transmissão e interdependência. O roteamento dinâmico estabelece que a vulnerabilidade de um nodo elétrico é proporcional à sua dominância no escoamento global de cargas na rede.

## 1. Abordagem Metodológica
O script analítico `src/etl/pipelines/network_builder.py` executa a montagem matemática do grafo do SIN por meio dos seguintes rigores axiomáticos:

1. **Cruzamento Topológico**: Empregou-se Árvores K-Dimensionais (`scipy.spatial.cKDTree`) para avaliar intersecções espaciais contíguas entre as hastes de Linhas de Transmissão (Arestas/Edges) e os pontos focais de Subestações (Nodos/Nodes).
2. **Grafo Matemático**: Uma vez extraída a matriz de adjacência geofísica, instanciou-se um modelo não-direcionado sobre a biblioteca `NetworkX`.

## 2. Modelagem de Risco via Betweenness Centrality
Ao invés de quantificar risco elétrico unicamente pela tensão do eixo (kV) ou potência instalada (MW), o modelo computa a **Centralidade de Intermediação (Betweenness Centrality)** de todas as subestações nacionais:

`$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$`

Onde `\sigma_{st}` representa a somatória dos caminhos mais curtos entre a origem `s` e o destino `t`, e `\sigma_{st}(v)` determina os caminhos que perpassam imperativamente pelo nó `v`. 

O resultado final é normalizado em uma distribuição escalar de `0` a `100`, revelando os gargalos intrínsecos estruturais (e.g., *Subestação Rio Verde Norte*). Um sinistro geofísico (fogo florestal) adjacente a nodos de elevado *score* ativa *flags* analíticas de Risco de Colapso em Cascata (*Cascade Failure Risk*) iminente.
