"""
Módulo de funções puras para cálculo de índices compostos de severidade e ameaça territorial.

Implementa o padrão Functional Core: equações logarítmicas de amortecimento climático
(precipitação vs. estiagem) e de decaimento espacial (inverso da distância até ativos críticos
ponderado por tensão kV e capacidade MW) sem estado oculto.
"""
from __future__ import annotations

import math


def safe_div(numerador: float | None, denominador: float | None) -> float:
    """
    Evita divisão por zero quando um foco incide exatamente sobre o ativo (`dist = 0`),
    fixando um piso de 100 metros (`0.1 km`) no denominador.
    """
    num = numerador if numerador is not None else 0.0
    den = denominador if (denominador is not None and denominador > 0) else 0.1
    return num / den


def indice_condicao_ambiental(
    risco: float | None,
    dias_sem_chuva: float | None,
    precipitacao: float | None,
) -> float:
    """Combina o Risco de Fogo INPE com o logaritmo da estiagem amortecido pela chuva."""
    risco_base = risco if risco is not None else 0.0
    dias_base = max(dias_sem_chuva if dias_sem_chuva is not None else 0.0, 0.0)
    chuva_base = max(precipitacao if precipitacao is not None else 0.0, 0.0)
    return round(risco_base * math.log(dias_base + 1.0) / (1.0 + chuva_base), 6)


def indice_queimada_evento(
    frp: float | None,
    risco: float | None,
    dias_sem_chuva: float | None,
    precipitacao: float | None,
) -> float:
    """Pondera a energia radiativa (`FRP`) pela condição termo-hidrológica local."""
    frp_base = max(frp if frp is not None else 0.0, 0.0)
    risco_base = max(risco if risco is not None else 0.0, 0.0)
    dias_base = max(dias_sem_chuva if dias_sem_chuva is not None else 0.0, 0.0)
    chuva_base = max(precipitacao if precipitacao is not None else 0.0, 0.0)

    indice = (
        math.log(frp_base + 1.0)
        * (1.0 + risco_base)
        * (1.0 + math.log(dias_base + 1.0))
        / (1.0 + chuva_base)
    )
    return round(indice, 6)


def calcular_indices_ameaca(
    frp: float | None,
    risco: float | None,
    dist_rodovia: float | None,
    dist_linha: float | None,
    dist_sub: float | None,
    dist_sis: float | None,
    dist_hosp: float | None,
    dist_ti: float | None,
    tensao_kv: float | None,
    capac_mw: float | None,
) -> dict[str, float]:
    """
    Calcula os 6 índices de pressão/ameaça inversamente proporcionais à distância métrica,
    amplificando o peso de linhas de transmissão e subestações pelo porte energético.
    """
    frp_base = max(frp if frp is not None else 0.0, 0.0)
    risco_base = max(risco if risco is not None else 0.0, 0.0)
    fator_risco = 1.0 + risco_base
    tensao_base = max(tensao_kv if tensao_kv is not None else 1.0, 0.0)
    capacidade_base = max(capac_mw if capac_mw is not None else 1.0, 0.0)

    return {
        "indice_ameaca_rodovia": round(safe_div(frp_base * fator_risco, dist_rodovia), 6),
        "indice_ameaca_linha": round(
            safe_div(frp_base * fator_risco * math.log(tensao_base + 1.0), dist_linha), 6
        ),
        "indice_ameaca_subestacao": round(
            safe_div(frp_base * fator_risco * math.log(capacidade_base + 1.0), dist_sub), 6
        ),
        "indice_ameaca_sistema_isolado": round(safe_div(frp_base * fator_risco, dist_sis), 6),
        "indice_pressao_saude": round(safe_div(frp_base * fator_risco, dist_hosp), 6),
        "indice_pressao_terra_indigena": round(safe_div(frp_base * fator_risco, dist_ti), 6),
    }
