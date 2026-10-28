-- setor: energia
-- objetivo: expor linhas de transmissao ONS para mapa de caminhos
-- datasource: dim_ons_linhas_transmissao
-- granularidade: linha_transmissao
-- visualizacao: deck_gl_path
SELECT
  id_linha_transmissao,
  nome_linha,
  tensao_kv,
  classe_tensao,
  extensao_km,
  classe_extensao,
  estado_sigla_estimado,
  classe_criticidade_linha,
  latitude,
  longitude,
  path_json
FROM dim_ons_linhas_transmissao;
