"""
Contratos compartilhados do projeto CCO DataOps.

Este módulo concentra valores usados por múltiplas camadas para evitar
divergências silenciosas entre ETL, streaming, motor espacial e specs.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
GEO_DIR = DATA_DIR / "geo"
PROCESSED_DIR = DATA_DIR / "processed"
DIMENSIONS_DIR = PROCESSED_DIR / "dimensions"
FACTS_DIR = PROCESSED_DIR / "fatos"

NOT_INFORMED = "NAO INFORMADO"
UNKNOWN_UF = "NI"
DEFAULT_EPOCH = "1970-01-01 00:00:00"

EPSG_GPS = 4326
EPSG_METRICO = 5880
DISTANCE_LIMITS_KM = (1, 3, 7, 15, 50)

BRAZIL_LAT_MIN = -35.0
BRAZIL_LAT_MAX = 6.0
BRAZIL_LON_MIN = -75.0
BRAZIL_LON_MAX = -30.0

GEOMETRY_WKT_COLUMN = "geometria_wkt"
PATH_JSON_COLUMN = "path_json"

DEFAULT_KAFKA_BROKER = "localhost:29092"
DEFAULT_KAFKA_BROKER_DRUID = "kafka:9092"
DEFAULT_KAFKA_TOPIC_FOCOS = "streaming_focos_incendio"
DEFAULT_KAFKA_TOPIC_EVENTOS = "streaming_eventos_incendio"
DEFAULT_KAFKA_CLIENT_ID = "produtor_focos_incendio"
DEFAULT_KAFKA_CLIENT_ID_EVENTOS = "produtor_eventos_incendio"

DEFAULT_DRUID_DATASOURCE_FATO = "fato_focos_incendio"
DEFAULT_DRUID_DATASOURCE_EVENTOS = "fato_eventos_incendio"
DEFAULT_DRUID_SUPERVISOR_URL = "http://localhost:8090/druid/indexer/v1/supervisor"
