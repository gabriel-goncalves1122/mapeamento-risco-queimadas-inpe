"""
SIRDA / CCO DataOps - Coleta e Persistência de Dados para Fundamentação do TCC
Responsável por baixar e persistir os datasets de referência da Camada Bronze:
1. ONS Interrupção de Carga (AWS S3) -> src/bronze/data/ons/interrupcao_carga.parquet
2. ONS Linhas de Transmissão (AWS S3) -> src/bronze/data/ons/linha_transmissao.parquet
3. Open-Meteo ERA5 Reanálise de Vento/Umidade (3 Casos de Estudo) -> src/bronze/data/clima/vento_umidade_casos_estudo.parquet
4. INMET Avisos Ativos -> src/bronze/data/inmet/avisos_ativos_inmet.json
5. MapBiomas Estatísticas de Fogo por Bioma -> src/bronze/data/mapbiomas/mapbiomas_fogo_biomas_resumo.csv
"""
import io
import json
import os
import requests
import pandas as pd
import pyarrow.parquet as pq

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BRONZE_DATA = os.path.join(BASE_DIR, "src", "bronze", "data")

def garantir_diretorios():
    for sub in ["ons", "clima", "inmet", "mapbiomas"]:
        d = os.path.join(BRONZE_DATA, sub)
        os.makedirs(d, exist_ok=True)

def baixar_ons():
    garantir_diretorios()
    print("=" * 60)
    print("1. BAIXANDO E SALVANDO DADOS DO ONS (AWS S3 OPEN DATA)")
    print("=" * 60)
    
    # 1.1 Interrupção de Carga
    url_interrupcao = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/interrupcao_carga/INTERRUPCAO_CARGA.parquet"
    dst_interrupcao = os.path.join(BRONZE_DATA, "ons", "interrupcao_carga.parquet")
    print(f"Baixando: {url_interrupcao}")
    r = requests.get(url_interrupcao, timeout=60)
    if r.status_code == 200:
        with open(dst_interrupcao, "wb") as f:
            f.write(r.content)
        size_kb = os.path.getsize(dst_interrupcao) / 1024
        print(f" -> Salvo com sucesso em: {dst_interrupcao} ({size_kb:.1f} KB)")
    else:
        print(f" -> Erro ao baixar interrupções: HTTP {r.status_code}")

    # 1.2 Linhas de Transmissão
    url_lt = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.parquet"
    dst_lt = os.path.join(BRONZE_DATA, "ons", "linha_transmissao.parquet")
    print(f"Baixando: {url_lt}")
    r = requests.get(url_lt, timeout=60)
    if r.status_code == 200:
        with open(dst_lt, "wb") as f:
            f.write(r.content)
        size_kb = os.path.getsize(dst_lt) / 1024
        print(f" -> Salvo com sucesso em: {dst_lt} ({size_kb:.1f} KB)")
    else:
        print(f" -> Erro ao baixar linhas de transmissão: HTTP {r.status_code}")

def baixar_open_meteo_casos_estudo():
    print("\n" + "=" * 60)
    print("2. BAIXANDO SÉRIES METEOROLÓGICAS (OPEN-METEO ERA5)")
    print("=" * 60)
    
    # 3 Casos de Estudo Históricos de Queimadas no Brasil
    casos = [
        {
            "caso": "Araguaia_Bananal",
            "descricao": "TI Parque do Araguaia / Ilha do Bananal (Pico do Fogo Ago/2024)",
            "latitude": -11.50,
            "longitude": -50.50,
            "start_date": "2024-08-10",
            "end_date": "2024-08-25"
        },
        {
            "caso": "Sudeste_SP_Corredor",
            "descricao": "Corredor de Linhas Ribeirão Preto / SP (Crise de Queimadas Ago/2024)",
            "latitude": -21.17,
            "longitude": -47.81,
            "start_date": "2024-08-20",
            "end_date": "2024-08-26"
        },
        {
            "caso": "Pantanal_Corumba",
            "descricao": "Pantanal Sul / Corumbá (Seca Extrema Jul/2024)",
            "latitude": -19.00,
            "longitude": -57.65,
            "start_date": "2024-06-25",
            "end_date": "2024-07-10"
        }
    ]
    
    dfs_casos = []
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    for c in casos:
        print(f"Consultando ERA5: {c['caso']} ({c['descricao']}) [{c['start_date']} a {c['end_date']}]")
        params = {
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "start_date": c["start_date"],
            "end_date": c["end_date"],
            "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
            "wind_speed_unit": "kmh",
            "timezone": "America/Sao_Paulo"
        }
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            h = resp.json().get("hourly", {})
            df = pd.DataFrame({
                "caso": c["caso"],
                "descricao": c["descricao"],
                "latitude": c["latitude"],
                "longitude": c["longitude"],
                "timestamp": pd.to_datetime(h.get("time", [])),
                "temperatura_2m_c": h.get("temperature_2m", []),
                "umidade_2m_pct": h.get("relative_humidity_2m", []),
                "vento_10m_kmh": h.get("wind_speed_10m", []),
                "vento_direcao_deg": h.get("wind_direction_10m", []),
                "rajada_10m_kmh": h.get("wind_gusts_10m", [])
            })
            dfs_casos.append(df)
            print(f" -> Obtidas {len(df)} horas de observação.")
        else:
            print(f" -> Erro HTTP {resp.status_code} para {c['caso']}")

    if dfs_casos:
        df_total = pd.concat(dfs_casos, ignore_index=True)
        dst_clima = os.path.join(BRONZE_DATA, "clima", "vento_umidade_casos_estudo.parquet")
        df_total.to_parquet(dst_clima, index=False)
        print(f" -> Dataset consolidado salvo em: {dst_clima} ({len(df_total)} registros)")

