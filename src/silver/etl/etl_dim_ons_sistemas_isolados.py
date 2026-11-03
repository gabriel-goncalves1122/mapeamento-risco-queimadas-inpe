"""
Pipeline ETL da Dimensão de Sistemas Isolados ONS (`ETLDimSistemasIsolados`).

Processa usinas e microssistemas não conectados ao SIN (concentrados na Amazônia Legal),
classifica prioridade energética e resolve o `codigo_ibge` via interseção espacial.
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.core.config.constants import ANEEL_DIR, DIMENSIONS_DIR, IBGE_DIR, NOT_INFORMED
from src.silver.utils.base import BaseETL
from src.silver.utils.df_helpers import coordenada_valida
from src.silver.utils.geo_helpers import garantir_crs_4326, geometry_para_path_json
from src.silver.utils.spatial_dimensions import carregar_municipios_geo
from src.silver.utils.string_helpers import extrair_uf_popup, limpar_codigo


class ETLDimSistemasIsolados(BaseETL):
    """ETL da dimensão energética `dim_ons_sistemas_isolados.csv`."""

    def __init__(
        self,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
        ibge_dir: str | Path | None = None,
    ) -> None:
        self.ibge_dir = str(ibge_dir or IBGE_DIR)
        super().__init__(
            input_path=input_path or os.path.join(str(ANEEL_DIR), "sistemas_isolados_ons.geojson"),
            output_path=output_path or os.path.join(str(DIMENSIONS_DIR), "dim_ons_sistemas_isolados.csv"),
        )

    @staticmethod
    def _obter_id_sistema(gdf: gpd.GeoDataFrame) -> pd.Series:
        if "OID" in gdf.columns:
            return gdf["OID"].astype(str)
        if "id" in gdf.columns:
            return gdf["id"].astype(str)
        return pd.Series(range(1, len(gdf) + 1), index=gdf.index).astype(str)

    @staticmethod
    def _extrair_nome_sistema(row: pd.Series) -> str:
        nome = limpar_codigo(row.get("Name", "NAO INFORMADO"))
        if nome != "NAO INFORMADO":
            return " ".join(nome.split())
        popup = str(row.get("PopupInfo", "")).strip()
        return limpar_codigo(popup.split("-")[0].strip()) if "-" in popup else "NAO INFORMADO"

    @staticmethod
    def _extrair_estado_sistema(row: pd.Series) -> str:
        uf = extrair_uf_popup(row.get("PopupInfo", ""))
        if uf != "NI":
            return uf
        uf = extrair_uf_popup(row.get("Name", ""))
        return uf if uf != "NI" else "NI"

    @staticmethod
    def _classificar_regiao_eletrica(estado_sigla: str) -> str:
        if estado_sigla in {"AC", "AM", "AP", "MA", "MT", "PA", "RO", "RR", "TO"}:
            return "AMAZONIA_LEGAL"
        return "NAO_INFORMADA" if estado_sigla == "NI" else "OUTRAS_REGIOES"

    @staticmethod
    def _classificar_prioridade_sistema(estado_sigla: str) -> str:
        if estado_sigla in {"AM", "PA", "AC", "AP", "RO", "RR"}:
            return "ALTA_PRIORIDADE"
        if estado_sigla in {"MT", "MA", "TO"}:
            return "MEDIA_PRIORIDADE"
        return "NAO_INFORMADA" if estado_sigla == "NI" else "BAIXA_PRIORIDADE"

    def _resolver_municipio(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Spatial Join ponto-em-polígono contra a malha municipal do IBGE."""
        municipios = carregar_municipios_geo(self.ibge_dir)
        pontos = gdf.reset_index(names="_rowid")[["_rowid", "geometry"]]
        join = gpd.sjoin(pontos, municipios, how="left", predicate="intersects")
        join = join.drop_duplicates(subset=["_rowid"]).set_index("_rowid")
        gdf["codigo_ibge"] = join["codigo_ibge"].reindex(gdf.index).fillna(NOT_INFORMED).values
        return gdf

    def transform(self, df: gpd.GeoDataFrame) -> pd.DataFrame:
        """Filtra geometrias Point válidas, classifica prioridade amazônica e gera `path_json`."""
        if df.empty:
            return df

        gdf = garantir_crs_4326(df)

        if "Name" not in gdf.columns:
            gdf["Name"] = "NAO INFORMADO"
        if "PopupInfo" not in gdf.columns:
            gdf["PopupInfo"] = ""

        gdf = gdf[gdf.geometry.notna()].copy()
        gdf = gdf[gdf.geometry.geom_type == "Point"].copy()
        if gdf.empty:
            return gdf

        gdf["longitude"] = gdf.geometry.x.round(6)
        gdf["latitude"] = gdf.geometry.y.round(6)
        gdf = gdf[gdf.apply(lambda row: coordenada_valida(row["latitude"], row["longitude"]), axis=1)].copy()

        gdf["id_sistema_isolado"] = self._obter_id_sistema(gdf)
        gdf["nome_sistema_isolado"] = gdf.apply(self._extrair_nome_sistema, axis=1)
        gdf["estado_sigla"] = gdf.apply(self._extrair_estado_sistema, axis=1)

        gdf["regiao_eletrica"] = gdf["estado_sigla"].apply(self._classificar_regiao_eletrica)
        gdf["prioridade_sistema_isolado"] = gdf["estado_sigla"].apply(self._classificar_prioridade_sistema)
        gdf["path_json"] = gdf.geometry.apply(geometry_para_path_json)

        gdf = self._resolver_municipio(gdf)

        colunas_finais = [
            "id_sistema_isolado", "nome_sistema_isolado", "estado_sigla",
            "regiao_eletrica", "prioridade_sistema_isolado", "codigo_ibge",
            "latitude", "longitude", "path_json",
        ]

        return pd.DataFrame(gdf[colunas_finais]).drop_duplicates(subset=["id_sistema_isolado"])


# Alias preservado para retrocompatibilidade
SistemasIsoladosONSETL = ETLDimSistemasIsolados


def executar() -> pd.DataFrame | None:
    """Ponto de entrada CLI e de orquestração."""
    return ETLDimSistemasIsolados().execute()


if __name__ == "__main__":
    executar()
