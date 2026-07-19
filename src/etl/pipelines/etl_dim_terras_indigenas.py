"""
=========================================================
MÓDULO: etl_dim_terras_indigenas.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
import os
import json
import math
import pandas as pd
import geopandas as gpd

from shapely.geometry import shape
from shapely.ops import unary_union

from src.config.constants import DIMENSIONS_DIR, EPSG_METRICO, GEO_DIR, NOT_INFORMED, RAW_DIR
from src.etl.utils.base import BaseETL
from src.etl.utils.spatial_dimensions import carregar_municipios_geo
from src.utils.cleaners import limpar_texto_druid
from src.etl.utils.geo_helpers import geometry_para_path_json

RAW_DIR = str(RAW_DIR)
GEO_DIR = str(GEO_DIR)
PROCESSED_DIR = str(DIMENSIONS_DIR)

FILE_CSV = os.path.join(RAW_DIR, 'tis_poligonais.csv')
FILE_GEOJSON = os.path.join(GEO_DIR, 'mapa_terras_indigenas.geojson')
OUTPUT_CSV = os.path.join(PROCESSED_DIR, 'dim_terras_indigenas.csv')

class ETLDimTerrasIndigenas(BaseETL):
    def __init__(self):
        super().__init__(
            input_path=FILE_GEOJSON,
            output_path=OUTPUT_CSV
        )

    def _limpar_codigo(self, valor):
        if pd.isna(valor): return "NAO INFORMADO"
        texto = str(valor).strip().replace('"', '').replace('\n', '').replace('\r', '')
        if texto.endswith('.0'): texto = texto[:-2]
        return texto if texto else "NAO INFORMADO"

    def _limpar_numero(self, valor, default=0.0):
        try:
            if pd.isna(valor): return default
            texto = str(valor).strip().replace(',', '.')
            numero = float(texto)
            if math.isnan(numero) or math.isinf(numero): return default
            return numero
        except Exception: return default

    def _classificar_area_ti(self, area_hectares):
        if area_hectares >= 1000000: return "MUITO_GRANDE"
        if area_hectares >= 100000: return "GRANDE"
        if area_hectares >= 10000: return "MEDIA"
        if area_hectares > 0: return "PEQUENA"
        return "NAO_INFORMADA"

    def _normalizar_sim_nao(self, valor):
        texto = limpar_texto_druid(valor)
        if texto in {"SIM", "S", "YES", "Y"}: return "SIM"
        if texto in {"NAO", "N", "NO"}: return "NAO"
        return "NAO_INFORMADO"

    def _classificar_regularizacao(self, estagio):
        texto = limpar_texto_druid(estagio)
        if "REGULARIZADA" in texto: return "REGULARIZADA"
        if "DECLARADA" in texto: return "DECLARADA"
        if "DELIMITADA" in texto: return "DELIMITADA"
        if "IDENTIFICADA" in texto or "EM ESTUDO" in texto: return "EM_ESTUDO_IDENTIFICACAO"
        return texto if texto != "NAO INFORMADO" else "NAO_INFORMADO"

    def _classificar_prioridade_funai(self, estagio_regularizacao, em_faixa_fronteira, area_hectares):
        if em_faixa_fronteira == "SIM" and area_hectares >= 100000: return "ALTA_PRIORIDADE"
        if estagio_regularizacao != "REGULARIZADA": return "ALTA_PRIORIDADE"
        if area_hectares >= 100000: return "MEDIA_PRIORIDADE"
        return "MONITORAMENTO"

    def _geometria_valida_para_wkt(self, geom):
        if geom is None or geom.is_empty: return None
        try:
            if not geom.is_valid: geom = geom.buffer(0)
            return None if geom.is_empty else geom
        except Exception: return None

    def _calcular_municipios_interceptados(self, gdf):
        municipios = carregar_municipios_geo(GEO_DIR).to_crs(epsg=EPSG_METRICO)
        terras = gdf[['codigo_ti', 'geometry']].copy().to_crs(epsg=EPSG_METRICO)

        resultado = pd.DataFrame({'codigo_ti': gdf['codigo_ti'].astype(str)})
        resultado['codigos_ibge_interceptados'] = NOT_INFORMED
        resultado['codigo_ibge_principal'] = NOT_INFORMED
        resultado['qtd_municipios_interceptados'] = 0
        resultado['percentual_area_interceptada'] = 0.0
        resultado['match_status_municipios'] = 'SEM_INTERSECAO'

        if terras.empty or municipios.empty:
            return resultado

        areas_ti = terras.assign(area_ti_km2=terras.geometry.area / 1_000_000)[['codigo_ti', 'area_ti_km2']]
        inter = gpd.overlay(
            terras[['codigo_ti', 'geometry']],
            municipios[['codigo_ibge', 'geometry']],
            how='intersection',
            keep_geom_type=False,
        )

        if not inter.empty:
            inter['area_intersecao_km2'] = (inter.geometry.area / 1_000_000).round(6)
            inter = inter[inter['area_intersecao_km2'] > 0].copy()

        if not inter.empty:
            inter = inter.merge(areas_ti, on='codigo_ti', how='left')
            inter['percentual_area_ti'] = (
                (inter['area_intersecao_km2'] / inter['area_ti_km2']).fillna(0) * 100
            ).round(6)
            inter = inter.sort_values(['codigo_ti', 'area_intersecao_km2'], ascending=[True, False])

            registros = []
            for codigo_ti, grupo in inter.groupby('codigo_ti', sort=False):
                codigos = list(dict.fromkeys(grupo['codigo_ibge'].astype(str).tolist()))
                percentual = min(round(float(grupo['percentual_area_ti'].sum()), 6), 100.0)
                registros.append({
                    'codigo_ti': codigo_ti,
                    'codigos_ibge_interceptados': '|'.join(codigos),
                    'codigo_ibge_principal': codigos[0] if codigos else NOT_INFORMED,
                    'qtd_municipios_interceptados': len(codigos),
                    'percentual_area_interceptada': percentual,
                    'match_status_municipios': 'OK_INTERSECAO' if percentual >= 95 else 'INTERSECAO_PARCIAL',
                })

            resultado = resultado.drop(columns=[
                'codigos_ibge_interceptados',
                'codigo_ibge_principal',
                'qtd_municipios_interceptados',
                'percentual_area_interceptada',
                'match_status_municipios',
            ]).merge(pd.DataFrame(registros), on='codigo_ti', how='left')
            resultado['codigos_ibge_interceptados'] = resultado['codigos_ibge_interceptados'].fillna(NOT_INFORMED)
            resultado['codigo_ibge_principal'] = resultado['codigo_ibge_principal'].fillna(NOT_INFORMED)
            resultado['qtd_municipios_interceptados'] = resultado['qtd_municipios_interceptados'].fillna(0).astype(int)
            resultado['percentual_area_interceptada'] = resultado['percentual_area_interceptada'].fillna(0.0)
            resultado['match_status_municipios'] = resultado['match_status_municipios'].fillna('SEM_INTERSECAO')

        sem_intersecao = resultado['codigo_ibge_principal'] == NOT_INFORMED
        if sem_intersecao.any():
            terras_sem = terras[terras['codigo_ti'].isin(resultado.loc[sem_intersecao, 'codigo_ti'])]
            nearest = gpd.sjoin_nearest(
                terras_sem[['codigo_ti', 'geometry']],
                municipios[['codigo_ibge', 'geometry']],
                how='left',
            ).drop_duplicates(subset=['codigo_ti'])
            mapa_fallback = nearest.set_index('codigo_ti')['codigo_ibge'].to_dict()
            for idx, row in resultado[sem_intersecao].iterrows():
                codigo = mapa_fallback.get(row['codigo_ti'], NOT_INFORMED)
                if codigo != NOT_INFORMED:
                    resultado.loc[idx, 'codigos_ibge_interceptados'] = codigo
                    resultado.loc[idx, 'codigo_ibge_principal'] = codigo
                    resultado.loc[idx, 'qtd_municipios_interceptados'] = 1
                    resultado.loc[idx, 'match_status_municipios'] = 'FALLBACK_MUNICIPIO_PROXIMO'

        return resultado

    def extract(self) -> gpd.GeoDataFrame:
        if not os.path.exists(FILE_GEOJSON): raise FileNotFoundError(f"GeoJSON não encontrado: {FILE_GEOJSON}")
        if not os.path.exists(FILE_CSV): raise FileNotFoundError(f"CSV não encontrado: {FILE_CSV}")

        # 1. Carregar Geometrias e agrupar por unary_union
        with open(FILE_GEOJSON, 'r', encoding='utf-8') as f: geojson_data = json.load(f)
        
        dicionario_geo = {}
        for feature in geojson_data.get('features', []):
            codigo_ti = self._limpar_codigo(feature.get('properties', {}).get('codigo_ti', ''))
            if codigo_ti == "NAO INFORMADO": continue
            try:
                geom = self._geometria_valida_para_wkt(shape(feature.get('geometry')))
                if geom: dicionario_geo.setdefault(codigo_ti, []).append(geom)
            except Exception: continue

        registros_geo = []
        for codigo_ti, geoms in dicionario_geo.items():
            geom_unificada = self._geometria_valida_para_wkt(unary_union(geoms))
            if not geom_unificada: continue
            registros_geo.append({
                'codigo_ti': codigo_ti,
                'geometry': geom_unificada
            })
        
        gdf_geo = gpd.GeoDataFrame(registros_geo, crs="EPSG:4326")

        # 2. Carregar atributos CSV
        df_csv = pd.read_csv(FILE_CSV, dtype=str)
        df_csv['codigo_ti'] = df_csv['terrai_codigo'].apply(self._limpar_codigo)

        renames = {
            'terrai_nome': 'nome_terra_indigena', 'etnia_nome': 'etnia',
            'municipio_nome': 'municipios', 'uf_sigla': 'estado_sigla',
            'superficie_perimetro_ha': 'area_hectares', 'fase_ti': 'estagio_regularizacao',
            'modalidade_ti': 'modalidade', 'cr': 'coordenacao_regional',
            'faixa_fronteira': 'em_faixa_fronteira'
        }
        df_csv = df_csv.rename(columns=renames)
        
        colunas_necessarias = ['codigo_ti', 'nome_terra_indigena', 'etnia', 'municipios', 'estado_sigla',
                               'area_hectares', 'estagio_regularizacao', 'modalidade', 'coordenacao_regional', 'em_faixa_fronteira']
        
        for col in colunas_necessarias:
            if col not in df_csv.columns: df_csv[col] = "NAO INFORMADO"
            elif col in ['nome_terra_indigena', 'etnia', 'municipios', 'estado_sigla', 'estagio_regularizacao', 'modalidade', 'coordenacao_regional']:
                df_csv[col] = df_csv[col].apply(limpar_texto_druid)

        df_csv['area_hectares'] = df_csv['area_hectares'].apply(self._limpar_numero).round(2)
        df_csv['em_faixa_fronteira'] = df_csv['em_faixa_fronteira'].apply(self._normalizar_sim_nao)
        df_csv['estagio_regularizacao'] = df_csv['estagio_regularizacao'].apply(self._classificar_regularizacao)
        df_csv_final = df_csv.drop_duplicates(subset=['codigo_ti'])[colunas_necessarias]

        # Merge
        df_merged = pd.merge(df_csv_final, gdf_geo, on='codigo_ti', how='inner')
        return gpd.GeoDataFrame(df_merged, geometry='geometry', crs="EPSG:4326")

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        centroides = gdf.to_crs(epsg=EPSG_METRICO).geometry.centroid.to_crs(epsg=4326)
        gdf['latitude'] = centroides.y.round(6)
        gdf['longitude'] = centroides.x.round(6)
        gdf['path_json'] = gdf.geometry.apply(geometry_para_path_json)

        gdf['classe_area_ti'] = gdf['area_hectares'].apply(self._classificar_area_ti)
        gdf['prioridade_funai'] = gdf.apply(lambda r: self._classificar_prioridade_funai(r['estagio_regularizacao'], r['em_faixa_fronteira'], r['area_hectares']), axis=1)
        rel_municipios = self._calcular_municipios_interceptados(gdf)
        gdf = gdf.merge(rel_municipios, on='codigo_ti', how='left')

        gdf = gdf.fillna("NAO INFORMADO")

        colunas_finais = [
            'codigo_ti', 'nome_terra_indigena', 'etnia', 'estado_sigla',
            'area_hectares', 'classe_area_ti', 'estagio_regularizacao', 'modalidade',
            'coordenacao_regional', 'em_faixa_fronteira', 'prioridade_funai',
            'codigos_ibge_interceptados', 'codigo_ibge_principal',
            'qtd_municipios_interceptados', 'percentual_area_interceptada',
            'latitude', 'longitude', 'path_json'
        ]
        return pd.DataFrame(gdf[colunas_finais])

def main():
    etl = ETLDimTerrasIndigenas()
    etl.execute()


if __name__ == "__main__":
    main()
