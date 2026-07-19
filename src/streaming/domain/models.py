"""
=========================================================
MÓDULO: models.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import math
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

class FocoFatoPayload(BaseModel):
    """
    Representação tipada da Tabela Fato: FATO_FOCOS_INCENDIO.
    Adota o esquema Snowflake: apenas chaves de tempo, foreign keys e métricas numéricas.
    Valores textuais redundantes e classificações nominais foram removidos e devem
    ser resolvidos via JOINs (Lookups) no Druid/Superset.
    """

    model_config = ConfigDict(extra="forbid")

    # 1. Chaves Temporais (Partition Keys)
    data_hora: str = Field(..., description="Timestamp ISO (__time no Druid)")

    # 2. Dimensões Degeneradas (Ou FKs diretas textuais)
    pais_origem: str
    fk_bioma: str
    fk_satelite_sensor: str
    
    # 3. Chaves Estrangeiras (Relacionamentos)
    fk_municipio: str
    fk_municipio_espacial: str
    fk_terra_indigena: str
    fk_terra_indigena_proxima: str
    fk_trecho_rodoviario: str
    fk_linha_transmissao: str
    fk_subestacao: str
    fk_sistema_isolado: str
    fk_hospital: str

    # 4. Localização Exata
    latitude: Optional[float]
    longitude: Optional[float]
    coordenada_valida: int
    foco_point: str

    # 5. Métricas Quantitativas (Clima e Fogo)
    dias_sem_chuva: Optional[float]
    precipitacao_mm: Optional[float]
    risco_fogo_inpe: Optional[float]
    potencia_radiativa_fogo: Optional[float]
    indice_condicao_ambiental: Optional[float]
    indice_queimada_evento: Optional[float]

    # 6. Métricas Quantitativas Espaciais (Distâncias em KM)
    distancia_rodovia_km: Optional[float]
    distancia_linha_km: Optional[float]
    distancia_subestacao_km: Optional[float]
    distancia_sistema_isolado_km: Optional[float]
    distancia_hospital_km: Optional[float]
    distancia_terra_indigena_km: Optional[float]

    # 7. Métricas Analíticas (Ameaças)
    indice_ameaca_rodovia: Optional[float]
    indice_ameaca_linha: Optional[float]
    indice_ameaca_subestacao: Optional[float]
    indice_ameaca_sistema_isolado: Optional[float]
    indice_pressao_saude: Optional[float]
    indice_pressao_terra_indigena: Optional[float]
    indice_pressao_maxima: Optional[float]


class EventoFatoPayload(BaseModel):
    """
    Representação tipada da Fato de Eventos de Incêndio.

    O evento já chega agregado ao Kafka: o Druid apenas persiste o JSON.
    Por isso o payload mantém somente chaves, métricas e a geometria técnica
    necessária para desenhar a mancha do evento no Superset.
    """

    model_config = ConfigDict(extra="forbid")

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
    def rejeitar_nan_inf(cls, valor):
        if valor is None:
            return None
        valor_float = float(valor)
        if math.isnan(valor_float) or math.isinf(valor_float):
            raise ValueError("metricas da fato de eventos nao podem ser NaN ou Inf")
        return valor_float
