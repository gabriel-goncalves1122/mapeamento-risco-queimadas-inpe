"""
=========================================================
MÓDULO: etl_dim_ons_subestacoes.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
import os
import pandas as pd
import geopandas as gpd

from src.etl.utils.spatial_dimensions import carregar_municipios_geo
from src.config.constants import NOT_INFORMED

from src.config.constants import DIMENSIONS_DIR, GEO_DIR
from src.etl.utils.base import BaseETL
from src.etl.utils.string_helpers import limpar_codigo, extrair_popup_valor
from src.etl.utils.df_helpers import limpar_numero, coordenada_valida
from src.etl.utils.geo_helpers import geometry_para_path_json

GEO_DIR = str(GEO_DIR)
DIMENSIONS_DIR = str(DIMENSIONS_DIR)

class ETLDimSubestacoes(BaseETL):
    def __init__(self):
        super().__init__(
            input_path=os.path.join(GEO_DIR, 'subestacoes_ons.geojson'),
            output_path=os.path.join(DIMENSIONS_DIR, 'dim_ons_subestacoes.csv'),
            expected_geom_type='Point'
        )

    def _obter_id_subestacao(self, gdf):
        if "OID" in gdf.columns: return gdf["OID"].astype(str)
        if "id" in gdf.columns: return gdf["id"].astype(str)
        return pd.Series(range(1, len(gdf) + 1), index=gdf.index).astype(str)

    def _classificar_capacidade(self, capacidade_mw):
        if capacidade_mw is None or capacidade_mw <= 0: return "NAO_INFORMADA"
        if capacidade_mw >= 2000: return "EXTREMA"
        if capacidade_mw >= 1000: return "MUITO_ALTA"
        if capacidade_mw >= 300: return "ALTA"
        return "MEDIA" if capacidade_mw >= 100 else "BAIXA"

    def _classificar_criticidade(self, capacidade_mw):
        if capacidade_mw is None or capacidade_mw <= 0: return "NAO_INFORMADA"
        if capacidade_mw >= 1000: return "CRITICA"
        if capacidade_mw >= 300: return "ALTA"
        return "MEDIA" if capacidade_mw >= 100 else "BAIXA"

    def _normalizar_nome(self, row):
        nome_popup = limpar_codigo(extrair_popup_valor(row.get("PopupInfo", ""), "Nome"))
        if nome_popup != "NAO INFORMADO": return "SUBESTACAO " + " ".join(nome_popup.split())
        nome = limpar_codigo(row.get("Name", "NAO INFORMADO"))
        return " ".join(nome.split()) if nome != "NAO INFORMADO" else "NAO INFORMADO"

    def _normalizar_agente(self, row):
        agente = limpar_codigo(extrair_popup_valor(row.get("PopupInfo", ""), "Agente"))
        return " ".join(agente.split()) if agente != "NAO INFORMADO" else "NAO INFORMADO"

    def _resolver_municipio(self, gdf):
        """Spatial Join ponto-em-polígono para descobrir o codigo_ibge do município."""
        municipios = carregar_municipios_geo(GEO_DIR)
        pontos = gdf.reset_index(names='_rowid')[['_rowid', 'geometry']]
        join = gpd.sjoin(pontos, municipios, how='left', predicate='intersects')
        join = join.drop_duplicates(subset=['_rowid']).set_index('_rowid')
        gdf['codigo_ibge'] = join['codigo_ibge'].reindex(gdf.index).fillna(NOT_INFORMED).values
        return gdf

    def transform(self, gdf):
        if 'Name' not in gdf.columns: gdf['Name'] = 'NAO INFORMADO'
        if 'PopupInfo' not in gdf.columns: gdf['PopupInfo'] = ''

        gdf['longitude'] = gdf.geometry.x.round(6)
        gdf['latitude'] = gdf.geometry.y.round(6)
        
        # Filtro de coordenadas validas
        mask = gdf.apply(lambda row: coordenada_valida(row['latitude'], row['longitude']), axis=1)
        gdf = gdf[mask].copy()

        gdf['id_subestacao'] = self._obter_id_subestacao(gdf)
        gdf['nome_subestacao'] = gdf.apply(self._normalizar_nome, axis=1)
        gdf['agente_responsavel'] = gdf.apply(self._normalizar_agente, axis=1)
        gdf['capacidade_mw'] = gdf['PopupInfo'].apply(lambda html: limpar_numero(extrair_popup_valor(html, 'Capacidade'), default=0.0))

        gdf['classe_capacidade'] = gdf['capacidade_mw'].apply(self._classificar_capacidade)
        gdf['criticidade_subestacao'] = gdf['capacidade_mw'].apply(self._classificar_criticidade)

        gdf['path_json'] = gdf.geometry.apply(geometry_para_path_json)

        gdf = self._resolver_municipio(gdf)

        colunas_finais = [
            'id_subestacao', 'nome_subestacao', 'capacidade_mw', 'classe_capacidade',
            'criticidade_subestacao', 'agente_responsavel', 'codigo_ibge',
            'latitude', 'longitude', 'path_json'
        ]

        df_final = pd.DataFrame(gdf[colunas_finais]).drop_duplicates(subset=['id_subestacao'])
        return df_final

def processar_subestacoes_ons():
    etl = ETLDimSubestacoes()
    etl.execute()


if __name__ == "__main__":
    processar_subestacoes_ons()
