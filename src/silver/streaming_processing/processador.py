"""
Processador enriquecedor de focos de incêndio (`ProcessadorFocos`).

Orquestra a extração, o cálculo de índices contínuos e o cruzamento espacial via
Injeção de Dependência (`SpatialEngineProtocol`), emitindo payloads validados pelo
contrato Pydantic Snowflake (`FocoFatoPayload`) no padrão Functional Core.
"""
from __future__ import annotations

import warnings
from typing import Any, Callable, Mapping

warnings.filterwarnings("ignore", category=RuntimeWarning, module="shapely")

from src.core.config.constants import NOT_INFORMED
from src.core.contracts.contracts import SpatialEngineProtocol
from src.core.domain.foco_fato_payload import FocoFatoPayload
from src.silver.streaming_processing.processors.calculators import (
    indice_condicao_ambiental as calc_indice_condicao_ambiental,
    indice_queimada_evento as calc_indice_queimada_evento,
)
from src.silver.streaming_processing.processors.extractor import (
    extrair_coordenadas as ext_extrair_coordenadas,
    extrair_data as ext_extrair_data,
    foco_point as ext_foco_point,
    limpar_valor_numerico_nullable as ext_limpar_valor_numerico_nullable,
)
from src.silver.utils.cleaners import limpar_texto_druid


def transformar_foco(
    linha_bruta: Mapping[str, Any],
    motor_espacial: SpatialEngineProtocol | Any,
    text_cleaner: Callable[[Any], str] = limpar_texto_druid,
    fn_extrair_data: Callable[[Any], dict[str, Any]] = ext_extrair_data,
    fn_extrair_coordenadas: Callable[[Mapping[str, Any]], tuple[float | None, float | None, int]] = ext_extrair_coordenadas,
    fn_foco_point: Callable[[float | None, float | None, int | bool], str] = ext_foco_point,
    fn_limpar_num_nullable: Callable[[Any], float | None] = ext_limpar_valor_numerico_nullable,
    fn_condicao_ambiental: Callable[[float | None, float | None, float | None], float] = calc_indice_condicao_ambiental,
    fn_queimada_evento: Callable[[float | None, float | None, float | None, float | None], float] = calc_indice_queimada_evento,
) -> dict[str, Any]:
    """
    Função pura (Functional Core) de transformação e validação de um foco bruto do satélite INPE.

    Gera payload JSON-safe aderente à tabela fato `FATO_FOCOS_INCENDIO` (apenas FKs e métricas).
    """
    datas = fn_extrair_data(linha_bruta.get("DataHora"))

    estado_norm = text_cleaner(linha_bruta.get("Estado"))
    municipio_norm = text_cleaner(linha_bruta.get("Municipio"))
    bioma_norm = text_cleaner(linha_bruta.get("Bioma"))
    satelite_norm = text_cleaner(linha_bruta.get("Satelite"))

    fk_municipio_origem = f"{estado_norm}_{municipio_norm}"

    lat, lon, coord_valida = fn_extrair_coordenadas(linha_bruta)
    ponto_compacto = fn_foco_point(lat, lon, coord_valida)

    dias_sem_chuva = fn_limpar_num_nullable(linha_bruta.get("DiaSemChuva"))
    precipitacao_mm = fn_limpar_num_nullable(linha_bruta.get("Precipitacao"))
    risco_fogo_inpe = fn_limpar_num_nullable(linha_bruta.get("RiscoFogo"))
    frp = fn_limpar_num_nullable(linha_bruta.get("FRP"))

    ind_ambiental = fn_condicao_ambiental(risco_fogo_inpe, dias_sem_chuva, precipitacao_mm)
    ind_evento = fn_queimada_evento(frp, risco_fogo_inpe, dias_sem_chuva, precipitacao_mm)

    # Só aciona o índice espacial R-Tree quando a coordenada é geograficamente válida
    analise: dict[str, Any] = {}
    if coord_valida and motor_espacial is not None and hasattr(motor_espacial, "analisar_todas_ameacas"):
        analise = motor_espacial.analisar_todas_ameacas(lat, lon) or {}

    payload_obj = FocoFatoPayload(
        data_hora=datas["data_hora"],
        pais_origem=text_cleaner(linha_bruta.get("Pais")),
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
        foco_point=ponto_compacto,
        dias_sem_chuva=dias_sem_chuva,
        precipitacao_mm=precipitacao_mm,
        risco_fogo_inpe=risco_fogo_inpe,
        potencia_radiativa_fogo=frp,
        indice_condicao_ambiental=ind_ambiental,
        indice_queimada_evento=ind_evento,
        distancia_rodovia_km=analise.get("distancia_rodovia_km"),
        distancia_linha_km=analise.get("distancia_linha_km"),
        distancia_subestacao_km=analise.get("distancia_subestacao_km"),
        distancia_sistema_isolado_km=analise.get("distancia_sistema_isolado_km"),
        distancia_hospital_km=analise.get("distancia_hospital_km"),
        distancia_terra_indigena_km=analise.get("distancia_terra_indigena_km"),
    )

    return payload_obj.model_dump(mode="json")


class ProcessadorFocos:
    """
    Adaptador orientado a objetos para pipelines que injetam dependências de infraestrutura.

    Encapsula o `motor_espacial` e delega a transformação à função pura `transformar_foco`.
    """

    def __init__(
        self,
        motor_espacial: SpatialEngineProtocol | Any,
        text_cleaner: Callable[[Any], str] = limpar_texto_druid,
        fn_extrair_data: Callable[[Any], dict[str, Any]] = ext_extrair_data,
        fn_extrair_coordenadas: Callable[[Mapping[str, Any]], tuple[float | None, float | None, int]] = ext_extrair_coordenadas,
        fn_foco_point: Callable[[float | None, float | None, int | bool], str] = ext_foco_point,
        fn_limpar_num_nullable: Callable[[Any], float | None] = ext_limpar_valor_numerico_nullable,
        fn_condicao_ambiental: Callable[[float | None, float | None, float | None], float] = calc_indice_condicao_ambiental,
        fn_queimada_evento: Callable[[float | None, float | None, float | None, float | None], float] = calc_indice_queimada_evento,
    ) -> None:
        self.motor = motor_espacial
        self.text_cleaner = text_cleaner
        self.fn_extrair_data = fn_extrair_data
        self.fn_extrair_coordenadas = fn_extrair_coordenadas
        self.fn_foco_point = fn_foco_point
        self.fn_limpar_num_nullable = fn_limpar_num_nullable
        self.fn_condicao_ambiental = fn_condicao_ambiental
        self.fn_queimada_evento = fn_queimada_evento

    def transformar(self, linha_bruta: Mapping[str, Any]) -> dict[str, Any]:
        """Delega a transformação à função pura `transformar_foco`."""
        return transformar_foco(
            linha_bruta=linha_bruta,
            motor_espacial=self.motor,
            text_cleaner=self.text_cleaner,
            fn_extrair_data=self.fn_extrair_data,
            fn_extrair_coordenadas=self.fn_extrair_coordenadas,
            fn_foco_point=self.fn_foco_point,
            fn_limpar_num_nullable=self.fn_limpar_num_nullable,
            fn_condicao_ambiental=self.fn_condicao_ambiental,
            fn_queimada_evento=self.fn_queimada_evento,
        )

    def __call__(self, linha_bruta: Mapping[str, Any]) -> dict[str, Any]:
        return self.transformar(linha_bruta)
