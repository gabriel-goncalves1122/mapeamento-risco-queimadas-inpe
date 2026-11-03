-- categoria: payload_espacial
-- objetivo: medir custo de ler geometrias serializadas de rodovias
-- datasource: dim_rodovias_federais
-- padrao_carga: string_payload_scan
-- visualizacao: indicador
SELECT
  COUNT(*) AS trechos_total,
  SUM(LENGTH(path_json)) AS bytes_path_json_estimados,
  AVG(LENGTH(path_json)) AS media_path_json,
  MAX(LENGTH(path_json)) AS maior_path_json
FROM dim_rodovias_federais;
