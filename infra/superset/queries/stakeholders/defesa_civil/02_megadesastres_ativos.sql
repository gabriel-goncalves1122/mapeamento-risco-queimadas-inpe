SELECT
  f.__time as inicio_evento,
  f.fire_event_id,
  LOOKUP(f.fk_municipio_principal, 'municipios_nome') as nome_municipio,
  LOOKUP(f.fk_municipio_principal, 'municipios_uf') as uf_sigla,
  LOOKUP(f.fk_municipio_principal, 'municipios_regiao') as regiao_brasil,
  f.fk_bioma,
  f.duracao_dias,
  f.area_evento_km2,
  f.total_focos,
  f.soma_frp,
  f.indice_pressao_maxima
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.total_focos >= 5000 
  AND f.area_evento_km2 >= 500.0
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
ORDER BY f.total_focos DESC
LIMIT 20
