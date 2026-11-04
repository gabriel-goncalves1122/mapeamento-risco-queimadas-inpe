import math

from src.silver.streaming_processing.processors.calculators import (
    calcular_indices_ameaca,
    indice_queimada_evento,
    safe_div,
)


def test_calculators_normalizam_nulos_sem_nan():
    indices = calcular_indices_ameaca(
        frp=None,
        risco=None,
        dist_rodovia=None,
        dist_linha=None,
        dist_sub=None,
        dist_sis=None,
        dist_hosp=None,
        dist_ti=None,
        tensao_kv=None,
        capac_mw=None,
    )

    assert set(indices) == {
        "indice_ameaca_rodovia",
        "indice_ameaca_linha",
        "indice_ameaca_subestacao",
        "indice_ameaca_sistema_isolado",
        "indice_pressao_saude",
        "indice_pressao_terra_indigena",
    }
    assert all(valor == 0.0 for valor in indices.values())
    assert not any(math.isnan(valor) for valor in indices.values())


def test_indice_queimada_evento_reage_a_frp_risco_e_seca():
    baixo = indice_queimada_evento(1.0, 0.1, 1.0, 10.0)
    alto = indice_queimada_evento(120.0, 0.9, 30.0, 0.0)

    assert alto > baixo


def test_safe_div_usa_fallback_para_denominador_invalido():
    assert safe_div(10, None) == 100.0
    assert safe_div(10, 0) == 100.0
    assert safe_div(10, -3) == 100.0


def test_indices_ameaca_sao_finitos_com_distancias_invalidas():
    indices = calcular_indices_ameaca(
        frp=50.0,
        risco=0.8,
        dist_rodovia=0,
        dist_linha=-1,
        dist_sub=None,
        dist_sis=0,
        dist_hosp=-3,
        dist_ti=None,
        tensao_kv=None,
        capac_mw=None,
    )

    assert all(math.isfinite(valor) for valor in indices.values())
    assert all(valor >= 0 for valor in indices.values())
