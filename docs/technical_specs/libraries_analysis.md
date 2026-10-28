# Análise de Dependências e Bibliotecas

O coração de dados e inteligência do SIRDA (Sistema de Inteligência e Resposta a Desastres Ambientais) roda primariamente em Python, gerenciado pelo `uv` (empacotador ultrarrápido). As escolhas no `pyproject.toml` refletem o padrão-ouro do DataOps moderno.

## Core DataOps & Orquestração
- **`dagster` (>= 1.13.9):** Gerencia todo o grafo de *assets* (Camadas Bronze, Silver e Gold). Escolhido por sua abordagem centrada em dados e suporte nativo ao particionamento temporal.
- **`kafka-python-ng`:** Cliente robusto de Kafka para injetar os *payloads* no barramento em tempo real.
- **`pydantic`:** Aplica tipagem estrita e validação léxica, garantindo o "Contrato de Dados" antes que o fluxo seja despejado no Tópico Kafka, blindando o *Data Warehouse* contra colunas sujas.

## Análise Geoespacial & Performance Híbrida
- **`geopandas`, `shapely` e `pyogrio`:** O trio responsável por ler os vastos *Shapefiles* vetoriais do IBGE, FUNAI, DNIT e ANEEL. O `pyogrio` injeta performance C++ sobre a leitura de arquivos geoespaciais, acelerando enormemente o processamento da camada Silver em cruzamentos espaciais.
- **`pandas` e `pyarrow`:** Permitem transformações em memória baseadas em vetores e escrita instantânea de formatos de compressão columnar (Parquet), essenciais na conversão de tipos brutais e desfragmentação.

## Algoritmos Analíticos (Machine Learning e Grafos)
- **`scikit-learn` (DBSCAN):** Utilizado para analisar séries espaciais baseadas em densidade, traduzindo "pontos de calor isolados" em "manchas unificadas de incêndio" (*clustering*).
- **`networkx`:** Exclusivo e cirúrgico no trato da Infraestrutura Crítica Energética. Calcula distâncias topológicas e resiliência (centralidade) ao mapear usinas, subestações e linhas de transmissão como um Grafo matemático para inferir riscos em caso de rupturas.

## Engenharia de Qualidade (Testes)
- **`pytest` e `pytest-mock`:** Validam a execução silenciosa dos pipelines (CI/CD Local), efetuando testes falsos (*mock*) em APIs do INPE para garantir resiliência aos *endpoints* governamentais instáveis.
