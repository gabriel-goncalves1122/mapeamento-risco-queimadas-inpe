# 05. Ameaça Energética

## Conceito
O módulo de Ameaça Energética modela o risco que incêndios florestais representam para o Sistema Interligado Nacional (SIN), operado pelo ONS. O sistema combina três camadas de análise: (1) classificação estática das dimensões (tensão, capacidade, criticidade), (2) índices dinâmicos de ameaça em tempo real baseados em FRP e distância, e (3) análise topológica de grafos (*Betweenness Centrality* via NetworkX) para identificar quais subestações, se destruídas, causariam os piores Efeitos Cascata na rede.

## Classificação Estática das Dimensões

### Classificação de Subestações
A classificação das subestações é baseada em sua capacidade (em MW) e determina tanto a classe de capacidade quanto a criticidade intrínseca da infraestrutura.

**Capacidade:**

| MW | Classe |
|---|---|
| $\ge$ 2000 | `EXTREMA` |
| $\ge$ 1000 | `MUITO_ALTA` |
| $\ge$ 300 | `ALTA` |
| $\ge$ 100 | `MEDIA` |
| < 100 | `BAIXA` |

**Criticidade:**

| MW | Classe |
|---|---|
| $\ge$ 1000 | `CRITICA` |
| $\ge$ 300 | `ALTA` |
| $\ge$ 100 | `MEDIA` |
| < 100 | `BAIXA` |

```python
def _classificar_capacidade(self, capacidade_mw):
    if capacidade_mw is None or capacidade_mw <= 0: return "NAO_INFORMADA"
    if capacidade_mw >= 2000: return "EXTREMA"
    if capacidade_mw >= 1000: return "MUITO_ALTA"
    if capacidade_mw >= 300: return "ALTA"
    return "MEDIA" if capacidade_mw >= 100 else "BAIXA"

def _classificar_criticidade(self, capacidade_mw):
    if capacidade_mw is None or capacidade_mw <= 0: return "NAO_INFORMADA"
    if capacidade_mw >= 1000: return "CRITICA"
    if capacidade_mw >= 300: return "ALTA"
    return "MEDIA" if capacidade_mw >= 100 else "BAIXA"
```

### Classificação de Linhas de Transmissão
As linhas de transmissão são classificadas por sua tensão (kV) e extensão (km), e sua criticidade deriva de uma combinação de ambos os fatores.

**Tensão:**

| kV | Classe |
|---|---|
| $\ge$ 500 | `EXTRA_ALTA` |
| $\ge$ 230 | `ALTA` |
| $\ge$ 69 | `MEDIA` |
| < 69 | `BAIXA` |

**Extensão:**

| km | Classe |
|---|---|
| $\ge$ 200 | `MUITO_LONGA` |
| $\ge$ 50 | `LONGA` |
| $\ge$ 10 | `MEDIA` |
| < 10 | `CURTA` |

**Criticidade da Linha:**

| Critério | Classe |
|---|---|
| $\ge$ 500 kV | `CRITICA` |
| $\ge$ 230 kV AND $\ge$ 50 km | `ALTA` |
| $\ge$ 230 kV | `MEDIA_ALTA` |
| $\ge$ 69 kV | `MEDIA` |
| < 69 kV | `BAIXA` |

```python
def _classificar_tensao(self, tensao_kv):
    if tensao_kv >= 500: return "EXTRA_ALTA"
    if tensao_kv >= 230: return "ALTA"
    if tensao_kv >= 69: return "MEDIA"
    return "BAIXA" if tensao_kv > 0 else "NAO_INFORMADO"

def _classificar_extensao(self, extensao_km):
    if extensao_km >= 200: return "MUITO_LONGA"
    if extensao_km >= 50: return "LONGA"
    if extensao_km >= 10: return "MEDIA"
    return "CURTA" if extensao_km > 0 else "NAO_INFORMADA"

def _classificar_criticidade_linha(self, tensao_kv, extensao_km):
    if tensao_kv >= 500: return "CRITICA"
    if tensao_kv >= 230 and extensao_km >= 50: return "ALTA"
    if tensao_kv >= 230: return "MEDIA_ALTA"
    if tensao_kv >= 69: return "MEDIA"
    return "BAIXA" if tensao_kv > 0 else "NAO_INFORMADA"
```

### Sistemas Isolados ONS
```python
def _classificar_regiao_eletrica(self, estado_sigla):
    if estado_sigla in {"AC", "AM", "AP", "MA", "MT", "PA", "RO", "RR", "TO"}: return "AMAZONIA_LEGAL"
    return "NAO_INFORMADA" if estado_sigla == "NI" else "OUTRAS_REGIOES"

def _classificar_prioridade_sistema(self, estado_sigla):
    if estado_sigla in {"AM", "PA", "AC", "AP", "RO", "RR"}: return "ALTA_PRIORIDADE"
    if estado_sigla in {"MT", "MA", "TO"}: return "MEDIA_PRIORIDADE"
    return "NAO_INFORMADA" if estado_sigla == "NI" else "BAIXA_PRIORIDADE"
```

## Índices de Ameaça Dinâmica

