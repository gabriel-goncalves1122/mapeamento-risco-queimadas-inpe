"""
=========================================================
MÓDULO: processador.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import pandas as pd
import warnings
from src.config.constants import NOT_INFORMED

# ==========================================
# 0. Blindagem de Terminal
# ==========================================
warnings.filterwarnings("ignore", category=RuntimeWarning, module="shapely")

from src.utils.cleaners import limpar_texto_druid
from src.streaming.processors.extractor import FogoExtractor
from src.streaming.processors.calculators import FogoCalculators
from src.streaming.domain.models import FocoFatoPayload

class ProcessadorFocos:
    """
    Processador Orquestrador da tabela fato FATO_FOCOS_INCENDIO.
    
    Refatorado para arquitetura Snowflake:
    Gera um payload enxuto (FocoFatoPayload), validado via Pydantic,
    contendo apenas Métricas Numéricas e Chaves Estrangeiras.
    """

    def __init__(self, motor_espacial):
        self.motor = motor_espacial

    def transformar(self, linha_bruta):
        # 1. Extração
        datas = FogoExtractor.extrair_data(linha_bruta.get('DataHora'))

        estado_norm = limpar_texto_druid(linha_bruta.get('Estado'))
        municipio_norm = limpar_texto_druid(linha_bruta.get('Municipio'))
        bioma_norm = limpar_texto_druid(linha_bruta.get('Bioma'))
        satelite_norm = limpar_texto_druid(linha_bruta.get('Satelite'))

        fk_municipio_origem = f"{estado_norm}_{municipio_norm}"

        lat, lon, coord_valida = FogoExtractor.extrair_coordenadas(linha_bruta)
        foco_point = FogoExtractor.foco_point(lat, lon, coord_valida)

        dias_sem_chuva = FogoExtractor.limpar_valor_numerico_nullable(linha_bruta.get('DiaSemChuva'))
        precipitacao_mm = FogoExtractor.limpar_valor_numerico_nullable(linha_bruta.get('Precipitacao'))
        risco_fogo_inpe = FogoExtractor.limpar_valor_numerico_nullable(linha_bruta.get('RiscoFogo'))
        frp = FogoExtractor.limpar_valor_numerico_nullable(linha_bruta.get('FRP'))

        # 2. Cálculos Puros (Apenas Índices contínuos, as classes de texto foram removidas para o Druid tratar)
        indice_condicao_ambiental = FogoCalculators.indice_condicao_ambiental(risco_fogo_inpe, dias_sem_chuva, precipitacao_mm)
        indice_queimada_evento = FogoCalculators.indice_queimada_evento(frp, risco_fogo_inpe, dias_sem_chuva, precipitacao_mm)

        # 3. Motor Espacial
        if coord_valida:
            analise = self.motor.analisar_todas_ameacas(lat, lon)
        else:
            analise = {}

        distancia_rodovia = analise.get('distancia_rodovia_km')
        distancia_linha = analise.get('distancia_linha_km')
        distancia_subestacao = analise.get('distancia_subestacao_km')
        distancia_sistema = analise.get('distancia_sistema_isolado_km')
        distancia_hospital = analise.get('distancia_hospital_km')
        distancia_ti = analise.get('distancia_terra_indigena_km')

        linha_tensao_kv = analise.get("linha_tensao_kv")
        subestacao_capacidade_mw = analise.get("subestacao_capacidade_mw")

        # 4. Cálculos Puros dependentes do Espacial
        indices = FogoCalculators.calcular_indices_ameaca(
            frp=frp, risco=risco_fogo_inpe,
            dist_rodovia=distancia_rodovia, dist_linha=distancia_linha,
            dist_sub=distancia_subestacao, dist_sis=distancia_sistema,
            dist_hosp=distancia_hospital, dist_ti=distancia_ti,
            tensao_kv=linha_tensao_kv, capac_mw=subestacao_capacidade_mw
        )

        indice_pressao_maxima = max(
            indices["indice_ameaca_rodovia"], indices["indice_ameaca_linha"],
            indices["indice_ameaca_subestacao"], indices["indice_ameaca_sistema_isolado"],
            indices["indice_pressao_saude"], indices["indice_pressao_terra_indigena"]
        )

        # 5. Payload Assembly com validação Pydantic (Snowflake Fact Table)
        payload_obj = FocoFatoPayload(
            data_hora=datas["data_hora"],
            
            pais_origem=limpar_texto_druid(linha_bruta.get('Pais')),
            fk_bioma=bioma_norm,
            fk_satelite_sensor=satelite_norm,
            
            fk_municipio=fk_municipio_origem,
            fk_municipio_espacial=analise.get("codigo_ibge_espacial", NOT_INFORMED),
            fk_terra_indigena=analise.get("codigo_ti", NOT_INFORMED),
            fk_terra_indigena_proxima=analise.get("codigo_ti_proxima", NOT_INFORMED),
            fk_trecho_rodoviario=analise.get("id_trecho_rodoviario", NOT_INFORMED),
            fk_linha_transmissao=analise.get("id_linha_transmissao", NOT_INFORMED),
            fk_subestacao=analise.get("id_subestacao", NOT_INFORMED),
            fk_sistema_isolado=analise.get("id_sistema_isolado", NOT_INFORMED),
            fk_hospital=analise.get("codigo_cnes_prox", NOT_INFORMED),

            latitude=lat,
            longitude=lon,
            coordenada_valida=1 if coord_valida else 0,
            foco_point=foco_point,

            dias_sem_chuva=dias_sem_chuva,
            precipitacao_mm=precipitacao_mm,
            risco_fogo_inpe=risco_fogo_inpe,
            potencia_radiativa_fogo=frp,
            indice_condicao_ambiental=indice_condicao_ambiental,
            indice_queimada_evento=indice_queimada_evento,

            distancia_rodovia_km=distancia_rodovia,
            distancia_linha_km=distancia_linha,
            distancia_subestacao_km=distancia_subestacao,
            distancia_sistema_isolado_km=distancia_sistema,
            distancia_hospital_km=distancia_hospital,
            distancia_terra_indigena_km=distancia_ti,

            indice_ameaca_rodovia=indices["indice_ameaca_rodovia"],
            indice_ameaca_linha=indices["indice_ameaca_linha"],
            indice_ameaca_subestacao=indices["indice_ameaca_subestacao"],
            indice_ameaca_sistema_isolado=indices["indice_ameaca_sistema_isolado"],
            indice_pressao_saude=indices["indice_pressao_saude"],
            indice_pressao_terra_indigena=indices["indice_pressao_terra_indigena"],
            indice_pressao_maxima=round(indice_pressao_maxima, 6)
        )

        return payload_obj.model_dump(mode='json')
