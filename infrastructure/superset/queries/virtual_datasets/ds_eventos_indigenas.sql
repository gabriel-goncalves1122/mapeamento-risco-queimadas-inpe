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
  LOOKUP(fk_terra_indigena, 'ti_path_json') AS ti_path_json_dentro,
  
  -- TI Lookups (Proxima/Entorno)
  fk_terra_indigena_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_nome') AS ti_nome_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_etnia') AS ti_etnia_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_uf') AS ti_uf_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_path_json') AS ti_path_json_proxima,

  -- Unified TI Lookups for easy filtering
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_nome'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_nome')
  ) AS ti_nome_unificado,
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_etnia'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_etnia')
  ) AS ti_etnia_unificada,
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_path_json'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_path_json')
  ) AS ti_path_json_unificado,
  max_frp
  
FROM fato_eventos_incendio
WHERE 
  ((fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO')
  OR indice_pressao_terra_indigena > 0)
  {% if from_dttm is defined and from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25
ORDER BY max_frp DESC
LIMIT 50000
