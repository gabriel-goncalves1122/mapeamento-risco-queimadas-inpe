"""
Módulo de funções puras para extração e higienização de leituras brutas de satélite.

Implementa o padrão Functional Core: conversão determinística de timestamps para o
contrato `__time` do Druid, validação WGS84 e serialização GeoJSON pontual compacta.
"""
from __future__ import annotations

import json
import math
from typing import Any, Mapping

import pandas as pd

from src.core.config.constants import DEFAULT_EPOCH
from src.silver.utils.cleaners import limpar_valor_numerico_nullable


def extrair_data(valor_data: Any) -> dict[str, Any]:
    """
    Converte o timestamp bruto para o formato ISO esperado pelo Druid (`__time`),
    aplicando `DEFAULT_EPOCH` (`1970-01-01 00:00:00`) como fallback seguro.
    """
    dt_hora = pd.to_datetime(valor_data, errors="coerce")
    if pd.notna(dt_hora):
        return {
            "data_hora": dt_hora.strftime("%Y-%m-%d %H:%M:%S"),
            "data_dia": dt_hora.strftime("%Y-%m-%d"),
            "data_mes": dt_hora.strftime("%Y-%m-01"),
            "ano": int(dt_hora.year),
            "mes": int(dt_hora.month),
            "dia": int(dt_hora.day),
            "hora": int(dt_hora.hour),
            "minuto": int(dt_hora.minute),
        }
    return {
        "data_hora": DEFAULT_EPOCH,
        "data_dia": "1970-01-01",
        "data_mes": "1970-01-01",
        "ano": 1970,
        "mes": 1,
        "dia": 1,
        "hora": 0,
        "minuto": 0,
    }


def extrair_coordenadas(linha_bruta: Mapping[str, Any]) -> tuple[float | None, float | None, int]:
    """
    Extrai `(latitude, longitude, flag_valida)` descartando leituras fora do globo
    ou cravadas na origem nula `(0.0, 0.0)`.
    """
    lat = limpar_valor_numerico_nullable(linha_bruta.get("Latitude"))
    lon = limpar_valor_numerico_nullable(linha_bruta.get("Longitude"))

    coord_valida = (
        lat is not None
        and lon is not None
        and -90.0 <= lat <= 90.0
        and -180.0 <= lon <= 180.0
        and not (lat == 0.0 and lon == 0.0)
    )

    if not coord_valida:
        return None, None, 0
    return lat, lon, 1


def calcular_grids(lat: float | None, lon: float | None, coord_valida: int | bool) -> dict[str, float | None]:
    """Discretiza coordenadas em células de grade espacial (0.2°, 0.1° e 0.01°)."""
    if not coord_valida or lat is None or lon is None:
        return {
            "lat_grid_02": None,
            "lon_grid_02": None,
            "lat_grid_01": None,
            "lon_grid_01": None,
            "lat_grid_001": None,
            "lon_grid_001": None,
        }
    return {
        "lat_grid_02": round(math.floor(lat * 5) / 5, 2),
        "lon_grid_02": round(math.floor(lon * 5) / 5, 2),
        "lat_grid_01": round(math.floor(lat * 10) / 10, 1),
        "lon_grid_01": round(math.floor(lon * 10) / 10, 1),
        "lat_grid_001": round(math.floor(lat * 100) / 100, 2),
        "lon_grid_001": round(math.floor(lon * 100) / 100, 2),
    }


def foco_point(lat: float | None, lon: float | None, coord_valida: int | bool) -> str:
    """Serializa o ponto em GeoJSON compacto sem espaços para visualização no Superset."""
    if not coord_valida or lat is None or lon is None:
        return ""
    return json.dumps(
        {
            "type": "Point",
            "coordinates": [round(float(lon), 6), round(float(lat), 6)],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
