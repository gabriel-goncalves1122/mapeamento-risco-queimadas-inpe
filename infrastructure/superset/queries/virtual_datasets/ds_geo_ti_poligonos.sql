-- ============================================================
-- VIRTUAL DATASET: Polígonos de Terras Indígenas (Layer 1)
-- ALIMENTA: Mapa Múltiplo Deck.GL (Camada Cartográfica Base)
-- ============================================================
SELECT
  fk_ti_unificada,
  LOOKUP(fk_ti_unificada, 'ti_nome') AS ti_nome,
  LOOKUP(fk_ti_unificada, 'ti_path_json') AS ti_path_json
FROM (
  SELECT
    COALESCE(fk_terra_indigena, fk_terra_indigena_proxima) AS fk_ti_unificada
  FROM fato_eventos_incendio
  WHERE 
    ((fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO') OR indice_pressao_terra_indigena > 0)
    {% if from_dttm is defined and from_dttm is not none %}
    AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
    {% endif %}
  -- Agrupa primariamente (milhões para centenas de linhas)
  GROUP BY 1
)
-- Executa a verificação pesada do JSON apenas nas poucas TIs únicas afetadas
WHERE LOOKUP(fk_ti_unificada, 'ti_path_json') IS NOT NULL
LIMIT 10000
