# Dashboard: 03_Seguranca_Energetica

Este documento cataloga os gráficos e consultas que compõem o painel visual **03_Seguranca_Energetica** no Apache Superset.

## Catálogo de Gráficos e Consultas Base

Abaixo estão listados os conjuntos de dados (Virtual Datasets) utilizados neste painel, seguidos pelos elementos visuais que eles alimentam e o código SQL subjacente.

### 🗃️ Dataset: `ds_eventos_energia`

**Gráficos que consomem este dado:**
- KPI: Linhas de Transmissão Ameaçadas *(Visualização: big_number_total)*
- KPI: MW Sob Risco (Subestações) *(Visualização: big_number_total)*
- Ranking: Linhas por Ameaça *(Visualização: echarts_timeseries_bar)*
- Scatter: Capacidade MW vs Ameaça *(Visualização: bubble_v2)*
- Tabela: Sistemas Isolados *(Visualização: table)*
- Série Temporal: Ameaça diária às Linhas *(Visualização: echarts_area)*
- Tabela: Subestações Ameaçadas (Network Science) *(Visualização: table)*

**Query SQL Subjacente:**
```sql
-- ============================================================
-- VIRTUAL DATASET: Infraestrutura de Energia (ONS)
-- ALIMENTA: Dashboard ONS / Setor Elétrico
-- TABELA BASE: fato_eventos_incendio
-- ============================================================
SELECT
  fire_event_id,
  __time,
  total_focos,
  
  -- Linhas de Transmissão
  indice_ameaca_linha,
  distancia_linha_km,
  fk_linha_transmissao,
  LOOKUP(fk_linha_transmissao, 'linha_nome') AS linha_nome,
  CAST(LOOKUP(fk_linha_transmissao, 'linha_tensao') AS FLOAT) AS linha_tensao_kv,
  LOOKUP(fk_linha_transmissao, 'linha_uf') AS linha_uf,
  
  -- Subestações
  indice_ameaca_subestacao,
  distancia_subestacao_km,
  fk_subestacao,
  LOOKUP(fk_subestacao, 'subestacao_nome') AS subestacao_nome,
  CAST(LOOKUP(fk_subestacao, 'subestacao_capacidade') AS FLOAT) AS subestacao_capacidade_mw,
  CAST(LOOKUP(fk_subestacao, 'subestacao_betweenness') AS FLOAT) AS subestacao_betweenness,
  LOOKUP(fk_subestacao, 'subestacao_risco_cascata') AS subestacao_risco_cascata,
  
  -- Sistemas Isolados
  indice_ameaca_sistema_isolado,
  distancia_sistema_isolado_km,
  fk_sistema_isolado,
  LOOKUP(fk_sistema_isolado, 'sistema_isolado_nome') AS sistema_isolado_nome,
  LOOKUP(fk_sistema_isolado, 'sistema_isolado_uf') AS sistema_isolado_uf,
  max_frp

FROM fato_eventos_incendio
WHERE
  (indice_ameaca_linha > 0 
  OR indice_ameaca_subestacao > 0 
  OR indice_ameaca_sistema_isolado > 0)
  {% if from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
ORDER BY max_frp DESC
LIMIT 50000
```

---

