# CCO DataOps - ETL Context (Agent Guide)

Bem-vindo à camada de Engenharia de Dados Lote (Batch). Responsável pelas Tabelas de Dimensão do Apache Druid/Superset.

## 🏗️ Padrão de Arquitetura (Obrigatório)
1. **Herança Orientada a Objetos**: Todo pipeline deve ser uma classe que herda de `BaseETL` (em `src/etl/utils/base.py`). Você NÃO deve reimplementar métodos de carregar e salvar. Implemente apenas `extract()` e `transform()`.
2. **Registro no Dagster**: Nenhum pipeline deve ser executado primariamente com `if __name__ == "__main__":`. Todo ETL deve ser empacotado como um `@asset` no Dagster (`src/orchestration/`).

## 🗺️ Regras de Geometria (Superset & Deck.gl)
Esta é a regra mais crítica desta camada. Todo output analítico espacial (exceto se for apenas Join) DEVE seguir o padrão compatível com os plugins Deck.gl do Apache Superset.

- **Padrão `path_json`**: Toda geometria complexa (Polígonos, Linhas e Pontos no Deck.gl) deve ser convertida com a função `geometry_para_path_json` localizada em `src.etl.utils.geo_helpers`. A saída deve se chamar `path_json`.
- **WKT como contrato técnico interno**: `geometria_wkt` é permitido em dimensões quando necessário para reconstrução Shapely/GeoPandas no `SpatialLayer`, cálculo de proximidade, interseção ou grafos. Não use `geometria_wkt` no payload da Fato Kafka/Druid.
- **Expurgo de formatos redundantes**: Não adicione `geojson_point` ou múltiplas cópias equivalentes da mesma geometria. Use `path_json` para visualização e, quando indispensável ao processamento interno, `geometria_wkt`.
- **Centróides**: Para facilitar mapas rápidos, exporte sempre colunas escalares `latitude` e `longitude` em EPSG:4326.

## 🧹 Regras de Limpeza de Dados
- **Sem colunas redundantes**: Não crie colunas como `estado_sigla_idx` ou IDs genéricos que poluem a base se já existe uma chave natural primária. Deixe que a indexação (bitmap/dictionary) aconteça nativamente no Druid.
- **Tratamento de Nulos**: Se não há dado, force a inserção da string `"NAO INFORMADO"`. Nunca insira `0` ou `-1` para representar strings ou valores nulos qualitativos.
- **Reuso**: Use `limpar_texto_druid` e `limpar_codigo` (importados de cleaners/string_helpers) sempre.

## 📝 Comentários em ETL
- Documente regras de limpeza quando elas preservam compatibilidade com uma fonte específica (INPE, ONS, CNES, IBGE) ou com o consumo no Druid/Superset.
- Comente o significado de colunas derivadas quando o nome sozinho não explicar a regra de negócio, especialmente chaves naturais, criticidade, prioridades e centróides.
- Explique o contrato geométrico ao criar `path_json`, `geometria_wkt`, `latitude` e `longitude`: visualização, reconstrução técnica ou cálculo espacial.
- Ao escolher defaults como `"NAO INFORMADO"`, `0.0` ou `None`, deixe claro se o campo é qualitativo, métrico ou opcional.
