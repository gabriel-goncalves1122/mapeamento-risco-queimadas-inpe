# Relatório Técnico de Experiência e Competências: Projeto SIRDA / CCO-DataOps

> **Documento-base estruturado para confecção de Currículo Vitae (CV), perfil acadêmico/profissional e entrevistas técnicas.**  
> Este documento sintetiza de forma direta e objetiva o contexto do projeto, a fundamentação técnica, a arquitetura de dados desenvolvida, as análises de desempenho realizadas e os pontos de destaque para processos seletivos.

---

## 1. Contexto Geral e Vínculo Institucional

* **Instituição:** Universidade Federal de Itajubá (**UNIFEI**) — Campus Itajubá
* **Unidade Acadêmica:** Instituto de Engenharia de Sistemas e Tecnologia da Informação (**IESTI**)
* **Área de Conhecimento:** Engenharia da Computação / Engenharia de Dados
* **Papel:** Bolsista de Iniciação Científica (IC) / Desenvolvedor do Projeto
* **Orientação:** Profa. Dra. Barbara Pimenta Caetano (PQ)
* **Nome do Projeto:** **SIRDA** (*Sistema de Inteligência e Resposta a Desastres Ambientais*) / **CCO-DataOps**
* **Período de Execução:** 2025 – 2026

---

## 2. Contexto do Projeto e Motivação Técnica

### 2.1. O Problema Abordado
O monitoramento contínuo de anomalias térmicas e queimadas no território nacional impõe desafios técnicos relevantes:
1. **Limitações de Modelos em Lote (*Batch*):** Relatórios processados periodicamente em intervalos longos reduzem a eficácia da resposta operacional a focos de incêndio ativos.
2. **Custo Computacional em Junções Espaciais:** Cruzar milhões de pontos observacionais com polígonos complexos (fronteiras municipais, terras indígenas e faixas de servidão) gera alto consumo de processamento e lentidão em bancos de dados relacionais tradicionais.
3. **Escassez de Contexto Relacional nos Dados Brutos:** Coordenadas térmicas isoladas fornecem apenas detecções pontuais, sem indicar a proximidade de infraestruturas estratégicas ou áreas de preservação ambiental.

### 2.2. Objetivo do Projeto
Desenvolver e avaliar experimentalmente uma arquitetura *DataOps* orientada a eventos para ingestão, processamento e disponibilização analítica de dados geoespaciais em tempo quase real. O sistema integra:
* Extração e correlação de dados abertos governamentais: **INPE** (anomalias térmicas), **ONS/ANEEL** (malha do setor elétrico), **FUNAI** (terras indígenas), **IBGE** (municípios), **DNIT** (rodovias) e **CNES** (hospitais).
* Persistência em banco colunar distribuído para consultas agregadas com baixa latência.
* Painéis analíticos no **Apache Superset** voltados a diferentes esferas operacionais: monitoramento preventivo da rede elétrica (prevenção de desligamentos e blecautes), proteção territorial indígena e apoio à logística da Defesa Civil.

---

## 3. Pilha Tecnológica Empregada

