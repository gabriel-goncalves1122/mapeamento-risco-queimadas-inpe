-- setor: eventos_incendio
-- objetivo: expor a mancha dos eventos para mapa Deck.gl sem joins operacionais
-- datasource: fato_eventos_incendio
-- granularidade: evento
-- visualizacao: mapa_polygon
SELECT
  fire_event_id,
  __time AS data_inicio,
  data_fim,
  latitude_centroide,
  longitude_centroide,
  path_json,
  total_focos,
  soma_frp,
  max_frp,
  max_risco_fogo,
  duracao_dias,
  area_evento_km2,
  fk_municipio_principal,
  fk_terra_indigena_proxima,
  fk_hospital
FROM fato_eventos_incendio
WHERE path_json IS NOT NULL
  AND path_json <> ''
  AND path_json <> '[]';
