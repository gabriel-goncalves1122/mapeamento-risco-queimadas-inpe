-- ============================================================
-- VIRTUAL DATASET: Linhas de Transmissão ONS (Layer 1)
-- ALIMENTA: Mapa Múltiplo Deck.GL (Camada Cartográfica Base)
-- ============================================================
SELECT
  fk_linha_transmissao,
  LOOKUP(fk_linha_transmissao, 'linha_nome') AS linha_nome,
  LOOKUP(fk_linha_transmissao, 'linha_path_json') AS linha_path_json
FROM (
  SELECT
    fk_linha_transmissao
  FROM fato_eventos_incendio
  WHERE 
    indice_ameaca_linha > 0
    {% if from_dttm is defined and from_dttm is not none %}
    AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
    {% endif %}
  -- Agrupa extraindo apenas as malhas viárias das linhas expostas
  GROUP BY 1
)
WHERE LOOKUP(fk_linha_transmissao, 'linha_path_json') IS NOT NULL
LIMIT 10000
