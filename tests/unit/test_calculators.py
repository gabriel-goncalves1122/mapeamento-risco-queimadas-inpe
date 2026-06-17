import math

import pytest

from src.streaming.processors.calculators import FogoCalculators


def test_calculators_normalizam_nulos_sem_nan():
    indices = FogoCalculators.calcular_indices_ameaca(
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
    baixo = FogoCalculators.indice_queimada_evento(1.0, 0.1, 1.0, 10.0)
    alto = FogoCalculators.indice_queimada_evento(120.0, 0.9, 30.0, 0.0)

    assert alto > baixo


@pytest.mark.parametrize(
    ("frp", "classe"),
    [(None, "SEM_FRP"), (0, "SEM_FRP"), (1, "BAIXA"), (10, "MEDIA"), (50, "ALTA"), (100, "EXTREMA")],
)
def test_classe_frp_respeita_limiares(frp, classe):
    assert FogoCalculators.classe_frp(frp) == classe


@pytest.mark.parametrize(
    ("risco", "classe"),
    [(None, "SEM_RISCO"), (0, "SEM_RISCO"), (0.1, "RISCO_BAIXO"), (0.5, "RISCO_MEDIO"), (0.8, "RISCO_ALTO")],
)
def test_classe_risco_inpe_respeita_limiares(risco, classe):
    assert FogoCalculators.classe_risco_inpe(risco) == classe


@pytest.mark.parametrize(
    ("valor", "classe"),
    [(None, "SEM_INDICE"), (0, "SEM_INDICE"), (1, "BAIXO"), (10, "MEDIO"), (30, "ALTO"), (100, "CRITICO")],
)
def test_classe_indice_respeita_limiares(valor, classe):
    assert FogoCalculators.classe_indice(valor) == classe


@pytest.mark.parametrize(
    ("valor", "classe"),
    [(0, "SEM_PRESSAO"), (1, "PRESSAO_BAIXA"), (30, "PRESSAO_MEDIA"), (100, "PRESSAO_ALTA"), (300, "PRESSAO_CRITICA")],
)
def test_classe_pressao_territorial_respeita_limiares(valor, classe):
    assert FogoCalculators.classe_pressao_territorial(valor) == classe


@pytest.mark.parametrize(
    ("valor", "classe"),
    [(0, "SEM_EVENTO"), (1, "EVENTO_BAIXO"), (4, "EVENTO_MEDIO"), (10, "EVENTO_ALTO"), (20, "EVENTO_CRITICO")],
)
def test_classe_queimada_evento_respeita_limiares(valor, classe):
    assert FogoCalculators.classe_queimada_evento(valor) == classe


def test_safe_div_usa_fallback_para_denominador_invalido():
    assert FogoCalculators.safe_div(10, None) == 100.0
    assert FogoCalculators.safe_div(10, 0) == 100.0
    assert FogoCalculators.safe_div(10, -3) == 100.0


def test_indices_ameaca_sao_finitos_com_distancias_invalidas():
    indices = FogoCalculators.calcular_indices_ameaca(
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
