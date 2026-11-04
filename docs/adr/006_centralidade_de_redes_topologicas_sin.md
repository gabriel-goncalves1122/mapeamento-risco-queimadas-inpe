# ADR 006: Modelagem Topológica e Risco de Cascata no SIN via NetworkX

* **Status:** Aprovado
* **Data:** 2026-10-28
* **Decisores:** Engenharia de Dados CCO-DataOps

---

## 1. Contexto

Incêndios florestais sob linhas de transmissão causam ionização atmosférica e curtos-circuitos por efeito Joule e fuligem, forçando o desligamento de circuitos pelo Operador Nacional do Sistema Elétrico (ONS). 

No entanto, o impacto de desligar uma linha de transmissão varia dramaticamente dependendo de onde ela está inserida na malha:
* O desligamento de uma linha em um circuito anelar periférico pode causar pouca perturbação.
* O desligamento de uma linha que alimenta um tronco de alta demanda (como os ramais que alimentam a Região Metropolitana de São Paulo e centros de carga do Sudeste) pode transferir carga instantaneamente para linhas vizinhas já sobrecarregadas, desencadeando um **apagão sistêmico em cascata (contingência N-2)**.

Os dados geoespaciais brutos da ANEEL/ONS fornecem traçados de linhas e pontos de subestações desarticulados, sem uma estrutura topológica explícita de rede em grafos.

---

## 2. Decisão

Implementar o componente [`SINNetworkCentralityModel`](../../src/gold/science/networkx/network_builder.py) na Camada Gold, aplicando **Ciência de Redes Complexas** com a biblioteca **NetworkX**:

1. **Inferência de Arestas via cKDTree**:
   - As coordenadas das subestações são indexadas em uma árvore `scipy.spatial.cKDTree`.
   - As pontas inicial e final de cada linha de transmissão (`LineString`) são associadas às subestações mais próximas dentro de um limiar métrico de 0.05 graus (~5 km).
2. **Construção do Grafo do SIN**:
   - Um grafo não direcionado ponderado $G(V, E)$ é instanciado, onde $V$ são as Subestações e $E$ são as Linhas de Transmissão ponderadas pela extensão em quilômetros.
3. **Cálculo de Centralidade de Intermediação (*Betweenness Centrality*)**:
   - Mede a fração de todos os caminhos mais curtos entre pares de nós que atravessam cada subestação:
     $$g(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
4. **Normalização e Estratificação de Risco de Cascata**:
   - O score é normalizado na escala de 0 a 100:
     $$betweenness\_score\_norm = \frac{g(v)}{\max(g)} \times 100$$
   - A classificação é categorizada em 5 faixas:
     * `EXTREMO` ($S \ge 80$): Assis (SP), Rio Verde Norte (GO), Samambaia (DF), Trindade (GO), Xavantes (SP), Bandeirantes (SP).
     * `ALTO` ($50 \le S < 80$): Londrina ESU (PR).
     * `MEDIO` ($20 \le S < 50$): Bom Jesus da Lapa II (BA), Luziânia (GO), Miracema (TO).
     * `BAIXO` ($0 < S < 20$).
     * `ISOLADO` ($S = 0$).

---

## 3. Consequências

### Positivas
* **Prevenção Operacional de Apagões**: Permite priorizar o despacho de viaturas de bombeiros para focos de calor que ameacem as subestações e linhas com maior potencial de colapso sistêmico.
* **Integração sem Custo de Runtime**: As métricas são pré-calculadas em lote na Camada Gold e disponibilizadas como *Lookups* no Druid, permitindo que consultas SQL ranqueiem o risco em milissegundos.

### Negativas / Trade-offs
* O cálculo de *Betweenness Centrality* exato tem complexidade temporal de $O(|V| \cdot |E|)$, consumindo alguns segundos durante o build da Camada Gold.
