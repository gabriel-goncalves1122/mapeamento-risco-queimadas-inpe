"""
Módulo de funções puras para conversão numérica, validação geográfica e escrita CSV.

Implementa o padrão Functional Core: funções sem estado para validação de coordenadas WGS84
e persistência consistente com terminadores Unix (`\n`) para a camada Silver e Druid.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.silver.utils.cleaners import limpar_numero


def coordenada_valida(lat: Any, lon: Any) -> bool:
    """
    Verifica se o par (lat, lon) — aceitando floats ou strings com vírgula —
    está nos limites WGS84 e descarta a origem nula (0.0, 0.0).
    """
    try:
        if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
            return False
        lat_f = float(str(lat).strip().replace(",", "."))
        lon_f = float(str(lon).strip().replace(",", "."))
        if math.isnan(lat_f) or math.isinf(lat_f) or math.isnan(lon_f) or math.isinf(lon_f):
            return False
        if not (-90.0 <= lat_f <= 90.0) or not (-180.0 <= lon_f <= 180.0):
            return False
        if lat_f == 0.0 and lon_f == 0.0:
            return False
        return True
    except (ValueError, TypeError):
        return False


def salvar_csv(df: pd.DataFrame, caminho: str | Path) -> Path:
    """Persiste DataFrame em UTF-8 com quoting mínimo e quebra de linha padronizada."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        destino,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    return destino
