"""
Codec de serialização bidirecional entre geometrias Shapely e arrays JSON (`PathJsonCodec`).

O Apache Superset (Deck.gl) exige coordenadas em arrays `[lon, lat]` serializados em
JSON (`path_json`), enquanto o `SpatialLayerLoader` e o `SINNetworkCentralityModel`
precisam reconstruir objetos Shapely a partir desse mesmo contrato sem depender de WKT.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

import pandas as pd
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry


class PathJsonCodec:
    """Codificador e decodificador estático de geometrias `path_json`."""

    @staticmethod
    def arredondar_coord(coord: Sequence[float], casas: int = 6) -> list[float]:
        """Limita a precisão decimal das coordenadas para reduzir o volume do CSV/JSON."""
        return [round(float(coord[0]), casas), round(float(coord[1]), casas)]

    @staticmethod
    def _coord_valida(valor: Any) -> bool:
        return (
            isinstance(valor, list)
            and len(valor) >= 2
            and all(isinstance(v, (int, float)) for v in valor[:2])
        )

    @staticmethod
    def _limpar_coord_path(valor: Sequence[Any]) -> tuple[float, float]:
        return (float(valor[0]), float(valor[1]))

    @classmethod
    def _line_string_ou_none(cls, coords: Sequence[Any]) -> LineString | None:
        try:
            pontos = [cls._limpar_coord_path(c) for c in coords if cls._coord_valida(c)]
            return LineString(pontos) if len(pontos) >= 2 else None
        except Exception:
            return None

    @classmethod
    def _polygon_ou_none(cls, coords: Sequence[Any]) -> BaseGeometry | None:
        try:
            pontos = [cls._limpar_coord_path(c) for c in coords if cls._coord_valida(c)]
            if len(pontos) < 4:
                return None
            geom = Polygon(pontos)
            if not geom.is_valid:
                geom = geom.buffer(0)
            return None if geom.is_empty else geom
        except Exception:
            return None

    @classmethod
    def geometry_para_path_json(cls, geom: BaseGeometry | None) -> str:
        """Serializa geometria Shapely no formato JSON esperado pelas camadas Deck.gl."""
        if geom is None or geom.is_empty:
            return "[]"

        if geom.geom_type == "Point":
            return json.dumps([cls.arredondar_coord(geom.coords[0])], ensure_ascii=False)

        if geom.geom_type == "LineString":
            coords = [cls.arredondar_coord(c) for c in geom.coords]
            return json.dumps(coords, ensure_ascii=False)

        if geom.geom_type == "MultiLineString":
            paths = [[cls.arredondar_coord(c) for c in linha.coords] for linha in geom.geoms]
            return json.dumps(paths, ensure_ascii=False)

        if geom.geom_type == "Polygon":
            coords = [cls.arredondar_coord(c) for c in geom.exterior.coords]
            return json.dumps([coords], ensure_ascii=False)

        if geom.geom_type == "MultiPolygon":
            polys = [[[cls.arredondar_coord(c) for c in poly.exterior.coords]] for poly in geom.geoms]
            return json.dumps(polys, ensure_ascii=False)

        return "[]"

    @classmethod
    def path_json_para_geometry(cls, valor: Any, tipo_geometria: str = "line") -> BaseGeometry | None:
        """
        Reconstrói objeto Shapely (`Point`, `LineString`/`MultiLineString` ou
        `Polygon`/`MultiPolygon`) a partir de uma string `path_json`.
        """
        try:
            if pd.isna(valor):
                return None
            data = json.loads(str(valor))
            if not data:
                return None

            tipo = str(tipo_geometria).lower()

            if tipo == "point":
                if cls._coord_valida(data):
                    return Point(cls._limpar_coord_path(data))
                if isinstance(data, list) and data and cls._coord_valida(data[0]):
                    return Point(cls._limpar_coord_path(data[0]))
                return None

            if tipo == "line":
                if isinstance(data, list) and data and cls._coord_valida(data[0]):
                    return cls._line_string_ou_none(data)
                linhas = [cls._line_string_ou_none(linha) for linha in data if isinstance(linha, list)]
                linhas_validas = [linha for linha in linhas if linha is not None]
                if not linhas_validas:
                    return None
                return linhas_validas[0] if len(linhas_validas) == 1 else MultiLineString(linhas_validas)

            if tipo == "polygon":
                if isinstance(data, list) and data and cls._coord_valida(data[0]):
                    return cls._polygon_ou_none(data)
                if (
                    isinstance(data, list)
                    and data
                    and isinstance(data[0], list)
                    and data[0]
                    and cls._coord_valida(data[0][0])
                ):
                    return cls._polygon_ou_none(data[0])
                poligonos = []
                for poly in data:
                    if isinstance(poly, list) and poly and isinstance(poly[0], list):
                        geom = cls._polygon_ou_none(poly[0])
                        if geom is not None:
                            poligonos.append(geom)
                if not poligonos:
                    return None
                return poligonos[0] if len(poligonos) == 1 else MultiPolygon(poligonos)

            return None
        except Exception:
            return None
