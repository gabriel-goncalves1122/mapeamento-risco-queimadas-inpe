# Contexto Territorial e Socioambiental (`docs/domain/`)

> **Trilha Geral de Documentação**: [Portal Geral (`docs/README.md`)](../README.md) | [Capítulo 01: Introdução e Proposta](../architecture/01_introducao_e_proposta.md) | [Dicionários de Dados](../data_dictionary/index.md)

Este diretório documenta o território de estudo de caso e a fundamentação geoespacial e demográfica que orienta a parametrização das zonas de amortecimento (*buffer zones*) e os cálculos de pressão sobre áreas protegidas no **CCO DataOps**.

---

## 1. Documentos Disponíveis

| Documento | Escopo Técnico e Territorial |
| :--- | :--- |
| [**`ti_parque_araguaia_canoana.md`**](ti_parque_araguaia_canoana.md) | Caracterização geográfica da Ilha do Bananal (TO), histórico fundiário e demarcação da Terra Indígena Parque do Araguaia (1959–1998), localização da Aldeia Canoanã (povo Iny / Javaé) e modelagem do risco de intrusão de queimadas. |

---

## 2. Integração com os Ciclos Técnicos do Pipeline

- **Ciclo 1 — Camada Bronze ([`src/bronze/FONTES_E_APIS.md`](../../src/bronze/FONTES_E_APIS.md))**: Extração dos polígonos oficiais homologados via serviço WFS 2.0 do Geoserver da FUNAI (`tis_poligonais_portaria.geojson`).
- **Ciclo 2 — Camada Silver ([`src/silver/etl/README.md`](../../src/silver/etl/README.md))**: Reprojeção para `EPSG:5880`, cálculo de área oficial e interseção espacial $N:M$ (`gpd.overlay`) com a malha municipal do IBGE em `ETLDimTerrasIndigenas`.
- **Ciclo 3 — Motor Espacial e Enriquecimento ([`src/silver/streaming_processing/README.md`](../../src/silver/streaming_processing/README.md))**: Identificação em tempo real de focos contidos no interior da Terra Indígena (`fk_terra_indigena`) ou na sua vizinhança (`fk_terra_indigena_proxima`, `distancia_terra_indigena_km`) e cálculo do `indice_pressao_terra_indigena` (raio de referência de $30\text{ km}$).
- **Ciclo 4 — Camada Gold ([`src/gold/ARQUITETURA.md`](../../src/gold/ARQUITETURA.md))**: Agrupamento ST-DBSCAN contabilizando todos os territórios indígenas interceptados pela mancha do evento (`codigos_ti_interceptadas` e `qtd_terras_indigenas_interceptadas`).
