"""
=========================================================
MÓDULO: processador.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import pandas as pd
import warnings
from config.constants import NOT_INFORMED

# ==========================================
# 0. Blindagem de Terminal
# ==========================================
warnings.filterwarnings("ignore", category=RuntimeWarning, module="shapely")

from pipelines.silver.utils.cleaners import limpar_texto_druid
from pipelines.silver.src.streaming_processing.processors.extractor import FogoExtractor
from pipelines.silver.src.streaming_processing.processors.calculators import FogoCalculators
from config.domain.models import FocoFatoPayload

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

        # 3. Motor Espacial (apenas localização e distâncias brutas)
        if coord_valida:
            analise = self.motor.analisar_todas_ameacas(lat, lon)
        else:
            analise = {}

        # 4. Payload Assembly com validação Pydantic (Dado Observacional Puro)
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
            fk_hospital_proximo=analise.get("codigo_cnes_prox", NOT_INFORMED),

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

            distancia_rodovia_km=analise.get('distancia_rodovia_km'),
            distancia_linha_km=analise.get('distancia_linha_km'),
            distancia_subestacao_km=analise.get('distancia_subestacao_km'),
            distancia_sistema_isolado_km=analise.get('distancia_sistema_isolado_km'),
            distancia_hospital_km=analise.get('distancia_hospital_km'),
            distancia_terra_indigena_km=analise.get('distancia_terra_indigena_km'),
        )

        return payload_obj.model_dump(mode='json')

