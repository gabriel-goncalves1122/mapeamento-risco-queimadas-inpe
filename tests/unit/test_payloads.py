import pytest
from pydantic import ValidationError

from src.config.constants import NOT_INFORMED
from src.streaming.domain.models import EventoFatoPayload, FocoFatoPayload

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


def test_evento_fato_payload_valido_e_sem_textos_redundantes():
    payload = EventoFatoPayload(
        fire_event_id="EVT_20250101000000_abcdef1234",
        data_inicio="2025-01-01 00:00:00",
        data_fim="2025-01-01 01:00:00",
        pais_origem="BRASIL",
        fk_bioma="CERRADO",
        fk_satelite_sensor="GOES",
        fk_municipio_principal="3132404",
        codigos_ibge_interceptados=["3132404"],
        qtd_municipios_interceptados=1,
        fk_terra_indigena=NOT_INFORMED,
        codigos_ti_interceptadas=[NOT_INFORMED],
        qtd_terras_indigenas_interceptadas=0,
        fk_terra_indigena_proxima="TI_001",
        fk_trecho_rodoviario="BR_001",
        fk_linha_transmissao="LT_001",
        fk_subestacao="SE_001",
        fk_sistema_isolado="SIS_001",
        fk_hospital="CNES_001",
        latitude_centroide=-22.4,
        longitude_centroide=-45.4,
        path_json="[[[-45.4,-22.4],[-45.41,-22.4],[-45.4,-22.41],[-45.4,-22.4]]]",
        total_focos=3,
        duracao_horas=1.0,
        duracao_dias=0.041667,
        area_evento_km2=1.2,
        soma_frp=60.0,
        media_frp=20.0,
        max_frp=30.0,
        media_risco_fogo=0.6,
        max_risco_fogo=0.7,
        media_dias_sem_chuva=4.0,
        media_precipitacao_mm=0.1,
        indice_condicao_ambiental_medio=0.5,
        indice_queimada_evento_medio=1.2,
        indice_queimada_evento_max=2.0,
        distancia_rodovia_km=2.0,
        distancia_linha_km=4.0,
        distancia_subestacao_km=8.0,
        distancia_sistema_isolado_km=12.0,
        distancia_hospital_km=1.0,
        distancia_terra_indigena_km=20.0,
        indice_ameaca_rodovia=1.0,
        indice_ameaca_linha=2.0,
        indice_ameaca_subestacao=3.0,
        indice_ameaca_sistema_isolado=4.0,
        indice_pressao_saude=5.0,
        indice_pressao_terra_indigena=6.0,
        indice_pressao_maxima=6.0,
        param_eps_km=5.0,
        param_eps_dias=2.0,
        param_min_samples=3,
        param_max_duration_days=7.0,
    )

    campos_proibidos = {
        "nome_municipio",
        "nome_hospital",
        "nome_terra_indigena",
        "geometria_wkt",
        "classe_criticidade_linha",
    }

    assert campos_proibidos.isdisjoint(EventoFatoPayload.model_fields)
    assert payload.total_focos == 3


def test_evento_fato_payload_rejeita_nan():
    payload = {}
    payload.update(
        {
            "fire_event_id": "EVT",
            "data_inicio": "2025-01-01 00:00:00",
            "data_fim": "2025-01-01 01:00:00",
            "pais_origem": "BRASIL",
            "fk_bioma": "CERRADO",
            "fk_satelite_sensor": "GOES",
            "fk_municipio_principal": "3132404",
            "codigos_ibge_interceptados": ["3132404"],
            "qtd_municipios_interceptados": 1,
            "fk_terra_indigena": NOT_INFORMED,
            "codigos_ti_interceptadas": [NOT_INFORMED],
            "qtd_terras_indigenas_interceptadas": 0,
            "fk_terra_indigena_proxima": NOT_INFORMED,
            "fk_trecho_rodoviario": NOT_INFORMED,
            "fk_linha_transmissao": NOT_INFORMED,
            "fk_subestacao": NOT_INFORMED,
            "fk_sistema_isolado": NOT_INFORMED,
            "fk_hospital": NOT_INFORMED,
            "latitude_centroide": float("nan"),
            "longitude_centroide": -45.4,
            "path_json": "[]",
            "total_focos": 3,
            "duracao_horas": 1.0,
            "duracao_dias": 0.1,
            "area_evento_km2": 0.1,
            "soma_frp": 1.0,
            "media_frp": 1.0,
            "max_frp": 1.0,
            "media_risco_fogo": 0.1,
            "max_risco_fogo": 0.1,
            "media_dias_sem_chuva": 1.0,
            "media_precipitacao_mm": 0.0,
            "indice_condicao_ambiental_medio": 0.1,
            "indice_queimada_evento_medio": 0.1,
            "indice_queimada_evento_max": 0.1,
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
            "indice_pressao_maxima": 0.0,
            "param_eps_km": 5.0,
            "param_eps_dias": 2.0,
            "param_min_samples": 3,
            "param_max_duration_days": 7.0,
        }
    )

    with pytest.raises(ValidationError):
        EventoFatoPayload(**payload)
