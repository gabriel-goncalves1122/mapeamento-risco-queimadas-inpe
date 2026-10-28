"""
=========================================================
MÓDULO: extractor.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import math
import json
import pandas as pd
from config.constants import DEFAULT_EPOCH, NOT_INFORMED

class FogoExtractor:
    """
    Funções puras e estáticas para extração de dados brutos:
    - Conversão de tipos.
    - Lógica de extração de tempo, coordenadas e grids.
    """

    @staticmethod
    def limpar_valor_numerico_nullable(valor):
        try:
            if valor is None or pd.isna(valor):
                return None
            texto = str(valor).strip().replace(',', '.')
            if texto == "":
                return None
            f_valor = float(texto)
            if math.isnan(f_valor) or math.isinf(f_valor) or f_valor <= -900:
                return None
            return f_valor
        except (ValueError, TypeError):
            return None

    @staticmethod
    def texto_idx(valor):
        if valor is None or pd.isna(valor):
            return NOT_INFORMED
        texto = str(valor).strip()
        return texto if texto else NOT_INFORMED

    @staticmethod
    def flag_idx(valor_flag):
        return "SIM" if valor_flag == 1 else "NAO"

    @staticmethod
    def extrair_data(valor_data):
        dt_hora = pd.to_datetime(valor_data, errors='coerce')
        if pd.notna(dt_hora):
            return {
                "data_hora": dt_hora.strftime('%Y-%m-%d %H:%M:%S'),
                "data_dia": dt_hora.strftime('%Y-%m-%d'),
                "data_mes": dt_hora.strftime('%Y-%m-01'),
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
            "ano": 1970, "mes": 1, "dia": 1, "hora": 0, "minuto": 0,
        }

    @staticmethod
    def extrair_coordenadas(linha_bruta):
        lat = FogoExtractor.limpar_valor_numerico_nullable(linha_bruta.get('Latitude'))
        lon = FogoExtractor.limpar_valor_numerico_nullable(linha_bruta.get('Longitude'))

        coord_valida = (
            lat is not None and lon is not None and
            -90 <= lat <= 90 and -180 <= lon <= 180 and
            not (lat == 0.0 and lon == 0.0)
        )

        if not coord_valida:
            return None, None, 0
        return lat, lon, 1

    @staticmethod
    def calcular_grids(lat, lon, coord_valida):
        if not coord_valida:
            return {
                "lat_grid_02": None, "lon_grid_02": None,
                "lat_grid_01": None, "lon_grid_01": None,
                "lat_grid_001": None, "lon_grid_001": None,
            }
        return {
            "lat_grid_02": round(math.floor(lat * 5) / 5, 2),
            "lon_grid_02": round(math.floor(lon * 5) / 5, 2),
            "lat_grid_01": round(math.floor(lat * 10) / 10, 1),
            "lon_grid_01": round(math.floor(lon * 10) / 10, 1),
            "lat_grid_001": round(math.floor(lat * 100) / 100, 2),
            "lon_grid_001": round(math.floor(lon * 100) / 100, 2),
        }

    @staticmethod
    def foco_point(lat, lon, coord_valida):
        if not coord_valida:
            return ""
        return json.dumps(
            {
                "type": "Point",
                "coordinates": [round(float(lon), 6), round(float(lat), 6)]
            },
            ensure_ascii=False,
            separators=(',', ':')
        )
