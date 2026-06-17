"""
=========================================================
MÓDULO: st_dbscan_clustering.py
---------------------------------------------------------
Função Geral: Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica.
=========================================================
"""
import os
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
from sklearn.cluster import DBSCAN
import time
from src.config.constants import FACTS_DIR, RAW_DIR

RAW_DIR = str(RAW_DIR)
PROCESSED_DIR = str(FACTS_DIR)

def processar_st_dbscan():
    """
    Agrupa pontos isolados de incêndio em polígonos de 'Eventos' utilizando ST-DBSCAN.
    
    Explicação do Algoritmo:
    Diferente de agrupamentos por K-Means, o ST-DBSCAN considera tanto a densidade espacial
    (distância física em graus geográficos) quanto a densidade temporal (tempo em dias).
    1. Os dados brutos são filtrados.
    2. O tempo (DataHora) é convertido em dias contínuos e escalonado matematicamente.
    3. O scikit-learn DBSCAN agrupa registros próximos no mapa E no tempo.
    4. Bibliotecas espaciais (GeoPandas/Shapely) calculam a Envoltória Convexa (Convex Hull)
       envolvendo os pontos externos do cluster para gerar o polígono final da área queimada.
    """
    print("🔥 Iniciando ST-DBSCAN para descoberta de Eventos de Incêndio...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    input_file = os.path.join(RAW_DIR, 'focos_incendio_brutos.csv')
    output_file = os.path.join(PROCESSED_DIR, 'fogo_eventos_stdbscan.csv')
    
    if not os.path.exists(input_file):
        print("⚠️ Arquivo bruto de focos não encontrado.")
        return
        
    print("📥 Lendo focos de calor...")
    # Lendo apenas as colunas essenciais para o clustering (reduz uso de RAM)
    df = pd.read_csv(input_file, usecols=['Latitude', 'Longitude', 'DataHora', 'FRP'], nrows=500000) 
    # Limitando a 500k para não estourar a RAM do i5 de imediato, já que scikit-learn DBSCAN aloca memória
    
    df = df.dropna(subset=['Latitude', 'Longitude', 'DataHora'])
    df['datahora_dt'] = pd.to_datetime(df['DataHora'])
    
    # Filtrar dados absurdos
    df = df[(df['Latitude'] >= -35) & (df['Latitude'] <= 6) & (df['Longitude'] >= -75) & (df['Longitude'] <= -30)]
    
    print(f"📍 Total de focos para processamento: {len(df)}")
    
    # 1. Transformação de Coordenadas e Tempo para o ST-DBSCAN
    # A sacada é escalar o tempo para que tenha a mesma "unidade de penalidade" que a distância espacial.
    # Vamos converter o tempo para dias.
    min_time = df['datahora_dt'].min()
    df['tempo_dias'] = (df['datahora_dt'] - min_time).dt.total_seconds() / (24 * 3600)
    
    # 1 Grau de latitude ~ 111 km. 
    # Queremos agrupar fogos que estão a no máximo ~2km (0.02 graus) e ocorreram num raio de 2 dias.
    # O scikit-learn DBSCAN aceita pesos diferentes ou podemos padronizar.
    # Vamos escalar os eixos:
    # Eixo X (lon) e Y (lat) permanecem. Eixo T (tempo) será multiplicado por um fator.
    # Fator: se 0.02 graus = limite_espacial, e 2 dias = limite_temporal.
    # Então 1 dia equivale a 0.01 graus. Fator tempo = 0.01
    
    df['tempo_escalado'] = df['tempo_dias'] * 0.01
    
    X = df[['Longitude', 'Latitude', 'tempo_escalado']].values
    
    print("🧠 Rodando ST-DBSCAN (scikit-learn)...")
    start_time = time.time()
    
    # Eps = 0.02 (aproximadamente 2.2 km)
    # Min_samples = 3 (mínimo de 3 detecções de satélite para virar um evento)
    db = DBSCAN(eps=0.02, min_samples=3, n_jobs=-1).fit(X)
    
    print(f"⏱️ Clustering finalizado em {time.time() - start_time:.2f} segundos.")
    
    df['event_id'] = db.labels_
    
    # Descartar ruídos (pontos soltos que não viraram clusters: label == -1)
    df_clusters = df[df['event_id'] != -1].copy()
    
    print(f"🌪️ Foram identificados {df_clusters['event_id'].nunique()} Eventos Dinâmicos de Incêndio!")
    
    # 2. Agregação por Cluster (Gerar Polígonos Convex Hull)
    print("📐 Gerando Polígonos (Convex Hull) para cada Evento...")
    
    gdf = gpd.GeoDataFrame(df_clusters, geometry=gpd.points_from_xy(df_clusters.Longitude, df_clusters.Latitude), crs="EPSG:4326")
    
    # Agrupar por event_id e criar a geometria
    eventos = []
    
    for event_id, grupo in gdf.groupby('event_id'):
        pontos = grupo.geometry.tolist()
        
        # Um Convex Hull exige pelo menos 3 pontos não colineares
        if len(pontos) >= 3:
            multiponto = MultiPoint(pontos)
            poligono = multiponto.convex_hull
            # Se for colinear, vira uma linha. Vamos usar buffer p/ garantir polígono caso aconteça.
            if poligono.geom_type in ['Point', 'LineString']:
                poligono = poligono.buffer(0.005)
        else:
            poligono = MultiPoint(pontos).buffer(0.005)
            
        data_inicio = grupo['datahora_dt'].min()
        data_fim = grupo['datahora_dt'].max()
        duracao_dias = (data_fim - data_inicio).total_seconds() / (24 * 3600)
        
        eventos.append({
            'fire_event_id': f"EVT_{event_id}",
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'duracao_dias': duracao_dias,
            'total_focos': len(grupo),
            'soma_frp': grupo['FRP'].sum(),
            'geometria_wkt': poligono.wkt
        })
        
    df_eventos = pd.DataFrame(eventos)
    df_eventos.to_csv(output_file, index=False)
    
    print(f"✅ Salvo em: {output_file}")
    if not df_eventos.empty:
        print("\n🏆 Top 3 Eventos mais longos:")
        print(df_eventos.sort_values(by='duracao_dias', ascending=False).head(3)[['fire_event_id', 'duracao_dias', 'total_focos']])

if __name__ == '__main__':
    processar_st_dbscan()
