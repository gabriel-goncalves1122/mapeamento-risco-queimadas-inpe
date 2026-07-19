"""
=========================================================
MÓDULO: settings.py
---------------------------------------------------------
Função Geral: Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica.
=========================================================
"""
import os
from src.config import constants

# ==========================================
# 1. Caminhos base do sistema
# ==========================================
BASE_DIR = str(constants.PROJECT_ROOT)

DATA_DIR = str(constants.DATA_DIR)

RAW_DIR = str(constants.RAW_DIR)
GEO_DIR = str(constants.GEO_DIR)
PROCESSED_DIR = str(constants.PROCESSED_DIR)
DIM_DIR = str(constants.DIMENSIONS_DIR)

# ==========================================
# 2. Entrada da tabela fato
# ==========================================
RAW_FOCOS = os.getenv(
    'RAW_FOCOS',
    os.path.join(RAW_DIR, 'focos_incendio_brutos.csv')
)

# Encoding do CSV bruto do INPE
CSV_ENCODING = os.getenv('CSV_ENCODING', 'utf-8')

# Tamanho dos blocos de leitura
CHUNK_SIZE_FOCOS = int(os.getenv('CHUNK_SIZE_FOCOS', '10000'))

# Use para testes rápidos.
# Exemplo:
# export LIMITE_LINHAS_TESTE=50000
# Para produção, deixe vazio.
_limite_teste = os.getenv('LIMITE_LINHAS_TESTE', '').strip()
LIMITE_LINHAS_TESTE = int(_limite_teste) if _limite_teste else None

# ==========================================
# 3. Dimensões processadas
# ==========================================
DIM_FUNAI = os.path.join(DIM_DIR, 'dim_terras_indigenas.csv')
DIM_MUNICIPIOS_COORD = os.path.join(DIM_DIR, 'dim_municipios_coordenadas.csv')

DIM_RODOVIAS = os.path.join(DIM_DIR, 'dim_rodovias_federais.csv')
DIM_LINHAS_ONS = os.path.join(DIM_DIR, 'dim_ons_linhas_transmissao.csv')
DIM_SUBESTACOES = os.path.join(DIM_DIR, 'dim_ons_subestacoes.csv')
DIM_SISTEMAS_ISO = os.path.join(DIM_DIR, 'dim_ons_sistemas_isolados.csv')
DIM_HOSPITAIS = os.path.join(DIM_DIR, 'dim_hospitais_cnes.csv')

# ==========================================
# 4. Configuração espacial
# ==========================================
# EPSG geográfico padrão GPS
EPSG_GPS = constants.EPSG_GPS

# EPSG métrico usado para cálculo de distâncias no Brasil
EPSG_METRICO = constants.EPSG_METRICO

# Limites de distância usados para gerar flags:
# rodovia_ate_1km, linha_ate_7km, hospital_ate_15km etc.
LIMITES_DISTANCIA_KM = list(constants.DISTANCE_LIMITS_KM)

# ==========================================
# 5. Kafka
# ==========================================
KAFKA_BROKER = os.getenv('KAFKA_BROKER', constants.DEFAULT_KAFKA_BROKER)

TOPICO_KAFKA = os.getenv(
    'TOPICO_KAFKA',
    constants.DEFAULT_KAFKA_TOPIC_FOCOS
)

TOPICO_KAFKA_EVENTOS = os.getenv(
    'TOPICO_KAFKA_EVENTOS',
    constants.DEFAULT_KAFKA_TOPIC_EVENTOS
)

KAFKA_CLIENT_ID = os.getenv(
    'KAFKA_CLIENT_ID',
    constants.DEFAULT_KAFKA_CLIENT_ID
)

KAFKA_CLIENT_ID_EVENTOS = os.getenv(
    'KAFKA_CLIENT_ID_EVENTOS',
    constants.DEFAULT_KAFKA_CLIENT_ID_EVENTOS
)

KAFKA_LINGER_MS = int(os.getenv('KAFKA_LINGER_MS', '20'))
KAFKA_BATCH_SIZE = int(os.getenv('KAFKA_BATCH_SIZE', '65536'))
KAFKA_COMPRESSION = os.getenv('KAFKA_COMPRESSION', 'gzip')

# Parametros da eventizacao operacional curta. O Druid ingere eventos fechados,
# entao a janela limita encadeamentos longos antes do envio ao Kafka.
EVENTOS_EPS_KM = float(os.getenv('EVENTOS_EPS_KM', '5.0'))
EVENTOS_EPS_DIAS = float(os.getenv('EVENTOS_EPS_DIAS', '2.0'))
EVENTOS_MIN_SAMPLES = int(os.getenv('EVENTOS_MIN_SAMPLES', '3'))
EVENTOS_MAX_DURATION_DAYS = float(os.getenv('EVENTOS_MAX_DURATION_DAYS', '7.0'))
EVENTOS_AREA_BUFFER_KM = float(os.getenv('EVENTOS_AREA_BUFFER_KM', '0.5'))

# ==========================================
# 6. Apache Druid
# ==========================================
DRUID_DATASOURCE_FATO = os.getenv(
    'DRUID_DATASOURCE_FATO',
    constants.DEFAULT_DRUID_DATASOURCE_FATO
)

DRUID_DATASOURCE_EVENTOS = os.getenv(
    'DRUID_DATASOURCE_EVENTOS',
    constants.DEFAULT_DRUID_DATASOURCE_EVENTOS
)

DRUID_SUPERVISOR_URL = os.getenv(
    'DRUID_SUPERVISOR_URL',
    constants.DEFAULT_DRUID_SUPERVISOR_URL
)

# Dentro do Docker, o Druid acessa Kafka por kafka:9092.
# Fora do Docker, o produtor Python acessa por localhost:29092.
KAFKA_BROKER_DRUID = os.getenv(
    'KAFKA_BROKER_DRUID',
    constants.DEFAULT_KAFKA_BROKER_DRUID
)

# ==========================================
# 7. Validação simples de caminhos
# ==========================================
def verificar_arquivos_obrigatorios():
    """
    Verifica se os arquivos essenciais existem antes de rodar o pipeline.
    Útil para evitar erro no meio da ingestão.
    """
    arquivos = {
        'RAW_FOCOS': RAW_FOCOS,
        'DIM_FUNAI': DIM_FUNAI,
        'DIM_MUNICIPIOS_COORD': DIM_MUNICIPIOS_COORD,
        'DIM_RODOVIAS': DIM_RODOVIAS,
        'DIM_LINHAS_ONS': DIM_LINHAS_ONS,
        'DIM_SUBESTACOES': DIM_SUBESTACOES,
        'DIM_SISTEMAS_ISO': DIM_SISTEMAS_ISO,
        'DIM_HOSPITAIS': DIM_HOSPITAIS,
    }

    faltando = []

    for nome, caminho in arquivos.items():
        if not os.path.exists(caminho):
            faltando.append((nome, caminho))

    if faltando:
        print("⚠️ Arquivos obrigatórios não encontrados:")
        for nome, caminho in faltando:
            print(f" - {nome}: {caminho}")

        return False

    print("✅ Todos os arquivos obrigatórios foram encontrados.")
    return True
