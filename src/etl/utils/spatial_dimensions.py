"""
Leitura padronizada das geometrias dimensionais base.

Esses helpers alimentam ETLs que precisam resolver relacoes espaciais durante
o batch, antes dos dados chegarem ao Druid/Superset.
"""
import json
import os

import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union

from src.config.constants import GEO_DIR, NOT_INFORMED
from src.etl.utils.geo_helpers import garantir_crs_4326
from src.etl.utils.keys import normalizar_codigo_ibge, normalizar_codigo_ti


def limpar_geometria(geom):
    if geom is None or geom.is_empty:
        return None
    if not geom.is_valid:
        geom = geom.buffer(0)
    if geom is None or geom.is_empty:
        return None
    return geom


def carregar_municipios_geo(geo_dir=None):
    geo_dir = str(geo_dir or GEO_DIR)
    gdf = gpd.read_file(os.path.join(geo_dir, "municipios_br.geojson"))
    gdf = garantir_crs_4326(gdf)
    gdf["codigo_ibge"] = gdf["id"].apply(normalizar_codigo_ibge)
    gdf = gdf[gdf["codigo_ibge"] != NOT_INFORMED].copy()
    gdf["geometry"] = gdf.geometry.apply(limpar_geometria)
    gdf = gdf[gdf.geometry.notna()].copy()
    return gdf[["codigo_ibge", "geometry"]].drop_duplicates(subset=["codigo_ibge"])


def carregar_terras_indigenas_geo(geo_dir=None):
    geo_dir = str(geo_dir or GEO_DIR)
    file_geojson = os.path.join(geo_dir, "mapa_terras_indigenas.geojson")
    with open(file_geojson, "r", encoding="utf-8") as fp:
        geojson_data = json.load(fp)

    geoms_por_ti = {}
    for feature in geojson_data.get("features", []):
        codigo_ti = normalizar_codigo_ti(feature.get("properties", {}).get("codigo_ti"))
        if codigo_ti == NOT_INFORMED:
            continue
        try:
            geom = limpar_geometria(shape(feature.get("geometry")))
        except Exception:
            geom = None
        if geom is not None:
            geoms_por_ti.setdefault(codigo_ti, []).append(geom)

    registros = []
    for codigo_ti, geoms in geoms_por_ti.items():
        geom = limpar_geometria(unary_union(geoms))
        if geom is not None:
            registros.append({"codigo_ti": codigo_ti, "geometry": geom})

    return gpd.GeoDataFrame(registros, geometry="geometry", crs="EPSG:4326")
