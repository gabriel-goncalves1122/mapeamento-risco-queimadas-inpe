"""
=========================================================
MÓDULO: Auxiliares Espaciais (geo_helpers.py)
---------------------------------------------------------
Função Geral: Abstrai a manipulação bruta de geometrias
vetoriais (Shapely) e GeoDataFrames. Força projeções e
limpa coordenadas sobrepostas para reduzir payload json.
=========================================================
"""
import json
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point


def garantir_crs_4326(gdf):
    """
    Força um GeoDataFrame a adotar a projeção geográfica global WGS 84 (EPSG:4326).
    Necessário porque o Superset/Deck.gl não renderiza coordenadas projetadas (ex: SIRGAS 2000).
    """
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    return gdf.to_crs(epsg=4326)


def arredondar_coord(coord, casas=6):
    return [round(float(coord[0]), casas), round(float(coord[1]), casas)]


def remover_repeticoes_periodicas(coords):
    if not coords:
        return coords

    coords_round = [tuple(arredondar_coord(c)) for c in coords]
    n = len(coords_round)

    for tamanho in range(2, (n // 2) + 1):
        if n % tamanho != 0:
            continue

        base = coords_round[:tamanho]
        repetido = True

        for i in range(0, n, tamanho):
            if coords_round[i:i + tamanho] != base:
                repetido = False
                break

        if repetido:
            return [list(c) for c in base]

    return [list(c) for c in coords_round]


def remover_consecutivos_duplicados(coords):
    if not coords:
        return coords

    limpos = [coords[0]]

    for coord in coords[1:]:
        if coord != limpos[-1]:
            limpos.append(coord)

    return limpos


def limpar_linestring_geometry(geom):
    """
    Remove coordenadas repetidas e anomalias de uma LineString ou MultiLineString.
    
    Por que isso é necessário?
    Muitas bases do ONS contêm polígonos/linhas "sujos" com vértices sobrepostos.
    Isso causa arquivos JSON massivos e lentidão no front-end do Apache Superset.
    A função reduz drasticamente o peso espacial mantendo o formato intacto.
    """
    if geom is None or geom.is_empty:
        return None

    if isinstance(geom, LineString):
        coords = list(geom.coords)
        coords = remover_repeticoes_periodicas(coords)
        coords = remover_consecutivos_duplicados(coords)

        if len(coords) < 2:
            return None

        return LineString(coords)

    if isinstance(geom, MultiLineString):
        linhas = []

        for linha in geom.geoms:
            coords = list(linha.coords)
            coords = remover_repeticoes_periodicas(coords)
            coords = remover_consecutivos_duplicados(coords)

            if len(coords) >= 2:
                linhas.append(LineString(coords))

        if not linhas:
            return None

        if len(linhas) == 1:
            return linhas[0]

        return MultiLineString(linhas)

    return geom


def geometry_para_path_json(geom):
    """
    Converte qualquer objeto geométrico Shapely num formato de Array JSON bidimensional.
    Este é o formato estrito exigido pela camada de visualização Deck.gl (PathLayer/PolygonLayer).
    """
    if geom is None or geom.is_empty:
        return "[]"

    if geom.geom_type == 'Point':
        return json.dumps([arredondar_coord(geom.coords[0])], ensure_ascii=False)

    elif geom.geom_type == 'LineString':
        coords = [arredondar_coord(c) for c in geom.coords]
        return json.dumps(coords, ensure_ascii=False)

    elif geom.geom_type == 'MultiLineString':
        paths = []
        for linha in geom.geoms:
            coords = [arredondar_coord(c) for c in linha.coords]
            paths.append(coords)
        return json.dumps(paths, ensure_ascii=False)

    elif geom.geom_type == 'Polygon':
        coords = [arredondar_coord(c) for c in geom.exterior.coords]
        return json.dumps([coords], ensure_ascii=False)

    elif geom.geom_type == 'MultiPolygon':
        polys = []
        for poly in geom.geoms:
            coords = [arredondar_coord(c) for c in poly.exterior.coords]
            polys.append([coords])
        return json.dumps(polys, ensure_ascii=False)

    return "[]"


def is_coordenada_valida_brasil(lat, lon):
    from config.constants import BRAZIL_LAT_MIN, BRAZIL_LAT_MAX, BRAZIL_LON_MIN, BRAZIL_LON_MAX
    if lat is None or lon is None: return False
    if not (-90 <= lat <= 90): return False
    if not (-180 <= lon <= 180): return False
    if lat == 0.0 and lon == 0.0: return False
    if not (BRAZIL_LAT_MIN <= lat <= BRAZIL_LAT_MAX): return False
    if not (BRAZIL_LON_MIN <= lon <= BRAZIL_LON_MAX): return False
    return True


def normalizar_par_coordenadas(lat, lon):
    import pandas as pd
    candidatos = [
        (lat, lon),
        (-abs(lat) if lat is not None else lat, lon),
        (lat, -abs(lon) if lon is not None else lon),
        (-abs(lat) if lat is not None else lat, -abs(lon) if lon is not None else lon),
    ]
    if lat is not None and lon is not None:
        candidatos.extend([
            (lon, lat),
            (-abs(lon), lat),
            (lon, -abs(lat)),
            (-abs(lon), -abs(lat)),
        ])

    for lat_cand, lon_cand in candidatos:
        if is_coordenada_valida_brasil(lat_cand, lon_cand):
            return pd.Series({"latitude": lat_cand, "longitude": lon_cand})

    return pd.Series({"latitude": None, "longitude": None})


def corrigir_geometria_invalida(geom):
    if geom is None or geom.is_empty: return None
    try:
        if not geom.is_valid: geom = geom.buffer(0)
        return None if geom.is_empty else geom
    except Exception: return None


def adicionar_centroides(gdf):
    from config.constants import EPSG_METRICO
    if gdf.empty:
        gdf['latitude'] = None
        gdf['longitude'] = None
        return gdf
        
    centroides = gdf.to_crs(epsg=EPSG_METRICO).geometry.centroid.to_crs(epsg=4326)
    gdf['latitude'] = centroides.y.round(6)
    gdf['longitude'] = centroides.x.round(6)
    return gdf

