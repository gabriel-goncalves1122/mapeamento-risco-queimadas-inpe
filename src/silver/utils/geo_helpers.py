"""
Serviço de higienização topológica e reprojeção geoespacial (`GeometryService`).

Centraliza a manipulação vetorial Shapely/GeoPandas, reprojeções EPSG:4326/5880,
simplificação topológica de linhas ONS/DNIT e cálculo de centroides. A codificação
`path_json` foi isolada em `PathJsonCodec` (`path_json_codec.py`) e permanece
re-exportada aqui por compatibilidade.
"""
from __future__ import annotations

from typing import Any, Sequence

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from shapely.geometry.base import BaseGeometry

from src.core.config.constants import (
    BRAZIL_LAT_MAX,
    BRAZIL_LAT_MIN,
    BRAZIL_LON_MAX,
    BRAZIL_LON_MIN,
    EPSG_GPS,
    EPSG_METRICO,
)
from src.silver.utils.df_helpers import DataFrameHelper
from src.silver.utils.path_json_codec import PathJsonCodec


class GeometryService:
    """Serviço de higienização topológica, reprojeção CRS e cálculo de centroides."""

    coordenada_valida = staticmethod(DataFrameHelper.coordenada_valida)

    @staticmethod
    def garantir_crs_4326(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Garante projeção geográfica WGS84 (EPSG:4326) exigida pelo Superset."""
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=EPSG_GPS)
        return gdf.to_crs(epsg=EPSG_GPS)

    @staticmethod
    def remover_repeticoes_periodicas(coords: Sequence[Sequence[float]]) -> list[list[float]]:
        """Elimina ciclos de vértices duplicados em malhas exportadas de KML/Shapefile."""
        if not coords:
            return list(coords)

        coords_round = [tuple(PathJsonCodec.arredondar_coord(c)) for c in coords]
        n = len(coords_round)

        for tamanho in range(2, (n // 2) + 1):
            if n % tamanho != 0:
                continue
            base = coords_round[:tamanho]
            if all(coords_round[i : i + tamanho] == base for i in range(0, n, tamanho)):
                return [list(c) for c in base]

        return [list(c) for c in coords_round]

    @staticmethod
    def remover_consecutivos_duplicados(coords: list[list[float]]) -> list[list[float]]:
        """Remove vértices adjacentes idênticos que inflam o payload JSON sem alterar o traçado."""
        if not coords:
            return coords

        limpos = [coords[0]]
        for coord in coords[1:]:
            if coord != limpos[-1]:
                limpos.append(coord)
        return limpos

    @classmethod
    def limpar_linestring_geometry(cls, geom: BaseGeometry | None) -> BaseGeometry | None:
        """Enxuga LineStrings/MultiLineStrings descartando segmentos degenerados (< 2 pontos)."""
        if geom is None or geom.is_empty:
            return None

        if isinstance(geom, LineString):
            coords = cls.remover_repeticoes_periodicas(list(geom.coords))
            coords = cls.remover_consecutivos_duplicados(coords)
            return LineString(coords) if len(coords) >= 2 else None

        if isinstance(geom, MultiLineString):
            linhas = []
            for linha in geom.geoms:
                coords = cls.remover_repeticoes_periodicas(list(linha.coords))
                coords = cls.remover_consecutivos_duplicados(coords)
                if len(coords) >= 2:
                    linhas.append(LineString(coords))
            if not linhas:
                return None
            return linhas[0] if len(linhas) == 1 else MultiLineString(linhas)

        return geom

    @classmethod
    def is_coordenada_valida_brasil(cls, lat: Any, lon: Any) -> bool:
        """Valida se o ponto cai dentro do bounding box territorial brasileiro."""
        if not cls.coordenada_valida(lat, lon):
            return False
        lat_f = float(str(lat).strip().replace(",", "."))
        lon_f = float(str(lon).strip().replace(",", "."))
        return (BRAZIL_LAT_MIN <= lat_f <= BRAZIL_LAT_MAX) and (BRAZIL_LON_MIN <= lon_f <= BRAZIL_LON_MAX)

    @staticmethod
    def _coerce_float_or_none(valor: Any) -> float | None:
        if valor is None or pd.isna(valor):
            return None
        try:
            return float(str(valor).strip().replace(",", "."))
        except (ValueError, TypeError):
            return None

    @classmethod
    def normalizar_par_coordenadas(cls, lat: Any, lon: Any) -> pd.Series:
        """
        Corrige inversões de sinal (hemisfério positivo) ou troca acidental entre
        latitude e longitude frequentes em cadastros manuais do CNES.
        """
        lat_f = cls._coerce_float_or_none(lat)
        lon_f = cls._coerce_float_or_none(lon)

        candidatos = [
            (lat_f, lon_f),
            (-abs(lat_f) if lat_f is not None else lat_f, lon_f),
            (lat_f, -abs(lon_f) if lon_f is not None else lon_f),
            (-abs(lat_f) if lat_f is not None else lat_f, -abs(lon_f) if lon_f is not None else lon_f),
        ]
        if lat_f is not None and lon_f is not None:
            candidatos.extend(
                [
                    (lon_f, lat_f),
                    (-abs(lon_f), lat_f),
                    (lon_f, -abs(lat_f)),
                    (-abs(lon_f), -abs(lat_f)),
                ]
            )

        for lat_cand, lon_cand in candidatos:
            if cls.is_coordenada_valida_brasil(lat_cand, lon_cand):
                return pd.Series({"latitude": lat_cand, "longitude": lon_cand})

        return pd.Series({"latitude": None, "longitude": None})

    @staticmethod
    def corrigir_geometria_invalida(geom: BaseGeometry | None) -> BaseGeometry | None:
        """Aplica `buffer(0)` para corrigir auto-interseções em polígonos IBGE/FUNAI."""
        if geom is None or geom.is_empty:
            return None
        try:
            if not geom.is_valid:
                geom = geom.buffer(0)
            return None if geom is None or geom.is_empty else geom
        except Exception:
            return None

    @staticmethod
    def adicionar_centroides(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calcula centroides em projeção métrica (EPSG:5880) e reconverte para WGS84."""
        if gdf.empty:
            gdf["latitude"] = None
            gdf["longitude"] = None
            return gdf

        centroides = gdf.to_crs(epsg=EPSG_METRICO).geometry.centroid.to_crs(epsg=EPSG_GPS)
        gdf["latitude"] = centroides.y.round(6)
        gdf["longitude"] = centroides.x.round(6)
        return gdf


coordenada_valida = GeometryService.coordenada_valida
garantir_crs_4326 = GeometryService.garantir_crs_4326
arredondar_coord = PathJsonCodec.arredondar_coord
remover_repeticoes_periodicas = GeometryService.remover_repeticoes_periodicas
remover_consecutivos_duplicados = GeometryService.remover_consecutivos_duplicados
limpar_linestring_geometry = GeometryService.limpar_linestring_geometry
geometry_para_path_json = PathJsonCodec.geometry_para_path_json
path_json_para_geometry = PathJsonCodec.path_json_para_geometry
is_coordenada_valida_brasil = GeometryService.is_coordenada_valida_brasil
normalizar_par_coordenadas = GeometryService.normalizar_par_coordenadas
corrigir_geometria_invalida = GeometryService.corrigir_geometria_invalida
adicionar_centroides = GeometryService.adicionar_centroides
