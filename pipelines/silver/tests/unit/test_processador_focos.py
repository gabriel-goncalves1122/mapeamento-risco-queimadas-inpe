import json

from config.constants import NOT_INFORMED
from pipelines.silver.src.streaming_processing.processador import ProcessadorFocos


class MotorFake:
    def __init__(self):
        self.chamadas = []

    def analisar_todas_ameacas(self, latitude, longitude):
        self.chamadas.append((latitude, longitude))
        return {
            "codigo_ibge_espacial": "3132404",
            "distancia_rodovia_km": 2.5,
            "distancia_linha_km": 7.0,
            "distancia_subestacao_km": 12.0,
            "distancia_sistema_isolado_km": None,
            "distancia_hospital_km": 1.2,
            "distancia_terra_indigena_km": 50.0,
            "linha_tensao_kv": 500.0,
            "subestacao_capacidade_mw": 1200.0,
        }


def test_processador_transforma_linha_suja_em_payload_json_serializavel():
    motor = MotorFake()
    processador = ProcessadorFocos(motor)
    linha = {
        "DataHora": "2025-01-02T03:04:05",
        "Pais": " Brasil ",
        "Estado": "Minas Gerais",
        "Municipio": "São João D'Aliança",
        "Bioma": "Cerrado",
        "Satelite": "Aqua\nModis",
        "Latitude": "-22,5",
        "Longitude": "-45,5",
        "DiaSemChuva": "10",
        "Precipitacao": "0,5",
        "RiscoFogo": "0,8",
        "FRP": "120,5",
    }

    payload = processador.transformar(linha)

    json.dumps(payload, ensure_ascii=False, allow_nan=False)
    assert motor.chamadas == [(-22.5, -45.5)]
    assert payload["pais_origem"] == "BRASIL"
    assert payload["fk_municipio"] == "MINAS GERAIS_SAO JOAO D'ALIANCA"
    assert payload["fk_municipio_espacial"] == "3132404"
    assert payload["fk_terra_indigena"] == NOT_INFORMED
    assert payload["fk_linha_transmissao"] == NOT_INFORMED
    assert payload["coordenada_valida"] == 1
    assert payload["precipitacao_mm"] == 0.5
    assert payload["potencia_radiativa_fogo"] == 120.5


def test_processador_nao_chama_motor_quando_coordenada_invalida():
    motor = MotorFake()
    processador = ProcessadorFocos(motor)

    payload = processador.transformar(
        {
            "DataHora": "sem data",
            "Pais": None,
            "Estado": "",
            "Municipio": "",
            "Bioma": "",
            "Satelite": "",
            "Latitude": "0",
            "Longitude": "0",
            "DiaSemChuva": "-999",
            "Precipitacao": "NaN",
            "RiscoFogo": "abc",
            "FRP": "",
        }
    )

    assert motor.chamadas == []
    assert payload["coordenada_valida"] == 0
    assert payload["latitude"] is None
    assert payload["longitude"] is None
    assert payload["fk_municipio_espacial"] == NOT_INFORMED
    assert payload["fk_municipio"] == f"{NOT_INFORMED}_{NOT_INFORMED}"


def test_processador_payload_nao_expoe_campos_textuais_redundantes():
    payload = ProcessadorFocos(MotorFake()).transformar(
        {
            "DataHora": "2025-01-02",
            "Pais": "Brasil",
            "Estado": "MG",
            "Municipio": "Itajuba",
            "Bioma": "Mata Atlantica",
            "Satelite": "NOAA",
            "Latitude": "-22.4",
            "Longitude": "-45.4",
        }
    )

    campos_proibidos = {
        "nome_municipio",
        "municipio_nome",
        "nome_hospital",
        "nome_subestacao",
        "geometria_wkt",
        "classe_criticidade_linha",
    }
    assert campos_proibidos.isdisjoint(payload)