As fórmulas de ameaça dinâmica calculam o impacto potencial em tempo real de focos de incêndio sobre os ativos energéticos. Elas consideram a energia radiativa do fogo (FRP), o risco meteorológico, as características do ativo e a distância até ele.

**Ameaça à Linha:**
$$ \text{ameaça}_{linha} = \frac{FRP \times (1 + risco) \times \ln(\text{tensão}_{kV} + 1)}{\max(\text{dist}_{linha_{km}}, 0.1)} $$

**Ameaça à Subestação:**
$$ \text{ameaça}_{subestação} = \frac{FRP \times (1 + risco) \times \ln(\text{capacidade}_{MW} + 1)}{\max(\text{dist}_{sub_{km}}, 0.1)} $$

**Ameaça ao Sistema Isolado:**
$$ \text{ameaça}_{sistema} = \frac{FRP \times (1 + risco)}{\max(\text{dist}_{sis_{km}}, 0.1)} $$

> [!NOTE]
> As fórmulas para linha e subestação incluem um peso logarítmico da importância do ativo (tensão ou capacidade). Isso significa que um incêndio próximo a uma linha de 500kV resulta em um *score* de ameaça superior ao mesmo incêndio ocorrendo próximo a uma linha de 69kV.

## Betweenness Centrality e Risco de Cascata

Para avaliar a importância topológica de cada subestação no grafo de transmissão nacional, utilizamos a métrica de *Betweenness Centrality*.

**Algoritmo:**
1. Constrói-se uma KDTree (`scipy.spatial.cKDTree`) das coordenadas de todas as subestações.
2. Para cada Linha de Transmissão, extraem-se os *endpoints* (início e fim da `LineString`).
3. Cada *endpoint* é associado à subestação mais próxima (threshold: $\approx 0.05^\circ \approx 5\text{km}$).
4. Se os *endpoints* apontam para subestações distintas, uma aresta $(u,v)$ é adicionada ao grafo.
5. Calcula-se `networkx.betweenness_centrality(G)`: a fração de todos os caminhos mais curtos que passam por cada nó.

$$ C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}} $$

6. O *score* é normalizado para a escala de 0-100:

$$ \text{score}_{norm} = \frac{score}{\max(score)} \times 100 $$

**Classificação de Risco de Cascata:**

| Score Normalizado | Classe | Significado |
|---|---|---|
| $\ge$ 80 | `EXTREMO` | Destruição causa blackout inter-regional |
| $\ge$ 50 | `ALTO` | Sobrecarga severa em rotas alternativas |
| $\ge$ 20 | `MEDIO` | Impacto significativo mas contornável |
| > 0 | `BAIXO` | Impacto localizado |
| 0 | `ISOLADO` | Nó não pertence ao grafo principal |

```python
def classify_cascade_risk(score):
    if score >= 80: return "EXTREMO"
    if score >= 50: return "ALTO"
    if score >= 20: return "MEDIO"
    if score > 0: return "BAIXO"
    return "ISOLADO"
```

## Consultas SQL de Ameaça

**Ameaça a Subestações:**
```sql
SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_subestacao, 'subestacao_nome') as nome_subestacao,
  CAST(LOOKUP(f.fk_subestacao, 'subestacao_capacidade') AS FLOAT) as capacidade_mw,
  LOOKUP(f.fk_subestacao, 'subestacao_risco_cascata') as risco_cascata,
  CAST(LOOKUP(f.fk_subestacao, 'subestacao_betweenness') AS FLOAT) as betweenness_score,
  f.total_focos,
  f.indice_ameaca_subestacao
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_ameaca_subestacao > 0
ORDER BY f.indice_ameaca_subestacao DESC
LIMIT 50;
```

**Risco de Apagão em Linhas:**
```sql
SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_linha_transmissao, 'linha_nome') as nome_linha,
  CAST(LOOKUP(f.fk_linha_transmissao, 'linha_tensao') AS FLOAT) as tensao_kv,
  LOOKUP(f.fk_linha_transmissao, 'linha_uf') as uf_linha,
  f.total_focos,
  f.indice_ameaca_linha
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_ameaca_linha > 0
ORDER BY f.indice_ameaca_linha DESC
LIMIT 50;
```

## Interpretação Operacional

Quando a SE Rio Verde Norte (Betweenness 100.00, Risco EXTREMO) aparece sob ameaça de incêndio, significa que a destruição dessa "ponte" cortaria o fluxo Norte $\rightarrow$ Centro-Oeste $\rightarrow$ Sudeste. A energia seria forçada a buscar caminhos alternativos mais longos, sobrecarregando linhas secundárias e disparando o ERAC (Esquema Regional de Alívio de Carga).

## Arquivos Fonte

- [etl_dim_ons_subestacoes.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/etl_dimensions/etl_dim_ons_subestacoes.py)
- [etl_dim_ons_linhas_transmissao.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/etl_dimensions/etl_dim_ons_linhas_transmissao.py)
- [etl_dim_ons_sistemas_isolados.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/etl_dimensions/etl_dim_ons_sistemas_isolados.py)
- [calculators.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/streaming_processing/processors/calculators.py)
- [network_builder.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/gold/src/science/networkx/network_builder.py)
