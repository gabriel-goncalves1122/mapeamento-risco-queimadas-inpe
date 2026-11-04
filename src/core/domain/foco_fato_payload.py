"""
Contrato Pydantic da Tabela Fato de Focos de Incêndio (`FocoFatoPayload`).

Representa o dado observacional atômico do satélite (sem strings descritivas
redundantes, respeitando a modelagem Snowflake exigida pelo Apache Druid).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FocoFatoPayload(BaseModel):
    """
    Representação tipada da Tabela Fato `FATO_FOCOS_INCENDIO`.

    Contém apenas chaves temporais, chaves estrangeiras (FKs) para as dimensões
    Silver, coordenadas do sensor e métricas quantitativas de clima, fogo e
    distância até infraestruturas críticas.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # 1. Chave Temporal (__time no Apache Druid)
    data_hora: str = Field(..., description="Timestamp ISO (__time no Druid)")

    # 2. Dimensões Degeneradas / FKs Diretas
    pais_origem: str
    fk_bioma: str
    fk_satelite_sensor: str

    # 3. Chaves Estrangeiras de Localização e Infraestrutura (Snowflake)
    fk_municipio: str
    fk_municipio_espacial: str
    fk_terra_indigena: str
    fk_terra_indigena_proxima: str
    fk_trecho_rodoviario: str
    fk_linha_transmissao: str
    fk_subestacao: str
    fk_sistema_isolado: str
    fk_hospital_proximo: str

    # 4. Coordenadas Geográficas WGS84
    latitude: Optional[float]
    longitude: Optional[float]
    coordenada_valida: int
    foco_point: str

    # 5. Métricas Quantitativas (Clima e Intensidade Térmica)
    dias_sem_chuva: Optional[float]
    precipitacao_mm: Optional[float]
    risco_fogo_inpe: Optional[float]
    potencia_radiativa_fogo: Optional[float]
    indice_condicao_ambiental: Optional[float]
    indice_queimada_evento: Optional[float]

    # 6. Métricas Quantitativas Espaciais (Distâncias Euclidianas em km - EPSG:5880)
    distancia_rodovia_km: Optional[float]
    distancia_linha_km: Optional[float]
    distancia_subestacao_km: Optional[float]
    distancia_sistema_isolado_km: Optional[float]
    distancia_hospital_km: Optional[float]
    distancia_terra_indigena_km: Optional[float]
