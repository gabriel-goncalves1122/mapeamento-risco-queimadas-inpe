-- setor: logistica
-- objetivo: expor trechos de rodovias federais para mapa de caminhos
-- datasource: dim_rodovias_federais
-- granularidade: trecho_rodoviario
-- visualizacao: deck_gl_path
SELECT
  id_trecho_rodoviario,
  codigo_rodovia,
  jurisdicao,
  revestimento,
  classe_revestimento,
  tipo_pavimento,
  situacao_fisica,
  classe_situacao_fisica,
  status_operacional,
  classe_status_operacional,
  criticidade_rodovia,
  latitude,
  longitude,
  path_json
FROM dim_rodovias_federais;
