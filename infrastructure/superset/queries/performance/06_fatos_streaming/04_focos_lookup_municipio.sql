-- categoria: fatos_streaming
-- objetivo: medir custo de LOOKUP em tabela de 3.3M linhas
-- datasource: fato_focos_incendio
-- padrao_carga: lookup_heavy
-- visualizacao: tabela
SELECT
  fk_bioma,
  LOOKUP(fk_municipio, 'municipios_uf') AS uf,
  COUNT(*) AS focos,
  AVG(potencia_radiativa_fogo) AS media_frp,
  MAX(potencia_radiativa_fogo) AS max_frp
FROM fato_focos_incendio
WHERE __time >= TIMESTAMP '2025-08-01' AND __time < TIMESTAMP '2025-11-01'
GROUP BY 1, 2
ORDER BY focos DESC;
