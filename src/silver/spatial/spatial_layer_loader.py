"""
Carregador e indexador de dimensões espaciais (`SpatialLayerLoader`).

Isola a leitura de CSVs Silver, a reconstrução de geometrias (`path_json`, WKT ou
par `latitude`/`longitude`), a reprojeção CRS (EPSG:4326 e EPSG:5880) e o
pré-aquecimento do índice espacial R-Tree (`sindex`) (SRP).
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely import wkt

from src.core.config.constants import (
    EPSG_GPS,
    EPSG_METRICO,
    GEOMETRY_WKT_COLUMN,
    NOT_INFORMED,
    PATH_JSON_COLUMN,
)
from src.silver.utils.cleaners import limpar_wkt
from src.silver.utils.path_json_codec import PathJsonCodec

logger = logging.getLogger(__name__)


class SpatialLayerLoader:
    """
    Carrega um CSV dimensional Silver e constrói os `GeoDataFrame`s indexados via R-Tree.

    Suporta três contratos de persistência geométrica em ordem de prioridade:
    1. `path_json` (padrão oficial das dimensões Silver para Superset/Deck.gl)
    2. `geometria_wkt` (fallback legado)
    3. Colunas escalares `latitude` e `longitude` (pontos puros)
    """

    def carregar(
        self,
        path: str | Path,
        nome: str,
        tipo_geometria: str = "point",
        projetar_metrico: bool = False,
    ) -> tuple[gpd.GeoDataFrame | None, gpd.GeoDataFrame | None]:
        """Retorna `(gdf_gps, gdf_metrico)` com seus respectivos `sindex` inicializados."""
        try:
            df = pd.read_csv(path, dtype=str)
            if df.empty:
                logger.warning("Dimensão '%s' vazia.", nome)
                return None, None

            df.columns = [str(col).strip() for col in df.columns]

            if PATH_JSON_COLUMN in df.columns:
                df["geometry"] = df[PATH_JSON_COLUMN].apply(
                    lambda valor: self.path_json_para_geom(valor, tipo_geometria=tipo_geometria, nome=nome)
                )
            elif GEOMETRY_WKT_COLUMN in df.columns:
                # Compatibilidade com CSVs legados que armazenavam WKT bruto
                df[GEOMETRY_WKT_COLUMN] = df[GEOMETRY_WKT_COLUMN].apply(limpar_wkt)
                df["geometry"] = df[GEOMETRY_WKT_COLUMN].apply(self.wkt_para_geom)
            elif {"latitude", "longitude"}.issubset(df.columns):
                df["latitude"] = df["latitude"].apply(self.normalizar_coord)
                df["longitude"] = df["longitude"].apply(self.normalizar_coord)
                df = df.dropna(subset=["latitude", "longitude"])
                # Descarta coordenadas fora do globo ou no ponto nulo (0, 0) no Golfo da Guiné
                df = df[
                    (df["latitude"].between(-90, 90))
                    & (df["longitude"].between(-180, 180))
                    & ~((df["latitude"] == 0.0) & (df["longitude"] == 0.0))
                ].copy()
                df["geometry"] = gpd.points_from_xy(df["longitude"], df["latitude"])
            else:
                logger.warning(
                    "Dimensão '%s' sem %s ou latitude/longitude.",
                    nome,
                    GEOMETRY_WKT_COLUMN,
                )
                return None, None

            df = df.dropna(subset=["geometry"]).copy()
            if df.empty:
                logger.warning("Dimensão '%s' ficou vazia após limpeza geométrica.", nome)
                return None, None

            gdf_gps = gpd.GeoDataFrame(df, geometry="geometry", crs=f"EPSG:{EPSG_GPS}")
            # Força a construção antecipada da R-Tree em WGS84 antes do loop de streaming
            _ = gdf_gps.sindex

            gdf_metrico: gpd.GeoDataFrame | None = None
            if projetar_metrico:
                # EPSG:5880 (SIRGAS 2000 / Brazil Polyconic) permite medir distâncias em metros
                gdf_metrico = gdf_gps.to_crs(epsg=EPSG_METRICO)
                _ = gdf_metrico.sindex

            logger.info("Dimensão '%s' indexada. Total: %s registros.", nome, len(gdf_gps))
            return gdf_gps, gdf_metrico
        except Exception as exc:
            logger.warning("Erro ao carregar '%s': %s", nome, exc)
            return None, None

    @staticmethod
    def path_json_para_geom(valor: Any, tipo_geometria: str = "point", nome: str = "") -> Any:
        """Reconstrói geometria Shapely a partir de `path_json` via `PathJsonCodec`."""
        geom = PathJsonCodec.path_json_para_geometry(valor, tipo_geometria=tipo_geometria)
        if geom is None and str(tipo_geometria).lower() not in {"point", "line", "polygon"}:
            logger.warning("Tipo geométrico '%s' não reconhecido para '%s'.", tipo_geometria, nome)
        return geom

    @staticmethod
    def wkt_para_geom(valor: Any) -> Any:
        """Converte string WKT em geometria Shapely válida aplicando `buffer(0)` se necessário."""
        try:
            if pd.isna(valor):
                return None
            texto = str(valor).strip()
            if not texto or texto == NOT_INFORMED:
                return None
            geom = wkt.loads(texto)
            if geom is None or geom.is_empty:
                return None
            if not geom.is_valid:
                geom = geom.buffer(0)
            return None if geom is None or geom.is_empty else geom
        except Exception:
            return None

    @staticmethod
    def normalizar_coord(valor: Any) -> float | None:
        """Converte coordenada textual (com ponto ou vírgula) em float finito."""
        try:
            if pd.isna(valor):
                return None
            texto = str(valor).replace(",", ".").strip()
            if not texto:
                return None
            numero = float(texto)
            return None if math.isnan(numero) or math.isinf(numero) else numero
        except Exception:
            return None