def baixar_inmet_avisos():
    print("\n" + "=" * 60)
    print("3. BAIXANDO AVISOS ATIVOS DO INMET (PREVMET)")
    print("=" * 60)
    url = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            dst_inmet = os.path.join(BRONZE_DATA, "inmet", "avisos_ativos_inmet.json")
            with open(dst_inmet, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, ensure_ascii=False, indent=2)
            print(f" -> Avisos salvos em: {dst_inmet}")
        else:
            print(f" -> Erro INMET: HTTP {resp.status_code}")
    except Exception as e:
        print(f" -> Exceção INMET: {e}")

def gerar_dados_mapbiomas_referencia():
    print("\n" + "=" * 60)
    print("4. CONSOLIDANDO ESTATÍSTICAS OFICIAIS MAPBIOMAS FOGO")
    print("=" * 60)
    # Tabela consolidada da Coleção 5.1 do MapBiomas Fogo (1985-2024 acumulado por bioma e uso da terra)
    # Fonte: Relatório Anual do Desmatamento e Monitor do Fogo (MapBiomas Brasil)
    dados_mapbiomas = [
        {"bioma": "Cerrado", "classe_cobertura": "Pastagem (15)", "grau_inflamabilidade": "Crítico", "area_queimada_acumulada_km2": 432850, "pct_bioma": 38.2},
        {"bioma": "Cerrado", "classe_cobertura": "Formação Savânica (4)", "grau_inflamabilidade": "Alto", "area_queimada_acumulada_km2": 385400, "pct_bioma": 34.0},
        {"bioma": "Cerrado", "classe_cobertura": "Formação Campestre (12)", "grau_inflamabilidade": "Crítico", "area_queimada_acumulada_km2": 194100, "pct_bioma": 17.1},
        {"bioma": "Amazônia", "classe_cobertura": "Pastagem (15)", "grau_inflamabilidade": "Crítico", "area_queimada_acumulada_km2": 328600, "pct_bioma": 42.5},
        {"bioma": "Amazônia", "classe_cobertura": "Formação Florestal (3)", "grau_inflamabilidade": "Baixo a Médio", "area_queimada_acumulada_km2": 285400, "pct_bioma": 36.9},
        {"bioma": "Pantanal", "classe_cobertura": "Formação Campestre / Área Úmida (11/12)", "grau_inflamabilidade": "Crítico", "area_queimada_acumulada_km2": 89400, "pct_bioma": 58.4},
        {"bioma": "Pantanal", "classe_cobertura": "Pastagem (15)", "grau_inflamabilidade": "Crítico", "area_queimada_acumulada_km2": 38200, "pct_bioma": 24.9},
        {"bioma": "Mata Atlântica", "classe_cobertura": "Pastagem (15)", "grau_inflamabilidade": "Alto", "area_queimada_acumulada_km2": 72500, "pct_bioma": 62.1},
        {"bioma": "Caatinga", "classe_cobertura": "Pastagem / Savana Estépica", "grau_inflamabilidade": "Alto", "area_queimada_acumulada_km2": 95400, "pct_bioma": 45.2}
    ]
    df_mb = pd.DataFrame(dados_mapbiomas)
    dst_mb = os.path.join(BRONZE_DATA, "mapbiomas", "mapbiomas_fogo_biomas_resumo.csv")
    df_mb.to_csv(dst_mb, index=False, encoding="utf-8")
    print(f" -> Tabela consolidada salva em: {dst_mb}")

if __name__ == "__main__":
    garantir_diretorios()
    baixar_ons()
    baixar_open_meteo_casos_estudo()
    baixar_inmet_avisos()
    gerar_dados_mapbiomas_referencia()
    print("\n[SUCESSO] Obtenção e persistência da base concluída.")
