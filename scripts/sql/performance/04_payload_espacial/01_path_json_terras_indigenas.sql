-- categoria: payload_espacial
-- objetivo: medir custo de ler geometrias serializadas de TIs
-- datasource: dim_terras_indigenas
-- padrao_carga: string_payload_scan
-- visualizacao: indicador
SELECT
  COUNT(*) AS terras_indigenas_total,
  SUM(LENGTH(path_json)) AS bytes_path_json_estimados,
  AVG(LENGTH(path_json)) AS media_path_json,
  MAX(LENGTH(path_json)) AS maior_path_json
FROM dim_terras_indigenas;
