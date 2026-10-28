"""
=========================================================
MÓDULO: calculators.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import math

class FogoCalculators:
    """
    Funções puras e estáticas para cálculos de índices de fogo
    e ameaças territoriais/ambientais.
    """

    @staticmethod
    def safe_div(numerador, denominador):
        if numerador is None:
            numerador = 0.0
        if denominador is None or denominador <= 0:
            denominador = 0.1
        return numerador / denominador

    @staticmethod
    def classe_frp(frp):
        if frp is None: return "SEM_FRP"
        if frp >= 100: return "EXTREMA"
        if frp >= 50: return "ALTA"
        if frp >= 10: return "MEDIA"
        if frp > 0: return "BAIXA"
        return "SEM_FRP"

    @staticmethod
    def classe_risco_inpe(risco):
        if risco is None: return "SEM_RISCO"
        if risco >= 0.8: return "RISCO_ALTO"
        if risco >= 0.5: return "RISCO_MEDIO"
        if risco > 0: return "RISCO_BAIXO"
        return "SEM_RISCO"

    @staticmethod
    def indice_condicao_ambiental(risco, dias_sem_chuva, precipitacao):
        risco_base = risco if risco is not None else 0.0
        dias_base = dias_sem_chuva if dias_sem_chuva is not None else 0.0
        chuva_base = precipitacao if precipitacao is not None else 0.0
        return round(risco_base * math.log(dias_base + 1) / (1 + chuva_base), 6)

    @staticmethod
    def classe_condicao_ambiental(indice):
        if indice >= 1.5: return "CONDICAO_CRITICA"
        if indice >= 0.8: return "CONDICAO_ALTA"
        if indice >= 0.3: return "CONDICAO_MEDIA"
        return "CONDICAO_BAIXA"

    @staticmethod
    def classe_indice(valor):
        if valor is None: return "SEM_INDICE"
        if valor >= 100: return "CRITICO"
        if valor >= 30: return "ALTO"
        if valor >= 10: return "MEDIO"
        if valor > 0: return "BAIXO"
        return "SEM_INDICE"

    @staticmethod
    def classe_pressao_territorial(indice):
        if indice >= 300: return "PRESSAO_CRITICA"
        if indice >= 100: return "PRESSAO_ALTA"
        if indice >= 30: return "PRESSAO_MEDIA"
        if indice > 0: return "PRESSAO_BAIXA"
        return "SEM_PRESSAO"

    @staticmethod
    def calcular_indices_ameaca(frp, risco, dist_rodovia, dist_linha, dist_sub, dist_sis, dist_hosp, dist_ti, tensao_kv, capac_mw):
        frp_base = frp if frp is not None else 0.0
        risco_base = risco if risco is not None else 0.0
        fator_risco = 1 + risco_base
        tensao_base = tensao_kv if tensao_kv is not None else 1.0
        capacidade_base = capac_mw if capac_mw is not None else 1.0

        return {
            "indice_ameaca_rodovia": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_rodovia), 6),
            "indice_ameaca_linha": round(FogoCalculators.safe_div(frp_base * fator_risco * math.log(tensao_base + 1), dist_linha), 6),
            "indice_ameaca_subestacao": round(FogoCalculators.safe_div(frp_base * fator_risco * math.log(capacidade_base + 1), dist_sub), 6),
            "indice_ameaca_sistema_isolado": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_sis), 6),
            "indice_pressao_saude": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_hosp), 6),
            "indice_pressao_terra_indigena": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_ti), 6),
        }

    @staticmethod
    def indice_queimada_evento(frp, risco, dias_sem_chuva, precipitacao):
        frp_base = frp if frp is not None else 0.0
        risco_base = risco if risco is not None else 0.0
        dias_base = dias_sem_chuva if dias_sem_chuva is not None else 0.0
        chuva_base = precipitacao if precipitacao is not None else 0.0

        indice = math.log(frp_base + 1) * (1 + risco_base) * (1 + math.log(dias_base + 1)) / (1 + chuva_base)
        return round(indice, 6)

    @staticmethod
    def classe_queimada_evento(indice):
        if indice >= 20: return "EVENTO_CRITICO"
        if indice >= 10: return "EVENTO_ALTO"
        if indice >= 4: return "EVENTO_MEDIO"
        if indice > 0: return "EVENTO_BAIXO"
        return "SEM_EVENTO"
