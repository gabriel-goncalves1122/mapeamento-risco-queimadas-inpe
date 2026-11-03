"""
Pipeline ETL da Dimensão de Subestações ONS (`ETLDimSubestacoes`).

Extrai potência instalada (MW) e concessionária a partir do `PopupInfo` da ANEEL,
classifica criticidade energética e resolve o `codigo_ibge` municipal via interseção espacial.
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.core.config.constants import ANEEL_DIR, DIMENSIONS_DIR, IBGE_DIR, NOT_INFORMED
from src.silver.utils.base import BaseETL
from src.silver.utils.df_helpers import coordenada_valida, limpar_numero
from src.silver.utils.geo_helpers import geometry_para_path_json
from src.silver.utils.spatial_dimensions import carregar_municipios_geo
from src.silver.utils.string_helpers import extrair_popup_valor, limpar_codigo


class ETLDimSubestacoes(BaseETL):
    """ETL da dimensão pontual `dim_ons_subestacoes.csv`."""

    def __init__(
        self,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
        ibge_dir: str | Path | None = None,
    ) -> None:
        self.ibge_dir = str(ibge_dir or IBGE_DIR)
        super().__init__(
            input_path=input_path or os.path.join(str(ANEEL_DIR), "subestacoes_ons.geojson"),
            output_path=output_path or os.path.join(str(DIMENSIONS_DIR), "dim_ons_subestacoes.csv"),
            expected_geom_type="Point",
        )

    @staticmethod
    def _obter_id_subestacao(gdf: gpd.GeoDataFrame) -> pd.Series:
        if "OID" in gdf.columns:
            return gdf["OID"].astype(str)
        if "id" in gdf.columns:
            return gdf["id"].astype(str)
        return pd.Series(range(1, len(gdf) + 1), index=gdf.index).astype(str)

    @staticmethod
    def _classificar_capacidade(capacidade_mw: float | None) -> str:
        if capacidade_mw is None or capacidade_mw <= 0:
            return "NAO_INFORMADA"
        if capacidade_mw >= 2000:
            return "EXTREMA"
        if capacidade_mw >= 1000:
            return "MUITO_ALTA"
        if capacidade_mw >= 300:
            return "ALTA"
        return "MEDIA" if capacidade_mw >= 100 else "BAIXA"

    @staticmethod
    def _classificar_criticidade(capacidade_mw: float | None) -> str:
        if capacidade_mw is None or capacidade_mw <= 0:
            return "NAO_INFORMADA"
        if capacidade_mw >= 1000:
            return "CRITICA"
        if capacidade_mw >= 300:
            return "ALTA"
        return "MEDIA" if capacidade_mw >= 100 else "BAIXA"

    @staticmethod
    def _normalizar_nome(row: pd.Series) -> str:
        nome_popup = limpar_codigo(extrair_popup_valor(row.get("PopupInfo", ""), "Nome"))
        if nome_popup != "NAO INFORMADO":
            return "SUBESTACAO " + " ".join(nome_popup.split())
        nome = limpar_codigo(row.get("Name", "NAO INFORMADO"))
        return " ".join(nome.split()) if nome != "NAO INFORMADO" else "NAO INFORMADO"

    @staticmethod
    def _normalizar_agente(row: pd.Series) -> str:
        agente = limpar_codigo(extrair_popup_valor(row.get("PopupInfo", ""), "Agente"))
        return " ".join(agente.split()) if agente != "NAO INFORMADO" else "NAO INFORMADO"

    def _resolver_municipio(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Spatial Join ponto-em-polígono contra a malha municipal do IBGE."""
        municipios = carregar_municipios_geo(self.ibge_dir)
        pontos = gdf.reset_index(names="_rowid")[["_rowid", "geometry"]]
        join = gpd.sjoin(pontos, municipios, how="left", predicate="intersects")
        join = join.drop_duplicates(subset=["_rowid"]).set_index("_rowid")
        gdf["codigo_ibge"] = join["codigo_ibge"].reindex(gdf.index).fillna(NOT_INFORMED).values
        return gdf

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Padroniza atributos elétricos e associa cada subestação ao seu município IBGE."""
        if "Name" not in gdf.columns:
            gdf["Name"] = "NAO INFORMADO"
        if "PopupInfo" not in gdf.columns:
            gdf["PopupInfo"] = ""

        gdf["longitude"] = gdf.geometry.x.round(6)
        gdf["latitude"] = gdf.geometry.y.round(6)

        mask = gdf.apply(lambda row: coordenada_valida(row["latitude"], row["longitude"]), axis=1)
        gdf = gdf[mask].copy()

        gdf["id_subestacao"] = self._obter_id_subestacao(gdf)
        gdf["nome_subestacao"] = gdf.apply(self._normalizar_nome, axis=1)
        gdf["agente_responsavel"] = gdf.apply(self._normalizar_agente, axis=1)
        gdf["capacidade_mw"] = gdf["PopupInfo"].apply(
            lambda html: limpar_numero(extrair_popup_valor(html, "Capacidade"), default=0.0)
        )

        gdf["classe_capacidade"] = gdf["capacidade_mw"].apply(self._classificar_capacidade)
        gdf["criticidade_subestacao"] = gdf["capacidade_mw"].apply(self._classificar_criticidade)
        gdf["path_json"] = gdf.geometry.apply(geometry_para_path_json)

        gdf = self._resolver_municipio(gdf)

        colunas_finais = [
            "id_subestacao", "nome_subestacao", "capacidade_mw", "classe_capacidade",
            "criticidade_subestacao", "agente_responsavel", "codigo_ibge",
            "latitude", "longitude", "path_json",
        ]

        return pd.DataFrame(gdf[colunas_finais]).drop_duplicates(subset=["id_subestacao"])


def executar() -> pd.DataFrame | None:
    """Ponto de entrada CLI e de orquestração."""
    return ETLDimSubestacoes().execute()


processar_subestacoes_ons = executar


if __name__ == "__main__":
    executar()
