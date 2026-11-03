"""
Processador enriquecedor de focos de incêndio (`ProcessadorFocos`).

Orquestra extração, cálculo de índices contínuos e cruzamento espacial via
Injeção de Dependência (`SpatialEngineProtocol`, `FogoExtractor`, `FogoCalculators`),
emitindo payloads validados pelo contrato Pydantic Snowflake (`FocoFatoPayload`).
"""
from __future__ import annotations

import warnings
from typing import Any, Callable, Mapping

warnings.filterwarnings("ignore", category=RuntimeWarning, module="shapely")

from src.core.config.constants import NOT_INFORMED
from src.core.contracts.contracts import SpatialEngineProtocol
from src.core.domain.foco_fato_payload import FocoFatoPayload
from src.silver.streaming_processing.processors.calculators import FogoCalculators
from src.silver.streaming_processing.processors.extractor import FogoExtractor
from src.silver.utils.cleaners import DruidTextCleaner


class ProcessadorFocos:
    """
    Transforma um registro bruto do satélite INPE num dicionário JSON-safe
    aderente à tabela fato `FATO_FOCOS_INCENDIO` (apenas FKs e métricas).

    Recebe `motor_espacial`, `extractor`, `calculators` e `text_cleaner` via
    construtor para permitir substituição e testes isolados (DIP).
    """

    def __init__(
        self,
        motor_espacial: SpatialEngineProtocol | Any,
        extractor: FogoExtractor | type[FogoExtractor] = FogoExtractor,
        calculators: FogoCalculators | type[FogoCalculators] = FogoCalculators,
        text_cleaner: Callable[[Any], str] = DruidTextCleaner.limpar_texto_druid,
    ) -> None:
        self.motor = motor_espacial
        self.extractor = extractor
        self.calculators = calculators
        self.text_cleaner = text_cleaner

    def transformar(self, linha_bruta: Mapping[str, Any]) -> dict[str, Any]:
        """Executa limpeza, enriquecimento espacial e validação Pydantic do foco."""
        datas = self.extractor.extrair_data(linha_bruta.get("DataHora"))

        estado_norm = self.text_cleaner(linha_bruta.get("Estado"))
        municipio_norm = self.text_cleaner(linha_bruta.get("Municipio"))
        bioma_norm = self.text_cleaner(linha_bruta.get("Bioma"))
        satelite_norm = self.text_cleaner(linha_bruta.get("Satelite"))

        fk_municipio_origem = f"{estado_norm}_{municipio_norm}"

        lat, lon, coord_valida = self.extractor.extrair_coordenadas(linha_bruta)
        foco_point = self.extractor.foco_point(lat, lon, coord_valida)

        dias_sem_chuva = self.extractor.limpar_valor_numerico_nullable(linha_bruta.get("DiaSemChuva"))
        precipitacao_mm = self.extractor.limpar_valor_numerico_nullable(linha_bruta.get("Precipitacao"))
        risco_fogo_inpe = self.extractor.limpar_valor_numerico_nullable(linha_bruta.get("RiscoFogo"))
        frp = self.extractor.limpar_valor_numerico_nullable(linha_bruta.get("FRP"))

        indice_condicao_ambiental = self.calculators.indice_condicao_ambiental(
            risco_fogo_inpe, dias_sem_chuva, precipitacao_mm
        )
        indice_queimada_evento = self.calculators.indice_queimada_evento(
            frp, risco_fogo_inpe, dias_sem_chuva, precipitacao_mm
        )

        # Só aciona o índice espacial R-Tree quando a coordenada é geograficamente válida
        analise = self.motor.analisar_todas_ameacas(lat, lon) if coord_valida else {}

        payload_obj = FocoFatoPayload(
            data_hora=datas["data_hora"],
            pais_origem=self.text_cleaner(linha_bruta.get("Pais")),
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
            distancia_rodovia_km=analise.get("distancia_rodovia_km"),
            distancia_linha_km=analise.get("distancia_linha_km"),
            distancia_subestacao_km=analise.get("distancia_subestacao_km"),
            distancia_sistema_isolado_km=analise.get("distancia_sistema_isolado_km"),
            distancia_hospital_km=analise.get("distancia_hospital_km"),
            distancia_terra_indigena_km=analise.get("distancia_terra_indigena_km"),
        )

        return payload_obj.model_dump(mode="json")
