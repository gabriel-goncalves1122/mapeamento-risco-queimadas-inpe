import pytest
from pydantic import ValidationError

from src.config.constants import NOT_INFORMED
from src.streaming.domain.models import FocoFatoPayload

def test_foco_fato_payload_valido():
    """
    Testa a criação de um payload perfeitamente válido de acordo com
    o modelo arquitetural Snowflake.
    """
    payload_dict = {
        "data_hora": "2023-08-15 14:30:00",
        "pais_origem": "BRASIL",
        "fk_bioma": "CERRADO",
        "fk_satelite_sensor": "AQUA_MODIS",
        
        "fk_municipio": "MG_ITAJUBA",
        "fk_municipio_espacial": "3132404",
        "fk_terra_indigena": NOT_INFORMED,
        "fk_terra_indigena_proxima": NOT_INFORMED,
        "fk_trecho_rodoviario": NOT_INFORMED,
        "fk_linha_transmissao": NOT_INFORMED,
        "fk_subestacao": NOT_INFORMED,
        "fk_sistema_isolado": NOT_INFORMED,
        "fk_hospital": NOT_INFORMED,

        "latitude": -22.42,
        "longitude": -45.45,
        "coordenada_valida": 1,
        "foco_point": "POINT(-45.45 -22.42)",

        "dias_sem_chuva": 10.0,
        "precipitacao_mm": 0.0,
        "risco_fogo_inpe": 0.95,
        "potencia_radiativa_fogo": 120.5,
        "indice_condicao_ambiental": 0.8,
        "indice_queimada_evento": 0.9,

        "distancia_rodovia_km": None,
        "distancia_linha_km": None,
        "distancia_subestacao_km": None,
        "distancia_sistema_isolado_km": None,
        "distancia_hospital_km": None,
        "distancia_terra_indigena_km": None,

        "indice_ameaca_rodovia": 0.0,
        "indice_ameaca_linha": 0.0,
        "indice_ameaca_subestacao": 0.0,
        "indice_ameaca_sistema_isolado": 0.0,
        "indice_pressao_saude": 0.0,
        "indice_pressao_terra_indigena": 0.0,
        "indice_pressao_maxima": 0.0
    }

    payload = FocoFatoPayload(**payload_dict)
    assert payload.fk_bioma == "CERRADO"
    assert payload.coordenada_valida == 1

def test_foco_fato_payload_preserva_contrato_snowflake_sem_nomes_redundantes():
    """
    A fato de streaming deve carregar FKs e métricas, não atributos textuais
    descritivos que pertencem às dimensões.
    """
    campos_proibidos = {
        "nome_municipio",
        "municipio_nome",
        "nome_hospital",
        "nome_subestacao",
        "classe_criticidade_linha",
        "geometria_wkt",
    }

    assert campos_proibidos.isdisjoint(FocoFatoPayload.model_fields)

def test_foco_fato_payload_rejeita_sem_data():
    """
    A tipagem de Snowflake exige estritamente a datetime como Partition Key
    do Apache Druid.
    """
    payload_dict = {
        "pais_origem": "BRASIL",
        # data_hora removido propositalmente
        "fk_bioma": "CERRADO",
        "fk_satelite_sensor": "AQUA_MODIS",
        
        "fk_municipio": "MG_ITAJUBA",
        "fk_municipio_espacial": "3132404",
        "fk_terra_indigena": NOT_INFORMED,
        "fk_terra_indigena_proxima": NOT_INFORMED,
        "fk_trecho_rodoviario": NOT_INFORMED,
        "fk_linha_transmissao": NOT_INFORMED,
        "fk_subestacao": NOT_INFORMED,
        "fk_sistema_isolado": NOT_INFORMED,
        "fk_hospital": NOT_INFORMED,

        "latitude": -22.42,
        "longitude": -45.45,
        "coordenada_valida": 1,
        "foco_point": "POINT(-45.45 -22.42)",

        "dias_sem_chuva": 10.0,
        "precipitacao_mm": 0.0,
        "risco_fogo_inpe": 0.95,
        "potencia_radiativa_fogo": 120.5,
        "indice_condicao_ambiental": 0.8,
        "indice_queimada_evento": 0.9,

        "indice_ameaca_rodovia": 0.0,
        "indice_ameaca_linha": 0.0,
        "indice_ameaca_subestacao": 0.0,
        "indice_ameaca_sistema_isolado": 0.0,
        "indice_pressao_saude": 0.0,
        "indice_pressao_terra_indigena": 0.0,
        "indice_pressao_maxima": 0.0
    }

    with pytest.raises(ValidationError):
        FocoFatoPayload(**payload_dict)
