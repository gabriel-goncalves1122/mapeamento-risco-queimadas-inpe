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
LIMIT 50
