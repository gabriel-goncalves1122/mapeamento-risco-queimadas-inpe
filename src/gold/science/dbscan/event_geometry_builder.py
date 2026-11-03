"""
Construtor geométrico de manchas de eventos de incêndio (`EventGeometryBuilder`).

Isola a reprojeção de pontos do cluster para EPSG:5880, o cálculo do envoltório
convexo (`convex_hull`), a aplicação de buffer métrico para focos colineares e a
serialização `path_json` para o Deck.gl no Apache Superset (SRP).
"""
from __future__ import annotations

from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPoint

from src.core.config.constants import EPSG_GPS, EPSG_METRICO
from src.silver.utils.path_json_codec import PathJsonCodec


class EventGeometryBuilder:
    """
    Constrói o polígono, centroide e área (km²) de um cluster de focos de incêndio.

    Opera em projeção policônica métrica (EPSG:5880) para calcular áreas e buffers
    reais em metros e reconverte o resultado para WGS84 (EPSG:4326) exigido pelo Superset.
    """

    def __init__(self, area_buffer_km: float = 0.5) -> None:
        self.area_buffer_km = area_buffer_km

    @staticmethod
    def pontos_metricos(df: pd.DataFrame) -> gpd.GeoSeries:
        """Projeta as colunas `longitude` e `latitude` de WGS84 para EPSG:5880 (metros)."""
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
            crs=f"EPSG:{EPSG_GPS}",
        )
        return gdf.to_crs(epsg=EPSG_METRICO).geometry

    def construir_geometria(self, grupo: pd.DataFrame) -> tuple[Any, float, float, float]:
        """
        Retorna `(geom_gps, centroide_lat, centroide_lon, area_km2)` para um cluster de focos.
        """
        pontos_metricos = self.pontos_metricos(grupo)
        multiponto = MultiPoint(list(pontos_metricos))
        geom_metric = multiponto.convex_hull

        # Focos colineares em WGS84 geram Point/LineString ou sliver < 1 m² após projeção policônica;
        # aplicamos o buffer métrico para produzir polígono visível no Deck.gl
        if geom_metric.geom_type in {"Point", "LineString"} or geom_metric.area < 1.0:
            geom_metric = multiponto.buffer(self.area_buffer_km * 1000.0)

        centroide_metric = geom_metric.centroid
        geom_gps = (
            gpd.GeoSeries([geom_metric], crs=f"EPSG:{EPSG_METRICO}")
            .to_crs(epsg=EPSG_GPS)
            .iloc[0]
        )
        centroide_gps = (
            gpd.GeoSeries([centroide_metric], crs=f"EPSG:{EPSG_METRICO}")
            .to_crs(epsg=EPSG_GPS)
            .iloc[0]
        )
        area_km2 = round(float(geom_metric.area) / 1_000_000.0, 6)
        return geom_gps, float(centroide_gps.y), float(centroide_gps.x), area_km2

    @staticmethod
    def serializar_path_json(geom_gps: Any) -> str:
        """Serializa o polígono WGS84 do evento no formato `path_json` do Deck.gl."""
        return PathJsonCodec.geometry_para_path_json(geom_gps)
