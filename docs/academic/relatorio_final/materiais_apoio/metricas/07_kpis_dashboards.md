# 07. KPIs e Dashboards Operacionais

## Conceito

Os KPIs (Key Performance Indicators) dos dashboards do Apache Superset representam as métricas agregadas finais que são consumidas pelos operadores de Defesa Civil, ONS, FUNAI e gestores ambientais. Esses KPIs combinam todos os índices calculados nas camadas anteriores (FRP, pressão, ameaça, condição ambiental) em visualizações operacionais de alto nível.

## Índice de Pressão Máxima

Para consolidar as diversas ameaças de um evento de incêndio em um único número representativo, o sistema calcula o **Índice de Pressão Máxima**. Esse índice avalia o pior cenário entre todos os 6 índices de ameaça calculados para cada evento, sendo a principal métrica utilizada no ranking de municípios críticos.

$$
\text{pressão}_{max} = \max(\text{ameaça}_{rodovia}, \text{ameaça}_{linha}, \text{ameaça}_{sub}, \text{ameaça}_{sis}, \text{pressão}_{saúde}, \text{pressão}_{TI})
$$

## KPIs Agregados nos Dashboards Superset

Os painéis do Superset utilizam fórmulas SQL para agregar as métricas processadas em tempo real:

| KPI | Fórmula SQL | Dashboard |
|---|---|---|
| Total de Eventos | `COUNT(fire_event_id)` | Painel Geral |
| Total de Focos Acumulados | `SUM(total_focos)` | Painel Geral |
| Área Total Destruída (km²) | `SUM(area_evento_km2)` | Painel Geral |
| FRP Máximo (Severidade) | `MAX(max_frp)` | Painel Geral |
| Megadesastres Ativos | `WHERE total_focos >= 5000 AND area_evento_km2 >= 500` | Defesa Civil |
| Hospitais Sob Risco | `COUNT(DISTINCT fk_hospital) WHERE indice_pressao_saude > 0` | Defesa Civil |
| MW Sob Risco | `SUM(subestacao_capacidade_mw) WHERE indice_ameaca_subestacao > 0` | ONS |
| Pressão Municipal | `SUM(indice_pressao_maxima) GROUP BY fk_municipio_principal` | Defesa Civil |

### Ranking de Municípios Críticos

Essa visão condensa a pressão máxima por município ao longo dos últimos dias.

```sql
SELECT
  LOOKUP(f.fk_municipio_principal, 'municipios_uf') as uf_sigla,
  LOOKUP(f.fk_municipio_principal, 'municipios_nome') as nome_municipio,
  LOOKUP(f.fk_municipio_principal, 'municipios_regiao') as regiao_brasil,
  COUNT(f.fire_event_id) as total_eventos,
  SUM(f.total_focos) as total_focos_somados,
  SUM(f.indice_pressao_maxima) as pressao_acumulada_municipio
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.fk_municipio_principal IS NOT NULL
  AND f.fk_municipio_principal != 'NAO_INFORMADO'
GROUP BY 1, 2, 3
ORDER BY pressao_acumulada_municipio DESC
LIMIT 50;
```

## Classificação Espacial

### Faixas de Distância

A interpretação espacial do evento e do risco associado a ele é baseada em limites definidos (1, 3, 7, 15, 50 km).

| Distância (km) | Faixa | Uso |
|---|---|---|
| ≤ 1 | `ATE_1KM` | Ameaça direta/contato |
| ≤ 3 | `ATE_3KM` | Zona de evacuação |
| ≤ 7 | `ATE_7KM` | Zona de alerta |
| ≤ 15 | `ATE_15KM` | Zona de monitoramento |
| ≤ 50 | `ATE_50KM` | Zona de influência |
| > 50 | `ACIMA_50KM` | Fora do raio operacional |

```python
def _faixa_distancia(self, distancia_km):
    if distancia_km is None or distancia_km < 0: return "SEM_DISTANCIA"
    if distancia_km <= 1: return "ATE_1KM"
    if distancia_km <= 3: return "ATE_3KM"
    if distancia_km <= 7: return "ATE_7KM"
    if distancia_km <= 15: return "ATE_15KM"
    if distancia_km <= 50: return "ATE_50KM"
    return "ACIMA_50KM"

def _flag_ate(self, distancia_km, limite_km):
    if distancia_km is None or distancia_km < 0: return 0
    return 1 if distancia_km <= limite_km else 0
```

### Classificação de Rodovias DNIT e Ameaça

