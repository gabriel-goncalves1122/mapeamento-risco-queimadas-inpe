# Dicionário de Dados - Camada Gold (Facts & Metrics)

A Camada Gold (Ouro) constitui o topo da arquitetura Medallion deste sistema. Aqui reside a carga bruta (Streaming via Kafka) e métricas consolidadas por inteligência artificial (Eventos Agrupados via DB-SCAN e Análise de Grafos).

**Regra de Ouro da Camada Gold**: As Tabelas Fato contêm *APENAS* Identificadores de Dimensão (FKs), Métricas (Valores Geográficos ou Físicos Contínuos), Categorias Enumeradas e Datas (Timestamp). Nenhuma string textual decorativa (nomes de municípios, nomes de estados) pode compor o payload, otimizando drasticamente o peso na serialização Kafka e o indexamento no Druid.

---

## 1. Fato: Focos de Incêndio (Streaming Base)
Ingerido continuamente pelo tópico Kafka `focos-incendio`. Trata-se da leitura atômica (um satélite, um pixel quente).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `timestamp` | Datetime (ISO) | Instante exato da leitura no satélite. Principal partição no Druid. |
| `foco_id` | String (UUID) | Identificador único do foco na nossa plataforma (Hash gerado via coordenadas e hora). |
| `satelite` | Categoria | Satélite que reportou (Ex: AQUA_M-T, TERRA_M-M). |
| `frp` | Float | *Fire Radiative Power* - Poder radioativo do pixel em Megawatts. Mede a agressividade térmica. |
| `lat`, `lon` | Float | Coordenadas cruas. |
| `risco_ons_calc` | Float | Distância contínua até a Linha de Transmissão mais próxima. Usado em filtros matemáticos. |
| **`id_municipio_fk`** | Int | Código IBGE (Join com Dimensão de Município). |
| **`id_linha_fk`** | Int | Código interno (Join com Dimensão de Linhas de Transmissão). |
| **`id_terra_indigena_fk`** | Int | Código FUNAI (Join com Dimensão de Terras Indígenas). |
| **`id_cnes_fk`** | Int | Código CNES do hospital mais próximo (Join com Dimensão de Hospitais). |

> *No Druid (Superset), o `id_municipio_fk` é automaticamente traduzido em `nome_municipio` ou `estado` em tempo de leitura usando Lookups, poupando a rede do fardo dessas strings durante o streaming Kafka.*

---

## 2. Fato: Eventos Climáticos (DB-SCAN Clusterizados)
Agregação gerada pós-processamento utilizando Algoritmo *ST-DBSCAN* (Spatial-Temporal). Representa a mancha orgânica do fogo que se une ao longo do espaço e tempo. Tópico `eventos-incendio`.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `timestamp_inicio` | Datetime | Início do evento. |
| `timestamp_fim` | Datetime | Fim da janela do evento. |
| `evento_id` | String | Hash UUID do cluster unificado. |
| `densidade` | Int | Número bruto de focos singulares acoplados a esse evento. |
| `risco_cascata_global` | Float | (Output de Machine Learning) Probabilidade calculada (0 a 1) deste fogo interromper a malha do ONS. |
| `area_estimada_km2` | Float | Cobertura total deduzida pelo Envelope Convexo (Convex Hull) dos pontos da mancha. |
| **`id_municipio_fk`** | Int | IBGE majoritário onde a mancha atua. |
| **`id_linha_afetada_fk`** | Int | Linha de Transmissão centralmente ameaçada. |

---

## 3. Relatórios Sintéticos Analíticos (`legacy/analytics`)
O sistema suporta exportação retroativa para benchmarks governamentais e acadêmicos. Arquivos gerados não fluem para o Superset (ficam no disco para auditoria).
*Verifique `legacy/analytics/` para mais detalhes de outputs.*
