import os

docs_structure = {
    "docs": {
        "README.md": """# Documentação Oficial: CCO DataOps 🚀

Bem-vindo(a) ao projeto CCO DataOps! Se você é um desenvolvedor Júnior chegando agora, respire fundo: este projeto é moderno, robusto e usa os melhores paradigmas de Engenharia de Dados e Ciência de Dados.

Nesta documentação, vamos te pegar pela mão e explicar como os dados saem do INPE/ONS e viram insights em tempo real e polígonos inteligentes.

### 📚 Índice
1. [Introdução e Arquitetura](./01_introducao/arquitetura.md)
2. [Modelagem e ETL (Snowflake)](./02_dados_e_etl/modelo_snowflake.md)
3. [Streaming com Kafka](./03_streaming/kafka_e_druid.md)
4. [Ciência de Dados Avançada](./04_ciencia_de_dados/grafos_networkx.md)
5. [DataOps e Orquestração](./05_dataops/orquestracao_dagster.md)
""",
        "01_introducao": {
            "arquitetura.md": """# Arquitetura do Projeto 🏗️

Nós não construímos um sistema simples. Construímos uma esteira analítica orientada a eventos.

## O Que Resolvemos?
Monitoramos focos de incêndio florestal cruzando espacialmente com infraestruturas críticas do Brasil (Linhas de Transmissão, Hospitais, Terras Indígenas). O objetivo é prever ameaças e disparar alertas.

## Componentes Chave:
1. **Produtores (Python)**: Lêem os dados do INPE e jogam no Apache Kafka.
2. **Processador (Streaming)**: Consome do Kafka, calcula distâncias espaciais e índices de ameaça em tempo real.
3. **Apache Druid (Banco OLAP)**: Um banco projetado para Big Data temporal. Ele engole os dados em milissegundos.
4. **Dagster (Orquestrador)**: O coração do DataOps. Ele garante que os scripts batch (ETLs espaciais) rodem na ordem certa.
5. **Apache Superset**: Nosso front-end de BI para os Dashboards geoespaciais.
"""
        },
        "02_dados_e_etl": {
            "modelo_snowflake.md": """# Modelo Snowflake ❄️

Se você já estudou SQL, deve conhecer a modelagem "Star Schema" (Estrela). Aqui usamos o **Snowflake** (Floco de Neve).

### Por que Snowflake?
Em streaming (Kafka), trafegar textos longos (ex: "São José dos Campos", "SUBESTAÇÃO X") para cada um dos milhares de focos por minuto derruba a rede e custa caro em armazenamento.

### A Tabela Fato
A nossa Tabela Fato (`FATO_FOCOS_INCENDIO`) só tem 3 coisas:
1. **Timestamp**: `data_hora`
2. **IDs (Foreign Keys)**: `fk_municipio`, `fk_subestacao`, etc.
3. **Métricas Numericas**: `potencia_radiativa`, `indice_ameaca_subestacao`, etc.

As dimensões reais (nomes de cidades, coordenadas dos polígonos) ficam em planilhas/tabelas separadas que o Superset e o Druid cruzam via `JOIN` ou `Lookups` na hora de exibir o gráfico!
""",
            "etl_geospacial.md": """# ETL Geoespacial 🗺️

Temos vários scripts em `src/etl/pipelines/`. Eles rodam apenas 1x por semana ou por mês (lote/batch).

### O que eles fazem?
Eles pegam arquivos horríveis e mal formatados do governo (APIs ONS, CNES, IBGE) e limpam.
Usamos o `geopandas` e `shapely` para garantir que toda tabela tenha colunas padrão como:
- `latitude` e `longitude`
- `path_json` (para visualização no Superset/Deck.gl e reconstrução interna)

Esses scripts não rodam soltos. Eles são Assets no **Dagster**!
"""
        },
        "03_streaming": {
            "kafka_e_druid.md": """# Streaming: Kafka e Druid ⚡

Aqui é onde a mágica do Tempo Real acontece (`src/streaming/`).

## O Fluxo
1. **`produtor_focos.py`**: Pega os dados mais recentes de satélites.
2. O **Apache Kafka** atua como um "cano de água". Ele apenas transporta a água muito rápido.
3. **`processador.py`**: É o filtro no meio do cano. Ele pega o foco, calcula matematicamente (usando as fórmulas em `calculators.py`) o quão perigoso ele é para uma rodovia ou terra indígena próxima. E gera o nosso **FocoFatoPayload** limpo.
4. O Kafka manda para o **Apache Druid**.

### Druid
O Druid é um banco de dados analítico. Ele não serve para fazer `UPDATE` em um cadastro de usuário. Ele serve para fazer um `SELECT COUNT(*)` em 100 milhões de registros em 0.01 segundos.
"""
        },
        "04_ciencia_de_dados": {
            "grafos_networkx.md": """# Ciência de Redes no SIN 🕸️

**Script**: `src/science/network_builder.py`

### O que é?
O Sistema Interligado Nacional (SIN) é uma gigantesca teia de aranha (linhas de transmissão conectando subestações).

### O que fizemos?
Usamos `scipy.spatial.cKDTree` para encontrar espacialmente quais linhas tocam em quais subestações. Com isso, construímos um Grafo matemático usando `NetworkX`.

### Betweenness Centrality
O algoritmo calcula a "Centralidade de Intermediação" de cada Subestação. Ou seja, se o fogo desligar a "Subestação X", quantas cidades ficam sem energia por efeito cascata? O algoritmo nos diz exatamente o Score de Risco de cada subestação de 0 a 100!
""",
            "clusterizacao_st_dbscan.md": """# ST-DBSCAN: Fogo com Inteligência 🧠

**Script**: `src/science/st_dbscan_clustering.py`

### O Problema
O satélite captura um pixel quente. No dia seguinte ele captura outro do lado. Eles não são dois incêndios independentes, é o mesmo incêndio se alastrando!

### A Solução
Usamos Inteligência Artificial não-supervisionada (`scikit-learn DBSCAN`). Modificamos o algoritmo para ser "Espaço-Temporal" (ST-DBSCAN).
- Ele olha para os focos num raio de 2km e num intervalo de até 2 dias.
- Se eles são vizinhos no espaço e no tempo, o algoritmo une todos eles em um único **Evento de Incêndio**.

Em seguida, o `geopandas` usa Matemática Computacional (Convex Hull) para traçar um polígono exato englobando toda a área queimada.
"""
        },
        "05_dataops": {
            "orquestracao_dagster.md": """# Dagster: O Maestro 🎼

**Onde?** `src/orchestration/repo.py`

Antigamente o pessoal rodava scripts de ETL usando o `cron` do Linux. Se um falhasse, o da frente que dependia dele rodava vazio e quebrava o sistema inteiro.

No DataOps moderno, nós usamos o **Dagster**.
Ele transforma funções Python em `@assets` (Ativos de Dados).

### Grafo de Dependências
Nós definimos: "A `dim_linhas_transmissao` depende do `infra_extracao` baixar o dado". 
O Dagster monta um mapa visual (um grafo). Se o passo 1 falhar, ele nem tenta o passo 2. Ele mostra o log de erro lindamente na porta `http://localhost:3000`.

Isso garante que toda a esteira do CCO DataOps (do dado cru até o ST-DBSCAN complexo) seja monitorada e segura.
""",
            "docker_infra.md": """# Infraestrutura com Docker 🐳

Todo esse ecossistema não roda jogado no seu computador. Tudo está encapsulado.

No arquivo `docker-compose.yaml` raiz do projeto, temos contêineres para:
- Kafka (Mensageria)
- PostgreSQL (Metadados do Superset e Dagster)
- Zookeeper (Coordenação do Druid e Kafka)
- Apache Druid (Router, Broker, Historical, Coordinator, MiddleManager)
- Apache Superset (BI)
- Dagster (Orquestração DataOps)

### Cuidados com Hardware
Para máquinas como i5 com 16GB de RAM, nós inserimos bloqueios finos `deploy.resources.limits` no `docker-compose.yaml`. Isso significa que o Druid jamais "roubará" mais RAM do que estipulamos, evitando que sua máquina hospedeira congele (*OOMKilled*).
"""
        }
    }
}

base_path = '/home/gabriel/Documentos/UNIFEI/IC - DataOps'

def create_structure(base, structure):
    for name, content in structure.items():
        path = os.path.join(base, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

create_structure(base_path, docs_structure)
print("✅ Diretório de documentação 'docs/' gerado com sucesso!")
