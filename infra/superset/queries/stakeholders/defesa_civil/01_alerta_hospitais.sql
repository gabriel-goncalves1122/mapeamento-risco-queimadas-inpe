SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_municipio_principal, 'municipios_nome') as nome_municipio,
  LOOKUP(f.fk_municipio_principal, 'municipios_uf') as uf_sigla,
  LOOKUP(f.fk_municipio_principal, 'municipios_regiao') as regiao_brasil,
  f.total_focos,
  f.soma_frp,
  f.indice_pressao_saude,
  LOOKUP(f.fk_hospital, 'hospitais_nome') as nome_hospital,
  LOOKUP(f.fk_hospital, 'hospitais_tipo') as tipo_unidade,
  LOOKUP(f.fk_hospital, 'hospitais_critico') as hospital_critico,
  LOOKUP(f.fk_hospital, 'hospitais_24h') as funciona_24h
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_pressao_saude > 0
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
ORDER BY f.indice_pressao_saude DESC
LIMIT 50