| Critério | Classe |
|---|---|
| Operacional + Pavimentado | `ALTA_RELEVANCIA` |
| Operacional | `MEDIA_RELEVANCIA` |
| Em obras ou Planejada | `BAIXA_RELEVANCIA` |
| Não informado | `NAO_INFORMADA` |

A ameaça calculada para as rodovias se utiliza da proximidade e severidade:

$$
\text{ameaça}_{rodovia} = \frac{FRP \times (1 + risco)}{\max(dist\_rodovia_{km}, 0.1)}
$$

```python
def _classificar_criticidade_rodovia(self, revestimento_classe, situacao_classe, operacao_classe):
    if operacao_classe == "OPERACIONAL" and revestimento_classe == "PAVIMENTADO": return "ALTA_RELEVANCIA"
    if operacao_classe == "OPERACIONAL": return "MEDIA_RELEVANCIA"
    if situacao_classe in {"EM_OBRAS", "PLANEJADA"}: return "BAIXA_RELEVANCIA"
    return "BAIXA_RELEVANCIA" if operacao_classe != "NAO_INFORMADO" else "NAO_INFORMADA"
```

## Otimização de Performance (Superset & Druid)

Para suportar grandes volumes de requisições de forma fluida, estratégias específicas são adotadas nos painéis.

### Amostragem para Mapa Disperso
Para evitar estouro de heap JVM no Druid em visualizações geográficas de milhões de focos, é aplicada uma amostragem determinística (`sample_bucket`) no momento da ingestão do evento:

```json
{
  "type": "expression",
  "name": "sample_bucket",
  "expression": "abs(timestamp_extract(__time,'EPOCH') * 31 + cast(latitude_centroide * 1000, 'LONG') * 17 + cast(longitude_centroide * 1000, 'LONG') * 13) % 100"
}
```
Isso permite aplicar o filtro `WHERE sample_bucket < 10` que retorna cerca de 10% da amostra, preservando a densidade geográfica visual de forma uniforme.

### Virtual Datasets com Jinja Templates
Filtros de tempo dinâmicos via Superset usam Jinja paramétrico para diminuir o tempo de scan diretamente na fonte:

```sql
{% if from_dttm is not none %}
AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
{% endif %}
GROUP BY 1, 2, 3, ...
ORDER BY max_frp DESC LIMIT 50000
```

### Lookups Druid (Resolução O(1))
Em vez de realizar operações de `JOIN` em uma base distribuída, as descrições de chaves estrangeiras são materializadas utilizando *Druid Lookups* na infraestrutura.

| Lookup | Campo | Uso |
|---|---|---|
| `municipios_nome` | nome do município | Resolução de FK para label |
| `municipios_uf` | UF sigla | Filtro geográfico |
| `hospitais_nome` | nome do hospital | Alerta hospitalar |
| `hospitais_critico` | tipo_unidade_critica | Filtro de urgência |
| `ti_nome` | nome da TI | Ranking indígena |
| `ti_etnia` | etnia | Contexto antropológico |
| `subestacao_nome` | nome da subestação | Ranking energia |
| `subestacao_risco_cascata` | risco_cascata | Filtro de risco |
| `subestacao_betweenness` | score normalizado | Ordenação por centralidade |
| `rodovia_codigo` | código DNIT | Identificação rodoviária |

## Interpretação Operacional

Os KPIs do dashboard condensam toda a complexidade analítica em números acionáveis. O operador de resposta emergencial não precisa entender conceitos teóricos como *Betweenness Centrality* ou a clusterização subjacente via *ST-DBSCAN*. Ele apenas consome as conclusões traduzidas ("Rio Verde Norte está com Risco EXTREMO" ou "Hospital X está com pressão 150"). O uso extensivo de Lookups garante que todas essas traduções ocorram de forma escalável em $\mathcal{O}(1)$ pelo Apache Druid, conferindo latência interativa sem comprometer a riqueza técnica.

## Referências
- [eventizador.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/gold/src/science/dbscan/eventizador.py)
- [layers.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/spatial/layers.py)
- [constants.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/config/constants.py)
- [04_druid_lookups.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/scripts/etapas/04_druid_lookups.py)
- [etl_dim_rodovias_federais.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/etl_dimensions/etl_dim_rodovias_federais.py)
- [03_ranking_municipios_criticos.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/stakeholders/defesa_civil/03_ranking_municipios_criticos.sql)
- [ds_eventos_geral.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/virtual_datasets/ds_eventos_geral.sql)
- [ds_eventos_mapa_disperso.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/virtual_datasets/ds_eventos_mapa_disperso.sql)
