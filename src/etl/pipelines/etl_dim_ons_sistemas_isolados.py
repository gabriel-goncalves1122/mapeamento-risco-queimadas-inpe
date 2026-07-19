"""
=========================================================
MÓDULO: etl_dim_ons_sistemas_isolados.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
import os
import pandas as pd
import geopandas as gpd

from src.config.constants import DIMENSIONS_DIR, GEO_DIR
from src.etl.utils.spatial_dimensions import carregar_municipios_geo
from src.config.constants import NOT_INFORMED
from src.etl.utils.base import BaseETL
from src.etl.utils.string_helpers import limpar_codigo, extrair_uf_popup
from src.etl.utils.df_helpers import coordenada_valida
from src.etl.utils.geo_helpers import garantir_crs_4326, geometry_para_path_json

GEO_DIR = str(GEO_DIR)
DIMENSIONS_DIR = str(DIMENSIONS_DIR)

class SistemasIsoladosONSETL(BaseETL):
    def __init__(self):
        super().__init__(
            input_path=os.path.join(GEO_DIR, "sistemas_isolados_ons.geojson"),
            output_path=os.path.join(DIMENSIONS_DIR, "dim_ons_sistemas_isolados.csv")
        )

    def _obter_id_sistema(self, gdf):
        if "OID" in gdf.columns: return gdf["OID"].astype(str)
        if "id" in gdf.columns: return gdf["id"].astype(str)
        return pd.Series(range(1, len(gdf) + 1), index=gdf.index).astype(str)

    def _extrair_nome_sistema(self, row):
        nome = limpar_codigo(row.get("Name", "NAO INFORMADO"))
        if nome != "NAO INFORMADO": return " ".join(nome.split())
        popup = str(row.get("PopupInfo", "")).strip()
        return limpar_codigo(popup.split("-")[0].strip()) if "-" in popup else "NAO INFORMADO"

    def _extrair_estado_sistema(self, row):
        uf = extrair_uf_popup(row.get("PopupInfo", ""))
        if uf != "NI": return uf
        uf = extrair_uf_popup(row.get("Name", ""))
        return uf if uf != "NI" else "NI"

    def _classificar_regiao_eletrica(self, estado_sigla):
        if estado_sigla in {"AC", "AM", "AP", "MA", "MT", "PA", "RO", "RR", "TO"}: 
            return "AMAZONIA_LEGAL"
        return "NAO_INFORMADA" if estado_sigla == "NI" else "OUTRAS_REGIOES"

    def _classificar_prioridade_sistema(self, estado_sigla):
        if estado_sigla in {"AM", "PA", "AC", "AP", "RO", "RR"}: return "ALTA_PRIORIDADE"
        if estado_sigla in {"MT", "MA", "TO"}: return "MEDIA_PRIORIDADE"
        return "NAO_INFORMADA" if estado_sigla == "NI" else "BAIXA_PRIORIDADE"

    def _resolver_municipio(self, gdf):
        """Spatial Join ponto-em-polígono para descobrir o codigo_ibge do município."""
        municipios = carregar_municipios_geo(GEO_DIR)
        pontos = gdf.reset_index(names='_rowid')[['_rowid', 'geometry']]
        join = gpd.sjoin(pontos, municipios, how='left', predicate='intersects')
        join = join.drop_duplicates(subset=['_rowid']).set_index('_rowid')
        gdf['codigo_ibge'] = join['codigo_ibge'].reindex(gdf.index).fillna(NOT_INFORMED).values
        return gdf

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            print("⚠️ GeoJSON vazio.")
            return df
            
        gdf = garantir_crs_4326(df)

        if 'Name' not in gdf.columns: gdf['Name'] = 'NAO INFORMADO'
        if 'PopupInfo' not in gdf.columns: gdf['PopupInfo'] = ''

        gdf = gdf[gdf.geometry.notna()].copy()
        gdf = gdf[gdf.geometry.geom_type == 'Point'].copy()
        if gdf.empty: 
            print("⚠️ Nenhuma geometria Point válida.")
            return gdf

        gdf['longitude'] = gdf.geometry.x.round(6)
        gdf['latitude'] = gdf.geometry.y.round(6)
        gdf = gdf[gdf.apply(lambda row: coordenada_valida(row['latitude'], row['longitude']), axis=1)].copy()

        gdf['id_sistema_isolado'] = self._obter_id_sistema(gdf)
        gdf['nome_sistema_isolado'] = gdf.apply(self._extrair_nome_sistema, axis=1)
        gdf['estado_sigla'] = gdf.apply(self._extrair_estado_sistema, axis=1)

        gdf['regiao_eletrica'] = gdf['estado_sigla'].apply(self._classificar_regiao_eletrica)
        gdf['prioridade_sistema_isolado'] = gdf['estado_sigla'].apply(self._classificar_prioridade_sistema)

        # path_json é o contrato único para Druid/Superset e para reconstrução espacial interna.
        gdf['path_json'] = gdf.geometry.apply(geometry_para_path_json)

        gdf = self._resolver_municipio(gdf)

        colunas_finais = [
            'id_sistema_isolado', 'nome_sistema_isolado', 'estado_sigla',
            'regiao_eletrica', 'prioridade_sistema_isolado', 'codigo_ibge',
            'latitude', 'longitude', 'path_json'
        ]

        df_final = pd.DataFrame(gdf[colunas_finais]).drop_duplicates(subset=['id_sistema_isolado'])
        return df_final

def executar():
    etl = SistemasIsoladosONSETL()
    etl.execute()


if __name__ == "__main__":
    executar()
