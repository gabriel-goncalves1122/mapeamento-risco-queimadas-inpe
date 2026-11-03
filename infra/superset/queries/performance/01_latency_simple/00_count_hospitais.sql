-- categoria: latency_simple
-- objetivo: medir latencia minima em uma dimensao grande
-- datasource: dim_hospitais_cnes
-- padrao_carga: count_scan
-- visualizacao: indicador
SELECT COUNT(*) AS total_hospitais
FROM dim_hospitais_cnes;
