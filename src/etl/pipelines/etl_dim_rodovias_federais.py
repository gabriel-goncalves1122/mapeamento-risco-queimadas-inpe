"""
=========================================================
MÓDULO: etl_dim_rodovias_federais.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
import os
import hashlib
import pandas as pd
import geopandas as gpd

from src.config.constants import DIMENSIONS_DIR, GEO_DIR
from src.etl.utils.base import BaseETL
from src.etl.utils.string_helpers import limpar_codigo
from src.etl.utils.geo_helpers import garantir_crs_4326, limpar_linestring_geometry, geometry_para_path_json

GEO_DIR = str(GEO_DIR)
DIMENSIONS_DIR = str(DIMENSIONS_DIR)

class RodoviasFederaisETL(BaseETL):
    def __init__(self):
        super().__init__(
            input_path=os.path.join(GEO_DIR, "mapa_rodovias_federais.geojson"),
            output_path=os.path.join(DIMENSIONS_DIR, "dim_rodovias_federais.csv")
        )

    def _classificar_revestimento(self, revestimento):
        rev = limpar_codigo(revestimento)
        if "NAO PAVIMENTADO" in rev: return "NAO_PAVIMENTADO"
        if "PAVIMENTADO" in rev: return "PAVIMENTADO"
        if "IMPLANTADO" in rev: return "IMPLANTADO"
        return "NAO_INFORMADO" if rev == "NAO INFORMADO" else "OUTROS"

    def _classificar_operacao(self, status_operacional):
        status = limpar_codigo(status_operacional)
        if status in {"SIM", "S", "OPERACIONAL", "EM OPERACAO", "EM OPERAÇÃO"}: return "OPERACIONAL"
        if status in {"NAO", "N", "NÃO", "NAO OPERACIONAL", "NÃO OPERACIONAL"}: return "NAO_OPERACIONAL"
        return status if status != "NAO INFORMADO" else "NAO_INFORMADO"

    def _classificar_situacao(self, situacao_fisica):
        sit = limpar_codigo(situacao_fisica)
        if "CONSTRUIDA" in sit: return "CONSTRUIDA"
        if "PLANEJADA" in sit: return "PLANEJADA"
        if "EM OBRAS" in sit: return "EM_OBRAS"
        if "LEITO NATURAL" in sit: return "LEITO_NATURAL"
        return sit if sit != "NAO INFORMADO" else "NAO_INFORMADO"

    def _classificar_criticidade_rodovia(self, revestimento_classe, situacao_classe, operacao_classe):
        if operacao_classe == "OPERACIONAL" and revestimento_classe == "PAVIMENTADO": return "ALTA_RELEVANCIA"
        if operacao_classe == "OPERACIONAL": return "MEDIA_RELEVANCIA"
        if situacao_classe in {"EM_OBRAS", "PLANEJADA"}: return "BAIXA_RELEVANCIA"
        return "BAIXA_RELEVANCIA" if operacao_classe != "NAO_INFORMADO" else "NAO_INFORMADA"

    def _normalizar_codigo_rodovia(self, valor):
        codigo = limpar_codigo(valor).replace(" ", "")
        if codigo.startswith("BR") and not codigo.startswith("BR-"): return codigo.replace("BR", "BR-", 1)
        return codigo

    def _gerar_id_trecho_unico(self, row, indice):
        base = f"{row.get('id_trecho_rodoviario_origem', 'NA')}_{row.get('codigo_rodovia', 'NA')}_{row.get('jurisdicao', 'NA')}_{row.get('path_json', 'NA')}_{indice}"
        return f"ROD_{hashlib.md5(base.encode('utf-8')).hexdigest()[:10]}"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            print("⚠️ GeoJSON vazio.")
            return df
            
        gdf = garantir_crs_4326(df)

        cols_rename = {
            'vl_br': 'codigo_rodovia', 'ds_jurisdi': 'jurisdicao', 'ds_revesti': 'revestimento',
            'ds_tipo_pa': 'tipo_pavimento', 'ds_situaca': 'situacao_fisica', 'ds_operaci': 'status_operacional'
        }
        gdf = gdf.rename(columns={k: v for k, v in cols_rename.items() if k in gdf.columns})
        for col in cols_rename.values():
            if col not in gdf.columns: gdf[col] = "NAO INFORMADO"

        gdf['id_trecho_rodoviario_origem'] = gdf.get('id_trecho_rodoviario', pd.Series([""]*len(gdf))).astype(str)
        gdf['codigo_rodovia'] = gdf['codigo_rodovia'].apply(self._normalizar_codigo_rodovia)
        gdf['jurisdicao'] = gdf['jurisdicao'].apply(limpar_codigo)
        gdf['revestimento'] = gdf['revestimento'].apply(limpar_codigo)
        gdf['tipo_pavimento'] = gdf['tipo_pavimento'].apply(limpar_codigo)
        gdf['situacao_fisica'] = gdf['situacao_fisica'].apply(limpar_codigo)
        gdf['status_operacional'] = gdf['status_operacional'].apply(limpar_codigo)

        gdf = gdf[gdf.geometry.notna()].copy()
        gdf['geometry'] = gdf.geometry.apply(limpar_linestring_geometry)
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
        
        if gdf.empty: 
            print("⚠️ Geometrias inválidas após limpeza.")
            return gdf

        gdf['path_json'] = gdf.geometry.apply(geometry_para_path_json)
        
        centroides = gdf.geometry.centroid
        gdf['latitude'] = centroides.y.round(6)
        gdf['longitude'] = centroides.x.round(6)

        gdf = gdf.reset_index(drop=True)
        gdf['id_trecho_rodoviario'] = gdf.apply(lambda r: self._gerar_id_trecho_unico(r, r.name), axis=1)

        gdf['classe_revestimento'] = gdf['revestimento'].apply(self._classificar_revestimento)
        gdf['classe_situacao_fisica'] = gdf['situacao_fisica'].apply(self._classificar_situacao)
        gdf['classe_status_operacional'] = gdf['status_operacional'].apply(self._classificar_operacao)
        gdf['criticidade_rodovia'] = gdf.apply(lambda r: self._classificar_criticidade_rodovia(r['classe_revestimento'], r['classe_situacao_fisica'], r['classe_status_operacional']), axis=1)

        colunas_finais = [
            'id_trecho_rodoviario', 'codigo_rodovia', 'jurisdicao',
            'classe_revestimento', 'tipo_pavimento', 'classe_situacao_fisica',
            'classe_status_operacional', 'criticidade_rodovia',
            'latitude', 'longitude', 'path_json'
        ]
        
        # Limpeza final de duplicatas mantendo a unicidade da rodovia
        df_final = pd.DataFrame(gdf[colunas_finais]).drop_duplicates(
            subset=['codigo_rodovia', 'jurisdicao', 'classe_revestimento', 'tipo_pavimento', 'classe_situacao_fisica', 'classe_status_operacional', 'path_json']
        )
        return df_final

def executar():
    etl = RodoviasFederaisETL()
    etl.execute()


if __name__ == "__main__":
    executar()
