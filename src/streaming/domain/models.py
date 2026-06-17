"""
=========================================================
MÓDULO: models.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
from pydantic import BaseModel, Field
from typing import Optional

class FocoFatoPayload(BaseModel):
    """
    Representação tipada da Tabela Fato: FATO_FOCOS_INCENDIO.
    Adota o esquema Snowflake: apenas chaves de tempo, foreign keys e métricas numéricas.
    Valores textuais redundantes e classificações nominais foram removidos e devem
    ser resolvidos via JOINs (Lookups) no Druid/Superset.
    """
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
