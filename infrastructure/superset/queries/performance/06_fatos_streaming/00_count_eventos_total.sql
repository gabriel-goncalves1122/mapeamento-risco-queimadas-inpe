-- categoria: fatos_streaming
-- objetivo: medir latencia baseline em tabela fato (158K linhas)
-- datasource: fato_eventos_incendio
-- padrao_carga: count_scan
-- visualizacao: indicador
SELECT COUNT(*) AS total_eventos FROM fato_eventos_incendio;
