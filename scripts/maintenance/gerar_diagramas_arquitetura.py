import base64
import zlib
import urllib.request
import os

def kroki_url(diagram_type, diagram_text):
    compressed = zlib.compress(diagram_text.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"https://kroki.io/{diagram_type}/png/{encoded}"

graphs = [
    # 1. Streaming Topology
    """graph TD
    subgraph Data Acquisition
        INPE[API Focos INPE] -->|JSON/CSV| PROD(Produtor Kafka)
    end

    subgraph Stream Processing Pipeline
        PROD -->|Raw Hotspots| TOPIC_RAW[Kafka Topic: focos_brutos]
        TOPIC_RAW --> PROC(Processador Espacial)
        PROC -->|Cálculo de Distâncias| PROC
        PROC -->|Tipagem Pydantic| FATO[FocoFatoPayload]
    end

    subgraph Analytical Storage
        FATO -->|Stream| TOPIC_ENRICHED[Kafka Topic: focos_enriquecidos]
        TOPIC_ENRICHED -->|MiddleManager| DRUID[(Apache Druid OLAP)]
        DRUID -->|Segmentação Colunar| HIST[Historical Nodes]
    end

    subgraph Presentation
        DRUID --> SUPERSET[Apache Superset]
        SUPERSET --> DASH1(Dashboards de Risco)
        SUPERSET --> DASH2(Análise Territorial)
    end""",
    
    # 2. Ciência de Redes
    """graph LR
    subgraph Extração ONS
        SUB(Subestações) --> GEO1(GeoPandas EPSG:4326)
        LIN(Linhas Transmissão) --> GEO2(GeoPandas EPSG:4326)
    end

    subgraph Modelagem Topológica
        GEO1 --> KDTREE[cKDTree Spatial Index]
        GEO2 --> KDTREE
        KDTREE -->|Cruzamento Espacial| ADJ[Matriz de Adjacência]
        ADJ --> GRAPH((Grafo NetworkX))
    end

    subgraph Centralidade
        GRAPH -->|Betweenness Centrality| SCORE[Score de Risco em Cascata]
        SCORE --> DIM_SUB[(Dimensão Subestações ONS)]
    end""",
    
    # 3. ST-DBSCAN
    """flowchart TD
    RAW[(Focos Brutos)] --> FILTER(Filtros de Lat/Lon e Nulos)
    FILTER --> SCALE(Normalização Escalar Espaço-Tempo)
    
    subgraph Heurística ST-DBSCAN
        SCALE --> DBSCAN[scikit-learn DBSCAN]
        DBSCAN -->|Eps: 0.02, MinPts: 3| CLUSTERS(Agrupamento por Densidade)
        CLUSTERS --> RUIDO(Descarte de Ruídos: Label -1)
    end

    subgraph Poligonização
        RUIDO --> GDF(Conversão GeoPandas)
        GDF --> CONVEX(Convex Hull - Polígonos de Área)
    end

    CONVEX --> FAT_EVT[(Fato: Eventos de Incêndio)]""",
    
    # 4. Dagster
    """graph TD
    subgraph Dagster Software-Defined Assets
        EXTR(infra_extracao) --> DIM_LINHA(dim_linhas_transmissao)
        EXTR --> DIM_SUB(dim_subestacoes)
        
        DIM_LINHA --> NET(network_centrality_model)
        DIM_SUB --> NET
        
        RAW(focos_inpe_diario) --> ST(st_dbscan_fire_events)
    end"""
]

filenames = [
    "diagrama_streaming.png",
    "diagrama_grafos.png",
    "diagrama_dbscan.png",
    "diagrama_dagster.png"
]

output_dir = "/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/academic_paper"

for i, g in enumerate(graphs):
    url = kroki_url('mermaid', g)
    out_path = os.path.join(output_dir, filenames[i])
    print(f"Downloading {filenames[i]} from {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(out_path, 'wb') as out_file:
        out_file.write(response.read())
    print(f"Saved to {out_path}")
