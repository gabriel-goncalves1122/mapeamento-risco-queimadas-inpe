# Estatísticas de Armazenamento e Segmentação no Apache Druid

Este documento consolida as estatísticas volumétricas do banco de dados Apache Druid em ambiente de produção (Cenário de Testes), extraídas diretamente da tabela de sistema `sys.segments`.

As tabelas estão divididas na arquitetura *Snowflake* entre Tabelas Fato (dados transacionais/streaming de anomalias térmicas) e Tabelas Dimensão (geometrias estáticas e metadados de infraestrutura).

## Resumo Executivo
- **Total de Linhas Processadas:** ~4,05 Milhões de registros
- **Volume Total Ocupado em Disco:** ~850 MB (altamente compactado em formato colunar)
- **Total de Segmentos (Partições):** 695 Segmentos

---

## Tabelas Fato (Streaming de Anomalias Térmicas)

As Tabelas Fato contêm a série temporal particionada. A alta granularidade de segmentos (344 para cada fato) reflete a natureza do *streaming* e do particionamento diário/semanal configurado para os focos e eventos agrupados (DBSCAN).

| Datasource (Tabela) | Total de Segmentos | Número de Linhas | Tamanho (MB) | Descrição |
|---------------------|:---:|---:|---:|---|
| **`fato_focos_incendio`** | 344 | 3.335.198 | 572,10 MB | Focos de calor individuais brutos capturados por satélite (Nível 1). |
| **`fato_eventos_incendio`** | 344 | 147.560 | 102,71 MB | Clusters poligonais gerados pelo ST-DBSCAN representando incêndios contínuos (Nível 2). |
| **Subtotal Fatos** | **688** | **3.482.758** | **674,81 MB** | |

---

## Tabelas Dimensão (Infraestrutura Crítica e Contexto Geoespacial)

As Tabelas Dimensão utilizam particionamento único (1 segmento por tabela), pois representam o espaço geográfico estático (sem eixo de tempo). O maior volume recai sobre os polígonos complexos (Hospitais, Municípios e Terras Indígenas) com alta carga de vértices GeoJSON.

| Datasource (Tabela) | Total de Segmentos | Número de Linhas | Tamanho (MB) | Descrição |
|---------------------|:---:|---:|---:|---|
| **`dim_hospitais_cnes`** | 1 | 550.882 | 103,66 MB | Catálogo do DataSUS (Nível 3). É a maior dimensão em volume de registros, cruzando risco de fumaça vs hospitais. |
| **`dim_terras_indigenas`** | 1 | 650 | 44,26 MB | Limites territoriais da FUNAI. Tem alto peso em bytes por ter polígonos imensos e detalhados. |
| **`dim_municipios_coordenadas`** | 1 | 5.564 | 17,45 MB | Malha municipal brasileira para limite geográfico analítico. |
| **`dim_rodovias_federais`** | 1 | 14.255 | 8,76 MB | Malha logística (BIT/ANTT). Linhas multicadeias que cruzam florestas. |
| **`dim_ons_linhas_transmissao`**| 1 | 1.817 | 0,51 MB | Grafo logístico de Alta Tensão (NetworkX). |
| **`dim_ons_subestacoes`** | 1 | 627 | 0,15 MB | Nodos centrais do Sistema Elétrico (Betweenness Centrality). |
| **`dim_ons_sistemas_isolados`** | 1 | 120 | 0,02 MB | Nodos energéticos desconectados do SIN (Amazônia profunda). |
| **Subtotal Dimensões** | **7** | **573.915** | **174,81 MB** | |

---

## Conclusões sobre Compressão e Otimização
1. **Poder do Formato Colunar:** Mesmo hospedando **3.3 milhões de focos** e milhares de geometrias de alta densidade (polígonos detalhados do Brasil), o Druid conseguiu compactar toda a arquitetura em apenas **~850 MB** de armazenamento final nos *Historical Nodes*.
2. **Eficiência do LookUp Espacial:** As chaves estrangeiras (`fk_...`) nas Tabelas Fato evitam que as *Strings* de `GeoJSON` de centenas de MBs se repitam 3,3 milhões de vezes, garantindo viabilidade para a RAM da arquitetura DataOps.
