"""
=========================================================
MÓDULO: coletor_ons.py
---------------------------------------------------------
Função Geral: Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica.
=========================================================
"""
import requests
import json
import time

# URL base da ANEEL com um "coringa" {id} para trocarmos a camada dinamicamente
URL_BASE = "https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmiss%C3%A3o/MapServer/{id}/query"

# Dicionário mapeando o nome do arquivo final com o ID da camada na API
CAMADAS = {
    "linhas_transmissao": 1,
    "subestacoes": 3,
    "sistemas_isolados": 5
}

def extrair_camada(nome_arquivo, layer_id):
    print(f"\n🚀 Iniciando extração da camada: {nome_arquivo.upper()} (Layer {layer_id})")
    
    url = URL_BASE.format(id=layer_id)
    todas_as_features = []
    offset = 0
    limite = 1000
    
    while True:
        print(f"   Baixando registros de {offset} a {offset + limite}...")
        
        params = {
            "where": "1=1",
            "outFields": "*", # Puxa todas as colunas disponíveis!
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": limite,
            "outSR": "4326"
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"   ❌ Erro na conexão: {response.status_code}")
            break
            
        dados = response.json()
        features = dados.get("features", [])
        
        if not features:
            break
            
        todas_as_features.extend(features)
        offset += limite
        time.sleep(1) # Respeito ao servidor governamental
        
        if len(features) < limite:
            break

    if todas_as_features:
        # Empacota tudo em um GeoJSON padrão
        geojson_final = {
            "type": "FeatureCollection",
            "features": todas_as_features
        }
        
        caminho = f"data/geo/{nome_arquivo}_ons.geojson"
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(geojson_final, f, ensure_ascii=False)
            
        print(f"   ✅ Sucesso! {len(todas_as_features)} registros salvos em '{caminho}'.")
    else:
        print("   ⚠️ Nenhum dado encontrado para esta camada.")

def baixar_toda_infraestrutura():
    print("Iniciando Pipeline de Ingestão Geoespacial da ANEEL/ONS...")
    for nome, layer_id in CAMADAS.items():
        extrair_camada(nome, layer_id)
    print("\n🏁 Extração de infraestrutura elétrica concluída 100%!")

if __name__ == "__main__":
    baixar_toda_infraestrutura()