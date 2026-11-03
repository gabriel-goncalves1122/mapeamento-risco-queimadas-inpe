"""
Repositório de geometrias dimensionais base (`SpatialDimensionRepository`).

Centraliza o carregamento de malhas oficiais do IBGE e FUNAI e o enriquecimento
espacial ponto-em-polígono (`sjoin`), evitando duplicação de lógica geográfica
entre os ETLs de Hospitais, Subestações e Sistemas Isolados (SRP / DIP).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union

from src.core.config.constants import FUNAI_DIR, IBGE_DIR, NOT_INFORMED
from src.silver.utils.geo_helpers import GeometryService
from src.silver.utils.keys import DimensionalKeyNormalizer


class SpatialDimensionRepository:
    """
    Repositório para leitura e cruzamento espacial com malhas de referência (IBGE/FUNAI).

    Permite injeção dos diretórios `ibge_dir` e `funai_dir` para testes isolados.
    """

    def __init__(
        self,
        ibge_dir: str | Path = IBGE_DIR,
        funai_dir: str | Path = FUNAI_DIR,
    ) -> None:
        self.ibge_dir = str(ibge_dir)
        self.funai_dir = str(funai_dir)

    @staticmethod
    def limpar_geometria(geom: Any) -> Any:
        """Corrige polígonos auto-intersectantes via `buffer(0)` e descarta geometrias vazias."""
        return GeometryService.corrigir_geometria_invalida(geom)

    def carregar_municipios_geo(self, geo_dir: str | Path | None = None) -> gpd.GeoDataFrame:
        """Carrega malha municipal do IBGE projetada em EPSG:4326 com `codigo_ibge` de 6 dígitos."""
        diretorio = str(geo_dir or self.ibge_dir)
        gdf = gpd.read_file(os.path.join(diretorio, "municipios_br.geojson"))
        gdf = GeometryService.garantir_crs_4326(gdf)
        gdf["codigo_ibge"] = gdf["id"].apply(DimensionalKeyNormalizer.normalizar_codigo_ibge)
        gdf = gdf[gdf["codigo_ibge"] != NOT_INFORMED].copy()
        gdf["geometry"] = gdf.geometry.apply(self.limpar_geometria)
        gdf = gdf[gdf.geometry.notna()].copy()
        return gdf[["codigo_ibge", "geometry"]].drop_duplicates(subset=["codigo_ibge"])

    def carregar_terras_indigenas_geo(self, geo_dir: str | Path | None = None) -> gpd.GeoDataFrame:
        """Carrega e unifica (`unary_union`) polígonos de Terras Indígenas por `codigo_ti`."""
        diretorio = str(geo_dir or self.funai_dir)
        file_geojson = os.path.join(diretorio, "mapa_terras_indigenas.geojson")
        with open(file_geojson, "r", encoding="utf-8") as fp:
            geojson_data = json.load(fp)

        geoms_por_ti: dict[str, list[Any]] = {}
        for feature in geojson_data.get("features", []):
            codigo_ti = DimensionalKeyNormalizer.normalizar_codigo_ti(
                feature.get("properties", {}).get("codigo_ti")
            )
            if codigo_ti == NOT_INFORMED:
                continue
            try:
                geom = self.limpar_geometria(shape(feature.get("geometry")))
            except Exception:
                geom = None
            if geom is not None:
                geoms_por_ti.setdefault(codigo_ti, []).append(geom)

        registros = []
        for codigo_ti, geoms in geoms_por_ti.items():
            geom = self.limpar_geometria(unary_union(geoms))
            if geom is not None:
                registros.append({"codigo_ti": codigo_ti, "geometry": geom})

        return gpd.GeoDataFrame(registros, geometry="geometry", crs="EPSG:4326")

    def associar_municipio_por_intersecao(
        self,
        gdf: gpd.GeoDataFrame,
        municipios_gdf: gpd.GeoDataFrame | None = None,
    ) -> gpd.GeoDataFrame:
        """
        Realiza Spatial Join ponto-em-polígono para atribuir `codigo_ibge`
        a ativos pontuais (Subestações e Sistemas Isolados do ONS).
        """
        municipios = municipios_gdf if municipios_gdf is not None else self.carregar_municipios_geo()
        pontos = gdf.reset_index(names="_rowid")[["_rowid", "geometry"]]
        join = gpd.sjoin(pontos, municipios, how="left", predicate="intersects")
        join = join.drop_duplicates(subset=["_rowid"]).set_index("_rowid")
        gdf["codigo_ibge"] = join["codigo_ibge"].reindex(gdf.index).fillna(NOT_INFORMED).values
        return gdf


_DEFAULT_REPO = SpatialDimensionRepository()

limpar_geometria = SpatialDimensionRepository.limpar_geometria


def carregar_municipios_geo(geo_dir: str | Path | None = None) -> gpd.GeoDataFrame:
    """Função fachada para leitura da malha municipal do IBGE."""
    return _DEFAULT_REPO.carregar_municipios_geo(geo_dir=geo_dir)


def carregar_terras_indigenas_geo(geo_dir: str | Path | None = None) -> gpd.GeoDataFrame:
    """Função fachada para leitura da malha de Terras Indígenas da FUNAI."""
    return _DEFAULT_REPO.carregar_terras_indigenas_geo(geo_dir=geo_dir)
