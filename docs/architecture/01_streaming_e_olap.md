# Streaming e OLAP: O Coração de Performance do CCO

Para sustentar um Centro de Controle (CCO) de respostas a desastres, precisávamos de um sistema imune a gargalos de latência. Quando focos de incêndio entram em pico de detecção (ex: Amazônia em Setembro), inserções tradicionais num PostgreSQL cairiam por excesso de concorrência ou I/O.

## 1. Desacoplamento via Apache Kafka (Mensageria)
O Kafka atua como um pulmão.
1. O coletor da **Gold** (`produtor_eventos`) envia dados via _Producer_. 
2. Os dados residem temporariamente em tópicos segmentados (`focos-incendio`, `eventos-incendio`).
3. Isso garante que nenhum pico de dados, por maior que seja, consiga derrubar o Banco de Dados. A pressão é controlada.

## 2. Apache Druid (O Motor OLAP Analítico)
Por que o Druid e não um Postgres/PostGIS tradicional?
Em testes práticos do projeto, mapear visualmente milhões de focos em um mapa (Dashboard) causava demoras de ~15 segundos numa arquitetura tradicional. 

O Apache Druid inverte esse paradigma através de:
- **Indexação em Bitmaps (Roaring):** Permite filtrar dimensões (ex: `estado = 'MG'`) com comparações bit-a-bit instantâneas, não varrendo o disco (Full Scan).
- **Segmentos baseados em Tempo:** Focos de incêndio são inerentemente *Time-Series*. O Druid fragmenta os dados por hora/dia, permitindo pular dados irrelevantes no filtro.
- **Lookup Joins (A Magia do Medallion):** Em vez de jogar o peso do *Join* para a Tabela Fato gigante, carregamos as Dimensões (Municípios, Hospitais) na memória RAM do Druid como `Lookups`. A query no Superset converte IDs em Nomes instantaneamente no momento da leitura, barateando o payload do Streaming.
