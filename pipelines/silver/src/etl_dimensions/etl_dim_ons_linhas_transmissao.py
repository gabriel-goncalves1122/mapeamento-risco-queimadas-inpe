"""
=========================================================
MÓDULO: etl_dim_ons_linhas_transmissao.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
import os
import re
import pandas as pd

from config.constants import DIMENSIONS_DIR, EPSG_METRICO, ANEEL_DIR
from pipelines.silver.utils.base import BaseETL
from pipelines.silver.utils.string_helpers import limpar_codigo, extrair_popup_valor, extrair_uf_nome_linha
from pipelines.silver.utils.df_helpers import limpar_numero
from pipelines.silver.utils.geo_helpers import limpar_linestring_geometry, geometry_para_path_json, adicionar_centroides

ANEEL_DIR = str(ANEEL_DIR)
DIMENSIONS_DIR = str(DIMENSIONS_DIR)

class ETLDimLinhasTransmissao(BaseETL):
    def __init__(self):
        super().__init__(
            input_path=os.path.join(ANEEL_DIR, 'linhas_transmissao_ons.geojson'),
            output_path=os.path.join(DIMENSIONS_DIR, 'dim_ons_linhas_transmissao.csv')
        )

    def _extrair_numero_texto(self, texto):
        if texto is None or pd.isna(texto): return 0.0
        t = str(texto).upper().replace(',', '.')
        t = re.sub(r'(\d+)P(\d+)', r'\1.\2', t)
        match = re.search(r'(\d+(?:\.\d+)?)', t)
        return limpar_numero(match.group(1)) if match else 0.0

    def _extrair_tensao_popup_ou_nome(self, row):
        tensao = self._extrair_numero_texto(extrair_popup_valor(row.get('PopupInfo', ''), 'Tensão'))
        if tensao > 0: return tensao
        nome_texto = str(row.get('Name', '')).upper().replace(',', '.')
        nome_texto = re.sub(r'(\d+)P(\d+)', r'\1.\2', nome_texto)
        match = re.search(r'LT\s+(\d+(?:\.\d+)?)\s*KV', nome_texto) or re.search(r'(\d+(?:\.\d+)?)\s*KV', nome_texto)
        return limpar_numero(match.group(1)) if match else 0.0

    def _extrair_extensao_popup(self, row):
        return self._extrair_numero_texto(extrair_popup_valor(row.get('PopupInfo', ''), 'Extensão'))

    def _classificar_tensao(self, tensao_kv):
        if tensao_kv >= 500: return "EXTRA_ALTA"
        if tensao_kv >= 230: return "ALTA"
        if tensao_kv >= 69: return "MEDIA"
        return "BAIXA" if tensao_kv > 0 else "NAO_INFORMADO"

    def _classificar_extensao(self, extensao_km):
        if extensao_km >= 200: return "MUITO_LONGA"
        if extensao_km >= 50: return "LONGA"
        if extensao_km >= 10: return "MEDIA"
        return "CURTA" if extensao_km > 0 else "NAO_INFORMADA"

    def _classificar_criticidade_linha(self, tensao_kv, extensao_km):
        if tensao_kv >= 500: return "CRITICA"
        if tensao_kv >= 230 and extensao_km >= 50: return "ALTA"
        if tensao_kv >= 230: return "MEDIA_ALTA"
        if tensao_kv >= 69: return "MEDIA"
        return "BAIXA" if tensao_kv > 0 else "NAO_INFORMADA"

    def _extrair_nome_linha(self, valor):
        nome = limpar_codigo(valor)
        return " ".join(nome.split()).replace(" KV ", " KV ") if nome != "NAO INFORMADO" else nome

    def _montar_nome_linha_visual(self, row):
        nome = self._extrair_nome_linha(row.get('Name', 'NAO INFORMADO'))
        t = str(nome).strip().upper()
        is_technical = t in {"", "NAO INFORMADO"} or bool(re.fullmatch(r'[A-Z]{3,8}-?[A-Z0-9]{4,12}', t))
        
        if not is_technical: return nome
        tensao = row.get('tensao_kv', 0.0)
        oid = row.get('id_linha_transmissao', 'SEM_ID')
        if tensao and tensao > 0: return f"LINHA LT {int(tensao) if tensao.is_integer() else tensao} KV SEM_NOME OID {oid}"
        return f"LINHA TRANSMISSAO SEM_NOME OID {oid}"

    def _obter_id_linha(self, gdf):
        if "OID" in gdf.columns: return gdf["OID"].astype(str)
        if "id" in gdf.columns: return gdf["id"].astype(str)
        return pd.Series(range(1, len(gdf) + 1), index=gdf.index).astype(str)

    def transform(self, gdf):
        if 'Name' not in gdf.columns: gdf['Name'] = 'NAO INFORMADO'
        if 'PopupInfo' not in gdf.columns: gdf['PopupInfo'] = ''

        gdf['id_linha_transmissao'] = self._obter_id_linha(gdf)
        gdf['nome_linha_original'] = gdf['Name'].apply(self._extrair_nome_linha)
        gdf['tensao_kv'] = gdf.apply(self._extrair_tensao_popup_ou_nome, axis=1)
        gdf['extensao_km'] = gdf.apply(self._extrair_extensao_popup, axis=1)
        gdf['nome_linha'] = gdf.apply(self._montar_nome_linha_visual, axis=1)
        gdf['Shape_Length'] = gdf['Shape_Length'].apply(limpar_numero) if 'Shape_Length' in gdf.columns else 0.0

        gdf['estado_sigla_estimado'] = gdf['nome_linha'].apply(extrair_uf_nome_linha)
        gdf['classe_tensao'] = gdf['tensao_kv'].apply(self._classificar_tensao)
        gdf['classe_extensao'] = gdf['extensao_km'].apply(self._classificar_extensao)
        gdf['classe_criticidade_linha'] = gdf.apply(lambda r: self._classificar_criticidade_linha(r['tensao_kv'], r['extensao_km']), axis=1)

        gdf['geometry'] = gdf.geometry.apply(limpar_linestring_geometry)
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

        if gdf.empty: 
            print("⚠️ Nenhuma geometria válida após limpeza.")
            return None

        gdf['path_json'] = gdf.geometry.apply(geometry_para_path_json)
        
        gdf = adicionar_centroides(gdf)

        colunas_finais = [
            'id_linha_transmissao', 'nome_linha', 'tensao_kv',
            'classe_tensao', 'extensao_km', 'classe_extensao',
            'estado_sigla_estimado', 'classe_criticidade_linha', 'latitude', 'longitude', 'path_json'
        ]

        return pd.DataFrame(gdf[colunas_finais]).drop_duplicates(subset=['id_linha_transmissao'])

def processar_linhas_ons():
    etl = ETLDimLinhasTransmissao()
    etl.execute()


if __name__ == "__main__":
    processar_linhas_ons()
