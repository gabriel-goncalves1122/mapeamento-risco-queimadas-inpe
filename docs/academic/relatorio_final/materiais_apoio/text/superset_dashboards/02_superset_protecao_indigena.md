# Dashboard: 02_Protecao_Indigena

Este documento cataloga os gráficos e consultas que compõem o painel visual **02_Protecao_Indigena** no Apache Superset.

## Catálogo de Gráficos e Consultas Base

Abaixo estão listados os conjuntos de dados (Virtual Datasets) utilizados neste painel, seguidos pelos elementos visuais que eles alimentam e o código SQL subjacente.

### 🗃️ Dataset: `ds_eventos_indigenas`

**Gráficos que consomem este dado:**
- KPI: TIs Invadidas (Fogo Dentro) *(Visualização: big_number_total)*
- KPI: TIs Ameaçadas no Entorno *(Visualização: big_number_total)*
- Ranking: TIs por Pressão Acumulada *(Visualização: echarts_timeseries_bar)*
- Tabela: Fogo Dentro de TIs *(Visualização: table)*
- Tabela: Pressão no Entorno *(Visualização: table)*
- Mapa: Fogo em Terras Indígenas *(Visualização: deck_scatter)*

**Query SQL Subjacente:**
```sql
-- ============================================================
-- VIRTUAL DATASET: Eventos Indígenas
-- ALIMENTA: Dashboard FUNAI / ONGs Indígenas
-- TABELA BASE: fato_eventos_incendio
-- ============================================================
SELECT
  fire_event_id,
  __time,
  latitude_centroide,
  longitude_centroide,
  total_focos,
  soma_frp,
  area_evento_km2,
  duracao_dias,
  
  -- TI Metrics
  indice_pressao_terra_indigena,
  distancia_terra_indigena_km,
  
  -- TI Classification
  CASE
    WHEN fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO'
    THEN 'DENTRO'
    ELSE 'ENTORNO'
  END AS tipo_ameaca,
  
  -- TI Lookups (Dentro)
  fk_terra_indigena,
  LOOKUP(fk_terra_indigena, 'ti_nome') AS ti_nome_dentro,
  LOOKUP(fk_terra_indigena, 'ti_etnia') AS ti_etnia_dentro,
  LOOKUP(fk_terra_indigena, 'ti_uf') AS ti_uf_dentro,
  
  -- TI Lookups (Proxima/Entorno)
  fk_terra_indigena_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_nome') AS ti_nome_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_etnia') AS ti_etnia_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_uf') AS ti_uf_proxima,

  -- Unified TI Lookups for easy filtering
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_nome'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_nome')
  ) AS ti_nome_unificado,
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_etnia'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_etnia')
  ) AS ti_etnia_unificada,
  max_frp
  
FROM fato_eventos_incendio
WHERE 
  ((fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO')
  OR indice_pressao_terra_indigena > 0)
  {% if from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
ORDER BY max_frp DESC
LIMIT 50000
```

---

