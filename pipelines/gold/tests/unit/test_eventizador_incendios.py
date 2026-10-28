import json

import pandas as pd

from config.constants import NOT_INFORMED
from pipelines.gold.src.science.dbscan.eventizador import EventoConfig, EventizadorIncendios


class MotorFakeEventos:
    def __init__(self):
        self.chamadas = []

    def analisar_todas_ameacas(self, latitude, longitude):
        self.chamadas.append((latitude, longitude))
        return {
            "codigo_ibge_espacial": "3132404",
            "codigo_ti": NOT_INFORMED,
            "codigo_ti_proxima": "TI_001",
            "id_trecho_rodoviario": "BR_001",
            "id_linha_transmissao": "LT_001",
            "id_subestacao": "SE_001",
            "id_sistema_isolado": "SIS_001",
            "codigo_cnes_prox": "CNES_001",
            "distancia_rodovia_km": 2.0,
            "distancia_linha_km": 4.0,
            "distancia_subestacao_km": 8.0,
            "distancia_sistema_isolado_km": 12.0,
            "distancia_hospital_km": 1.0,
            "distancia_terra_indigena_km": 20.0,
            "linha_tensao_kv": 500.0,
            "subestacao_capacidade_mw": 1200.0,
        }


def _raw(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "DataHora",
            "Satelite",
            "Pais",
            "Estado",
            "Municipio",
            "Bioma",
            "DiaSemChuva",
            "Precipitacao",
            "RiscoFogo",
            "FRP",
            "Latitude",
            "Longitude",
        ],
    )


def _eventizador(min_samples=3, max_duration_days=7):
    return EventizadorIncendios(
        MotorFakeEventos(),
        EventoConfig(
            eps_km=5.0,
            eps_dias=2.0,
            min_samples=min_samples,
            max_duration_days=max_duration_days,
            area_buffer_km=0.5,
        ),
    )


def test_eventizador_nao_emite_singletons_abaixo_do_min_samples():
    eventos = _eventizador().eventizar_focos(
        _raw(
            [
                ["2025-01-01 00:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.40", "-45.40"],
                ["2025-01-01 00:10:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "12", "-22.401", "-45.401"],
            ]
        )
    )

    assert eventos == []


def test_eventizador_agrupa_focos_proximos_em_evento_json_serializavel():
    eventos = _eventizador().eventizar_focos(
        _raw(
            [
                ["2025-01-01 00:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0.1", "0.5", "10", "-22.400", "-45.400"],
                ["2025-01-01 00:10:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "4", "0.0", "0.6", "20", "-22.401", "-45.401"],
                ["2025-01-01 00:20:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "5", "0.0", "0.7", "30", "-22.402", "-45.402"],
            ]
        )
    )

    assert len(eventos) == 1
    evento = eventos[0]
    json.dumps(evento, ensure_ascii=False, allow_nan=False)
    assert evento["total_focos"] == 3
    assert evento["soma_frp"] == 60.0
    assert evento["fk_municipio_principal"] == "3132404"
    assert evento["codigos_ibge_interceptados"] == ["3132404"]
    assert evento["fk_hospital"] == "CNES_001"
    assert evento["path_json"] != "[]"
    assert -23 < evento["latitude_centroide"] < -22
    assert -46 < evento["longitude_centroide"] < -45


def test_eventizador_separa_eventos_distantes_no_tempo():
    eventos = _eventizador(max_duration_days=7).eventizar_focos(
        _raw(
            [
                ["2025-01-01 00:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.400", "-45.400"],
                ["2025-01-01 01:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.401", "-45.401"],
                ["2025-01-01 02:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.402", "-45.402"],
                ["2025-01-20 00:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.400", "-45.400"],
                ["2025-01-20 01:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.401", "-45.401"],
                ["2025-01-20 02:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.402", "-45.402"],
            ]
        )
    )

    assert len(eventos) == 2
    assert all(evento["duracao_dias"] <= 7 for evento in eventos)


def test_eventizador_separa_eventos_distantes_no_espaco():
    eventos = _eventizador().eventizar_focos(
        _raw(
            [
                ["2025-01-01 00:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.400", "-45.400"],
                ["2025-01-01 01:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.401", "-45.401"],
                ["2025-01-01 02:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.402", "-45.402"],
                ["2025-01-01 00:00:00", "GOES", "Brasil", "MT", "Cuiaba", "Cerrado", "3", "0", "0.5", "10", "-15.600", "-56.100"],
                ["2025-01-01 01:00:00", "GOES", "Brasil", "MT", "Cuiaba", "Cerrado", "3", "0", "0.5", "10", "-15.601", "-56.101"],
                ["2025-01-01 02:00:00", "GOES", "Brasil", "MT", "Cuiaba", "Cerrado", "3", "0", "0.5", "10", "-15.602", "-56.102"],
            ]
        )
    )

    assert len(eventos) == 2


def test_eventizador_descarta_coordenadas_fora_do_brasil():
    focos = _eventizador().preparar_focos(
        _raw(
            [
                ["2025-01-01 00:00:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "91", "-45.400"],
                ["2025-01-01 00:10:00", "GOES", "Brasil", "MG", "Itajuba", "Cerrado", "3", "0", "0.5", "10", "-22.4", "-10"],
            ]
        )
    )

    assert focos.empty
