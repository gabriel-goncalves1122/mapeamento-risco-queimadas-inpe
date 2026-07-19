# Ciência de Redes Aplicada ao Sistema Interligado Nacional (SIN)

A robustez da matriz energética subjaz a uma malha topológica interdependente e holística. O colapso incitado por focos térmicos massivos em hastes adjacentes incita propagação linear sob a teoria das redes complexas. Em virtude disto, uma simples contingência local é capaz de desencadear um efeito cascata catastrófico (Blackout em múltiplos estados).

## 1. Intersecção Espacial via Árvore Euclidiana
A modelagem axiomática encabeçada por `src/science/network_builder.py` constrói de forma analítica as adjacências sistêmicas que não figuram explicitamente nas dimensões normativas do Setor Elétrico.
- **Teia Eletromecânica**: As coordenadas massivas das subestações compõem e embasam uma Árvore Espacial de Consulta (`scipy.spatial.cKDTree`). Pelo rigor topológico, as extremidades desarticuladas das Linhas de Transmissão (Edges/Arestas) são associadas via varredura imediata Euclidiana às Suportes Condutores Específicos (Nodes/Nós), resultando em um Grafo Matemático Perfeito das ramificações nacionais energéticas.

## 2. Modelagem de Risco Iminente: Betweenness Centrality
O axioma analítico exclui a mera tipagem nominal de potências instaladas (MW) das subestações e incorpora como métrica suprema de vulnerabilidade sistêmica a métrica *Betweenness Centrality* (Centralidade de Intermediação).

Calculada globalmente através da biblioteca `NetworkX`, a centralidade desvenda quantas vezes uma subestação age ativamente como ponte conectiva para o tráfego nos *caminhos mais curtos* (*shortest paths*) entre todas as pontas isoladas do grafo do país.

`$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$`

Um elevado fator denota que o nodo carrega um ônus crítico inato à manutenção do Brasil Iluminado. Caso a esteira da Inteligência Geoespacial cruze a evolução temporal de um polígono de fogo destrutivo contra o raio geofísico de um desses Hubs primordiais, o Druid aciona as instâncias de Risco de Cascata (*Cascade Failure Risk*), direcionando os painéis analíticos do Superset em uma matriz global de alerta da infraestrutura nacional.