| Categoria | Ferramenta / Biblioteca | Aplicação no Projeto |
| :--- | :--- | :--- |
| **Linguagem & Ambiente** | `Python 3.12`, `uv` | Implementação dos módulos de ingestão, ETL, modelagem e testes; gestão determinística de dependências. |
| **Orquestração** | `Apache Dagster` | Construção de DAGs declarativos baseados em *Software-Defined Assets* (SDA), controle de linhagem de dados (*lineage*) e rastreabilidade de etapas. |
| **Mensageria & Streaming** | `Apache Kafka`, `kafka-python-ng` | Ingestão desacoplada de eventos térmicos, atuando como amortecedor de picos de carga entre as fontes e o banco analítico. |
| **Banco de Dados Analítico (OLAP)** | `Apache Druid` | Armazenamento colunar distribuído, indexação via bitmaps, compressão LZ4 e execução de consultas de agregação temporal e espacial. |
| **Banco Transacional / Metadados** | `PostgreSQL` | Repositório de metadados do Apache Druid e base de controle do Apache Superset. |
| **Camada de Visualização** | `Apache Superset` | Criação de conjuntos de dados virtuais (SQL), mapeamentos geoespaciais e painéis analíticos interativos. |
| **Geoprocessamento** | `GeoPandas`, `Shapely`, `PyProj`, `PyOgrio` | Manipulação de dados vetoriais, conversão de sistemas de coordenadas (SIRGAS 2000 / EPSG:4674), indexação em árvore (*R-Tree*) e operações de envoltória convexa. |
| **Modelagem & Ciência de Dados** | `NetworkX`, `Scikit-Learn`, `SciPy`, `Pandas` | Modelagem em grafo da infraestrutura do Sistema Interligado Nacional (SIN), cálculo de *Betweenness Centrality* e clusterização de focos via ST-DBSCAN. |
| **Contratos de Dados** | `Pydantic v2` | Validação de esquemas e tipagem estrita dos payloads trafegados no Kafka. |
| **Infraestrutura & DevOps** | `Docker`, `Docker Compose`, Bash Scripting | Conteinerização dos microsserviços do Druid, Kafka, Dagster e Superset, com controle de alocação de vCPU e limites de memória (*cgroups*). |
| **Engenharia de Performance** | JVM Tuning, Benchmarking | Parametrização de memória da JVM (`-Xms`, `-Xmx`, `MaxDirectMemorySize`), análise de *Garbage Collection*, testes de estresse de consultas e avaliação de cache. |
| **Análise Estatística** | Linguagem `R`, `ggplot2` | Processamento estatístico das métricas de desempenho dos ensaios e geração de gráficos de latência (P95, violinos de cache e vazão). |
| **Testes de Software** | `Pytest`, `pytest-mock` | Testes unitários de módulos matemáticos, validação de contratos de dados e testes sintáticos de consultas SQL analíticas. |

---

## 4. Arquitetura de Dados e Decisões de Engenharia

### 4.1. Camadas Medallion
O fluxo de dados foi estruturado em três níveis de processamento:
* **Bronze (Extração):** Coleta de dados brutos das fontes governamentais utilizando técnicas de *chunking* para controle de consumo de memória.
* **Silver (Dimensões Geográficas):** Padronização e limpeza das bases de referência espacial (municípios, rodovias, hospitais, terras indígenas e subestações/linhas de transmissão), gerando arquivos estruturados de dimensões.
* **Gold (Modelagem e Fato):** Aplicação de algoritmos de agrupamento espacial e cálculo de centralidade de rede, estruturando as tabelas fato (`fato_focos_incendio` e `fato_eventos_incendio`) para ingestão contínua.

### 4.2. Modelagem Dimensional e Normalização do Streaming
* **Estrutura Enxuta:** Os payloads transmitidos via Kafka e persistidos na tabela fato priorizam chaves inteiras/identificadores, métricas numéricas e atributos espaço-temporais essenciais, evitando o tráfego de campos textuais extensos (como nomes de municípios ou biomas).
* **Resolução por Lookups:** Atributos descritivos permanecem nas tabelas de dimensão, sendo consultados via tabelas de *Lookup* em memória no Apache Druid ou resolvidos na camada de apresentação (Superset), reduzindo o volume por linha a aproximadamente **0,16 KB**.

### 4.3. Indexação Espacial em Camada Prévia
* Para evitar a sobrecarga de junções espaciais (*Point-in-Polygon*) em tempo de consulta no motor OLAP, o enriquecimento geográfico foi antecipado para a etapa de processamento em Python.
* A utilização de estruturas de dados espaciais baseadas em árvores (*R-Tree* no GeoPandas) reduziu o custo de busca de geometrias para ordem logarítmica $O(\log N)$, entregando ao banco analítico dados com chaves de pertencimento já calculadas.

---

## 5. Modelagem Matemática e Algorítmica

### 5.1. Agrupamento Espaço-Temporal de Queimadas (ST-DBSCAN)
* **Objetivo:** Superar a limitação de analisar anomalias térmicas como coordenadas pontuais isoladas.
* **Método:** Aplicação do algoritmo **ST-DBSCAN** (*Spatio-Temporal DBSCAN*) para agrupar detecções vizinhas no espaço geográfico e na janela temporal de dias consecutivos.
* **Poligonização:** Utilização de *Shapely* para gerar a envoltória convexa (*Convex Hull*) de cada grupo de focos, calculando a área aproximada ($\text{km}^2$) e permitindo acompanhar o deslocamento e o perímetro do evento de queimada.

