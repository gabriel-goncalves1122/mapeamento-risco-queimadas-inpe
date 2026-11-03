-- setor: eventos_incendio
-- objetivo: priorizar municipios por eventos, focos representados e intensidade radiativa
-- datasource: fato_eventos_incendio, dim_municipios_coordenadas
-- granularidade: municipio
-- visualizacao: tabela_ranking
SELECT
  f.fk_municipio_principal AS codigo_ibge,
  m.municipios_nome,
  m.estado_sigla,
  m.regiao_brasil,
  COUNT(*) AS total_eventos,
  SUM(f.total_focos) AS focos_representados,
  SUM(f.soma_frp) AS frp_total,
  AVG(f.indice_pressao_maxima) AS pressao_media,
  MAX(f.indice_pressao_maxima) AS pressao_maxima
FROM fato_eventos_incendio f
LEFT JOIN dim_municipios_coordenadas m
  ON f.fk_municipio_principal = m.codigo_ibge
GROUP BY 1, 2, 3, 4
ORDER BY total_eventos DESC;
