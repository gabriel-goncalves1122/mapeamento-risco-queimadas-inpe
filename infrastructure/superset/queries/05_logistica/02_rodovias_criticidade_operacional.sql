-- setor: logistica
-- objetivo: listar trechos de maior criticidade operacional para priorizacao
-- datasource: dim_rodovias_federais
-- granularidade: trecho_rodoviario
-- visualizacao: tabela_mapa
SELECT
  id_trecho_rodoviario,
  codigo_rodovia,
  jurisdicao,
  status_operacional,
  situacao_fisica,
  tipo_pavimento,
  criticidade_rodovia,
  latitude,
  longitude,
  path_json
FROM dim_rodovias_federais
WHERE criticidade_rodovia <> 'NAO INFORMADO';
