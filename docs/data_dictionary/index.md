# 📖 Índice de Dicionários de Dados

O CCO-DataOps foi desenhado com forte foco em rastreabilidade de dados. Os modelos estruturais transitam por diferentes esquemas na jornada Medallion. Utilize os sumários abaixo para navegar até as especificações de cada camada.

---

## 🥉 Camada Bronze (Ingestion / Raw API)
Os dados aqui são representações fiéis (e sujas) obtidas de provedores externos. A governança destes dados está atrelada à documentação oficial das suas respectivas agências.

- **[Focos de Incêndio (INPE)](../../pipelines/bronze/inpe/DICIONARIO_DADOS.md)**: Coordenadas brutas provindas de sensores MODIS e VIIRS.
- **[Hospitais / Saúde (CNES)](../../pipelines/bronze/cnes/DICIONARIO_DADOS.md)**: Infraestrutura de Saúde.
- **[Linhas de Transmissão (ANEEL/ONS)](../../pipelines/bronze/aneel/DICIONARIO_DADOS.md)**: Sistema Interligado Nacional de energia.
- **[Terras Indígenas (FUNAI)](../../pipelines/bronze/funai/DICIONARIO_DADOS.md)**: Polígonos de preservação antropológica.
- **[Malha Rodoviária (DNIT)](../../pipelines/bronze/dnit/DICIONARIO_DADOS.md)**: Rodovias estaduais e federais (logística).
- **[Malha Municipal (IBGE)](../../pipelines/bronze/ibge/DICIONARIO_DADOS.md)**: Limites geométricos municipais e estaduais do Brasil.

---

## 🥈 Camada Silver (Conformed / Dimensions)
Dimensões limpas, sem nulos absolutos, e cruzadas no motor geográfico. Servem de fundação Lookups (Joins em Memória) para a camada ouro.
- **[Dicionário de Dimensões Espaciais (Silver)](../../pipelines/silver/DICIONARIO_DADOS.md)**: Exposição detalhada da modelagem física dos CSVs dimensionais (Hospitais, Rodovias, Municípios, etc.).

---

## 🥇 Camada Gold (Serving / Facts)
A modelagem Snowflake otimizada. Sem Strings textuais nos fatos, priorizando Kafka streaming e agregação sub-segundo no Apache Druid.
- **[Dicionário da Tabelas Fato (Gold)](../../pipelines/gold/DICIONARIO_DADOS.md)**: Contratos `Pydantic` e semântica das métricas para as Tabelas `FATO_FOCOS` e `FATO_EVENTOS_DB_SCAN`.
