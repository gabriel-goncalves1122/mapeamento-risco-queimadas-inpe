"""
Contrato Pydantic da Tabela Fato de Eventos de Incêndio (`EventoFatoPayload`).

Representa um evento espaço-temporal consolidado via ST-DBSCAN para persistência
direta no Apache Druid e renderização de polígonos `path_json` no Apache Superset.
"""
from __future__ import annotations

import math
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventoFatoPayload(BaseModel):
    """
    Representação tipada da Tabela Fato `FATO_EVENTOS_INCENDIO`.

    Mantém exclusivamente chaves estrangeiras (Snowflake), métricas agregadas de
    intensidade/ameaça e o polígono técnico `path_json`, bloqueando valores `NaN`
    ou `Inf` que quebrariam o parser JSON do Apache Druid.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    fire_event_id: str
    data_inicio: str = Field(..., description="Timestamp inicial do evento (__time no Druid)")
    data_fim: str

    pais_origem: str
    fk_bioma: str
    fk_satelite_sensor: str

    fk_municipio_principal: str
    codigos_ibge_interceptados: List[str] = Field(default_factory=list)
    qtd_municipios_interceptados: int
    fk_terra_indigena: str
    codigos_ti_interceptadas: List[str] = Field(default_factory=list)
    qtd_terras_indigenas_interceptadas: int
    fk_terra_indigena_proxima: str
    fk_trecho_rodoviario: str
    fk_linha_transmissao: str
    fk_subestacao: str
    fk_sistema_isolado: str
    fk_hospital: str

    latitude_centroide: float
    longitude_centroide: float
    path_json: str

    total_focos: int
    duracao_horas: float
    duracao_dias: float
    area_evento_km2: float

    soma_frp: float
    media_frp: float
    max_frp: float
    media_risco_fogo: float
    max_risco_fogo: float
    media_dias_sem_chuva: float
    media_precipitacao_mm: float
    indice_condicao_ambiental_medio: float
    indice_queimada_evento_medio: float
    indice_queimada_evento_max: float

    distancia_rodovia_km: Optional[float]
    distancia_linha_km: Optional[float]
    distancia_subestacao_km: Optional[float]
    distancia_sistema_isolado_km: Optional[float]
    distancia_hospital_km: Optional[float]
    distancia_terra_indigena_km: Optional[float]

    indice_ameaca_rodovia: float
    indice_ameaca_linha: float
    indice_ameaca_subestacao: float
    indice_ameaca_sistema_isolado: float
    indice_pressao_saude: float
    indice_pressao_terra_indigena: float
    indice_pressao_maxima: float

    param_eps_km: float
    param_eps_dias: float
    param_min_samples: int
    param_max_duration_days: float

    @field_validator(
        "latitude_centroide",
        "longitude_centroide",
        "duracao_horas",
        "duracao_dias",
        "area_evento_km2",
        "soma_frp",
        "media_frp",
        "max_frp",
        "media_risco_fogo",
        "max_risco_fogo",
        "media_dias_sem_chuva",
        "media_precipitacao_mm",
        "indice_condicao_ambiental_medio",
        "indice_queimada_evento_medio",
        "indice_queimada_evento_max",
        "distancia_rodovia_km",
        "distancia_linha_km",
        "distancia_subestacao_km",
        "distancia_sistema_isolado_km",
        "distancia_hospital_km",
        "distancia_terra_indigena_km",
        "indice_ameaca_rodovia",
        "indice_ameaca_linha",
        "indice_ameaca_subestacao",
        "indice_ameaca_sistema_isolado",
        "indice_pressao_saude",
        "indice_pressao_terra_indigena",
        "indice_pressao_maxima",
        "param_eps_km",
        "param_eps_dias",
        "param_max_duration_days",
    )
    @classmethod
    def rejeitar_nan_inf(cls, valor: float | None) -> float | None:
        """Rejeita `NaN` e `Inf` para garantir JSON estrito compatível com Kafka/Druid."""
        if valor is None:
            return None
        valor_float = float(valor)
        if math.isnan(valor_float) or math.isinf(valor_float):
            raise ValueError("metricas da fato de eventos nao podem ser NaN ou Inf")
        return valor_float