### 5.2. Modelagem Topológica da Malha de Transmissão Elétrica (NetworkX)
* **Objetivo:** Estimar o impacto da proximidade de incêndios em ativos estratégicos de geração e transmissão do Sistema Interligado Nacional (SIN).
* **Estruturação:** A rede de subestações e linhas de transmissão foi representada na forma de grafo não orientado $G = (V, E)$, onde os vértices correspondem a subestações e as arestas representam as linhas elétricas.
* **Métrica de Centralidade:** Cálculo da Centralidade de Intermediação (*Betweenness Centrality*) das subestações:
  $$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
  A métrica permitiu identificar os nós mais críticos para o fluxo global de carga elétrica, fornecendo um critério para ordenação de alertas operacionais quando ocorrem queimadas em suas imediações.

### 5.3. Validação Socioambiental: Vulnerabilidade em Terras Indígenas
* **Cálculo de Pressão Territorial:** O sistema correlaciona em tempo real a potência térmica do fogo (FRP) com os polígonos oficiais da FUNAI, diferenciando focos internos de pressões no entorno imediato (buffers).
* **Estudo de Caso Empírico:** A plataforma identificou a Terra Indígena Parque do Araguaia (Ilha do Bananal / TO) na faixa de `PRESSAO_CRITICA` em virtude da fronteira agropecuária em Formoso do Araguaia, correlacionando-se com ocorrências reais de incêndios que atingiram comunidades locais (como a Aldeia Canoanã).

---

## 6. Ensaios Experimentais e Avaliação de Desempenho

Como parte da investigação científica da Iniciação Científica, estruturou-se uma série de ensaios de planejamento de capacidade (*Capacity Planning*) do Apache Druid em ambiente conteinerizado sob diferentes condições de hardware e carga concorrente.

### 6.1. Volumetria e Ocupação em Disco
* **Volume Analítico:** Processamento de aproximadamente 3,33 milhões de focos térmicos individuais, 147 mil eventos poligonais agrupados e mais de 560 mil entidades dimensionais (hospitais, rodovias, municípios, subestações e terras indígenas), totalizando **mais de 4,05 milhões de registros**.
* **Armazenamento:** A tabela fato de 3,33 milhões de focos ocupou cerca de **566 MB** em disco, demonstrando a taxa de compressão colunar (formato nativo do Druid com LZ4 e índices bitmap).

### 6.2. Efeito da Compactação de Segmentos (DataOps)
* **Estado Fragmentado Inicial:** A ingestão contínua em pequenos intervalos gerou 6.518 micro-segmentos, acarretando sobrecarga de *file handles* e elevando a latência média de leitura para cerca de 1.624 ms em um nó de 6 núcleos.
* **Compactação:** A consolidação dos dados em segmentos unificados com granularidade temporal reduziu a latência média para **55 ms** no mesmo hardware.
* **Comparativo de Eficiência:** Sob a configuração de 4 vCPUs, a latência reduziu de 2.320 ms para 60 ms (**ganho relativo de aproximadamente 38,8 vezes**), comprovando empiricamente a importância da gestão de dados e compactação sobre o mero aumento de recursos de infraestrutura.

### 6.3. Comportamento sob Carga Concorrente e Uso de Recursos
* **Testes de Concorrência:** Simulação de 1 a 16 clientes simultâneos executando consultas agregadas no Druid.
* **Cenário Baseline (1.0 vCPU):** Apresentou saturação a partir do primeiro operador, com taxa de erro de 42,7% por *timeout* ao processar cruzamentos de geometrias complexas.
* **Cenário Ajustado (2.0 vCPUs):** Manteve operação estável, absorvendo 16 conexões simultâneas com platô de vazão em torno de **2,0 QPS** e **0% de falhas HTTP 500**.
* **Latência P95:** Situou-se entre **2,8 segundos** (sob 2 clientes) e **8,2 segundos** (sob 8 clientes) em consultas analíticas geoespaciais densas.
* **Perfil de Gargalo:** O uso de memória RAM dos contêineres permaneceu entre 70% e 80% sem eventos de *OOM Killer*, confirmando que a carga analítica geoespacial do sistema tem caráter predominantemente **CPU-Bound** (processamento de operações vetoriais e serialização).

