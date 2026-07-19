"""
=========================================================
MÓDULO: network_builder.py
---------------------------------------------------------
Função Geral: Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica.
=========================================================
"""
import os
import json
import pandas as pd
import numpy as np
import networkx as nx
from shapely.geometry import LineString, MultiLineString
from scipy.spatial import cKDTree
from src.config.constants import DIMENSIONS_DIR

DIMENSIONS_DIR = str(DIMENSIONS_DIR)


def _coord_valida(valor):
    return (
        isinstance(valor, list)
        and len(valor) >= 2
        and all(isinstance(v, (int, float)) for v in valor[:2])
    )


def _line_string_ou_none(coords):
    pontos = [(float(c[0]), float(c[1])) for c in coords if _coord_valida(c)]
    if len(pontos) < 2:
        return None
    return LineString(pontos)


def path_json_para_linhas(valor):
    """
    Reconstrói as linhas ONS a partir do contrato path_json usado no Druid.
    O grafo precisa apenas dos endpoints; WKT não deve ser exigido no CSV público.
    """
    try:
        data = json.loads(str(valor))
        if not data:
            return None
        if isinstance(data, list) and data and _coord_valida(data[0]):
            return _line_string_ou_none(data)
        linhas = [_line_string_ou_none(linha) for linha in data if isinstance(linha, list)]
        linhas = [linha for linha in linhas if linha is not None]
        if not linhas:
            return None
        return linhas[0] if len(linhas) == 1 else MultiLineString(linhas)
    except Exception:
        return None

def calculate_network_centrality():
    """
    Constrói um Grafo Matemático do Sistema Elétrico e calcula o Risco de Cascata.
    
    Explicação do Algoritmo:
    1. Usa uma KDTree (scipy.spatial) das coordenadas das Subestações para cruzamento ultrarrápido.
    2. Identifica os vértices extremos das Linhas de Transmissão (LineStrings).
    3. Conecta as subestações mais próximas das pontas da linha, gerando arestas matemáticas (Edges).
    4. Usa `networkx.betweenness_centrality` para medir quantas vezes um nó (Subestação) atua
       como ponte no caminho mais curto entre outros dois nós. 
    5. Nós com alto Betweenness recebem 'Risco de Cascata' crítico, pois se um incêndio destruí-los,
       várias regiões do Brasil ficarão isoladas eletricamente (Blackout sistêmico).
    """
    print("🌐 Iniciando Construção do Grafo do SIN (Sistema Interligado Nacional)...")
    
    subestacoes_file = os.path.join(DIMENSIONS_DIR, 'dim_ons_subestacoes.csv')
    linhas_file = os.path.join(DIMENSIONS_DIR, 'dim_ons_linhas_transmissao.csv')
    
    if not os.path.exists(subestacoes_file) or not os.path.exists(linhas_file):
        print("⚠️ Arquivos base não encontrados. Execute o ETL das infraestruturas primeiro.")
        return

    df_sub = pd.read_csv(subestacoes_file)
    df_lin = pd.read_csv(linhas_file)
    
    print(f"📍 Subestações (Nós): {len(df_sub)}")
    print(f"🛤️ Linhas de Transmissão (Arestas potenciais): {len(df_lin)}")

    # 1. Preparar KDTree das Subestações para cruzamento espacial rápido
    coords_sub = df_sub[['longitude', 'latitude']].values
    tree = cKDTree(coords_sub)
    
    # 2. Extrair os "endpoints" (pontos de início e fim) de cada linha
    edges = []
    
    for _, row in df_lin.iterrows():
        try:
            geom = path_json_para_linhas(row['path_json'])
            if geom is None:
                continue
            if geom.geom_type == 'LineString':
                coords = list(geom.coords)
                p1, p2 = coords[0], coords[-1]
                
                # Achar a subestação mais próxima de p1 e p2
                dist1, idx1 = tree.query(p1)
                dist2, idx2 = tree.query(p2)
                
                # Limite empírico de ~5km (0.05 graus aproximado)
                if dist1 < 0.05 and dist2 < 0.05 and idx1 != idx2:
                    sub1_id = df_sub.iloc[idx1]['id_subestacao']
                    sub2_id = df_sub.iloc[idx2]['id_subestacao']
                    edges.append((sub1_id, sub2_id))
            elif geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    coords = list(line.coords)
                    p1, p2 = coords[0], coords[-1]
                    dist1, idx1 = tree.query(p1)
                    dist2, idx2 = tree.query(p2)
                    if dist1 < 0.05 and dist2 < 0.05 and idx1 != idx2:
                        sub1_id = df_sub.iloc[idx1]['id_subestacao']
                        sub2_id = df_sub.iloc[idx2]['id_subestacao']
                        edges.append((sub1_id, sub2_id))
        except Exception:
            continue
            
    print(f"🔗 Arestas inferidas via cruzamento espacial: {len(edges)}")
    
    # 3. Construir Grafo e calcular Centralidade
    G = nx.Graph()
    G.add_edges_from(edges)
    
    print("🧮 Calculando Betweenness Centrality (isso pode levar alguns segundos)...")
    betweenness = nx.betweenness_centrality(G)
    
    # 4. Acoplar resultados de volta ao DataFrame de Subestações
    df_sub['betweenness_score'] = df_sub['id_subestacao'].map(betweenness).fillna(0.0)
    
    # Normalizar o score para ficar interpretável (0 a 100)
    max_score = df_sub['betweenness_score'].max()
    if max_score > 0:
        df_sub['betweenness_score_norm'] = (df_sub['betweenness_score'] / max_score) * 100
    else:
        df_sub['betweenness_score_norm'] = 0.0

    # Classificar o Risco de Queda em Cascata
    def classify_cascade_risk(score):
        if score >= 80: return "EXTREMO"
        if score >= 50: return "ALTO"
        if score >= 20: return "MEDIO"
        if score > 0: return "BAIXO"
        return "ISOLADO"
        
    df_sub['risco_cascata'] = df_sub['betweenness_score_norm'].apply(classify_cascade_risk)
    
    # Salvar arquivo enriquecido
    df_sub.to_csv(subestacoes_file, index=False)
    
    print(f"✅ Análise de Grafos concluída!")
    print(f"🏆 Top 3 Subestações Críticas:")
    top_3 = df_sub.sort_values(by='betweenness_score_norm', ascending=False).head(3)
    for _, row in top_3.iterrows():
        print(f"   - {row['nome_subestacao']} (Score: {row['betweenness_score_norm']:.2f})")

if __name__ == '__main__':
    calculate_network_centrality()
