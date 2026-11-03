# 📖 Índice Geral de Dicionários de Dados

O ecossistema **CCO-DataOps** foi desenhado com foco estrito em rastreabilidade de dados, integridade de esquemas e tipagem forte. Os modelos estruturais transitam pelas camadas da arquitetura Medallion. Utilize os sumários abaixo para navegar até as especificações de cada camada.

---

## 🥉 Camada Bronze (Ingestão / Raw API)
Os dados nesta camada são representações fiéis e imutáveis dos provedores governamentais externos. A extração e catalogação são gerenciadas por classes especializadas (como `AneelArcGisExtractor` para infraestrutura do setor elétrico) e rotinas de download de satélite.
* 📋 **[Dicionário de Esquemas Brutos (Bronze)](../../src/bronze/DICIONARIO_DADOS.md):** Especificação exaustiva de atributos originais, tipos de dados e nomes literais fornecidos pelos provedores antes de qualquer transformação.
* 🌐 **[Catálogo Técnico de Fontes e APIs (Bronze)](../../src/bronze/FONTES_E_APIS.md):** Endpoints, parâmetros HTTP GET, paginação ArcGIS REST, frequências de atualização e referências bibliográficas do Relatório Final para INPE, ANEEL, FUNAI, IBGE, DNIT e DATASUS.

---

## 🥈 Camada Silver (Dimensões Conformadas)
Dimensões padronizadas, sem valores nulos em chaves primárias, com projeções métricas SIRGAS 2000 (`EPSG:5880`) e indexação espacial via *STRtree / R-Tree*. Servem de base para os mecanismos de *Lookup* em memória do Apache Druid, permitindo *Joins* analíticos com latência sub-segundo:
* 📊 **[Dicionário de Dimensões Espaciais (Silver)](../../src/silver/DICIONARIO_DADOS.md):** Especificação física detalhada das 7 tabelas de dimensão (`dim_municipios_coordenadas`, `dim_hospitais_cnes`, `dim_terras_indigenas`, `dim_ons_linhas_transmissao`, `dim_ons_subestacoes`, `dim_ons_sistemas_isolados`, `dim_rodovias_federais`).
* 📘 **[Guia e Arquitetura da Camada Silver](../../src/silver/README.md):** Visão geral da engenharia de dimensões, motor espacial e validadores de qualidade.

---

## 🥇 Camada Gold (Serving / Tabelas Fato & Streaming)
Modelagem Snowflake otimizada. Não trafega strings redundantes no payload de streaming Kafka, priorizando chaves estrangeiras (`fk_*`), métricas contínuas e serialização compacta para agregação no Apache Druid:
* 📋 **[Dicionário das Tabelas Fato (Gold)](../../src/gold/DICIONARIO_DADOS.md):** Contratos de dados Pydantic (`FocoFatoPayload` e `EventoFatoPayload`), métricas térmicas (FRP, Risco de Fogo), índices dinâmicos de ameaça e topologia de grafos (Betweenness Centrality e Risco de Cascata ONS).
* 🏛️ **[Arquitetura e Engenharia da Camada Gold](../../src/gold/ARQUITETURA.md):** Detalhamento dos princípios POO/SOLID, modelos científicos (ST-DBSCAN e NetworkX) e produtores de streaming.