---

## 7. Documentação de Código e Padronização

* **Governança de Ambiente (`agents.md`):** Estabelecimento de diretrizes explícitas para garantir reprodutibilidade e consistência na escrita de código (como uso obrigatório do gerenciador `uv`, validação de contratos Pydantic e preservação de esquemas dimensionais sem campos textuais soltos na tabela fato).
* **Testes Automatizados:** Implementação de testes unitários e de integração com `pytest`, verificando a integridade dos cálculos matemáticos de grafos, os contratos de payload do Kafka e a sintaxe das consultas analíticas do Superset.

---

## 8. Produção Acadêmica

1. **Artigo Científico (Formato SBC):**
   * *Título:* "Uma Arquitetura DataOps Orientada a Eventos para Processamento de Dados Geoespaciais em Tempo Real"
   * *Autores:* Gabriel Gonçalves Sampaio, Barbara Pimenta Caetano
   * *Conteúdo:* Apresentação da arquitetura desacoplada, aplicação do ST-DBSCAN e Centralidade de Intermediação, com discussão dos resultados de capacidade computacional.
2. **Relatório Final de Iniciação Científica (UNIFEI / IESTI):**
   * *Título:* "Avaliação de Desempenho do Apache Druid: Estruturação de Experimentos e Análise Comparativa"
   * *Conteúdo:* Documentação monográfica completa com referencial teórico sobre bancos colunares OLAP, metodologia experimental e análise de dados em linguagem R.
3. **Apresentação em Simpósio:**
   * Apresentação dos resultados parciais e finais em evento acadêmico institucional da UNIFEI.

---

## 9. Bullets para Currículo e Processos Seletivos (Objetivos e Diretos)

### Engenharia de Dados & Infraestrutura Analítica
* *Implementou pipeline de ingestão e análise de dados de streaming com Apache Kafka, Apache Druid e Dagster, processando mais de 4 milhões de registros geoespaciais e tabulares.*
* *Estruturou modelo analítico (Esquema Constelação) para armazenamento em banco colunar, normalizando payloads via Pydantic e reduzindo o volume em disco para 0,16 KB por registro.*
* *Conduziu ensaios de compactação de segmentos no Apache Druid, mensurando redução de latência média de 2.320 ms para 60 ms no processamento de consultas colunares.*
* *Realizou testes de estresse e planejamento de capacidade (Capacity Planning) sob concorrência de até 16 conexões simultâneas, avaliando latências P95 e utilização de CPU e memória.*
* *Conteinerizou serviços em Docker Compose e ajustou parâmetros de memória e heap da JVM para estabilização de serviços analíticos sob limites de hardware.*

### Modelagem Geoespacial & Ciência de Dados
* *Aplicou o algoritmo ST-DBSCAN e envoltória convexa (Convex Hull) em Python para agrupar 3,3 milhões de focos de queimada em 147 mil eventos poligonais dinâmicos.*
* *Modelou a malha de transmissão de energia do ONS em grafo com NetworkX, calculando a Centralidade de Intermediação de subestações para análise de vulnerabilidade a incêndios florestais.*
* *Empregou estruturas de indexação espacial (R-Tree) com GeoPandas para otimizar o tempo de busca e cruzamento de geometrias de ordem linear para logarítmica.*
* *Estruturou rotinas em linguagem R para consolidação estatística das métricas de desempenho de sistemas e geração de gráficos de latência e vazão.*

---

## 10. Resumo para Perfil / Apresentação

> *"Graduando em Engenharia da Computação pela Universidade Federal de Itajubá (UNIFEI), com experiência de Iniciação Científica em Engenharia de Dados e Processamento Distribuído. Atuou no desenvolvimento e avaliação de pipelines analíticos com Apache Kafka, Apache Druid, Dagster e Docker, com foco em dados geoespaciais e infraestrutura energética. Possui experiência prática em modelagem dimensional, algoritmos de agrupamento espaço-temporal (ST-DBSCAN), análise de redes em grafos (NetworkX) e experimentos de planejamento de capacidade e desempenho de consultas colunares."*
