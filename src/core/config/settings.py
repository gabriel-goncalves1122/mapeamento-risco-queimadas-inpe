"""
Configuração centralizada e injetável do ecossistema CCO DataOps.

Encapsula variáveis de ambiente e caminhos das camadas Medalhão num objeto
imutável (`PipelineSettings`), permitindo Injeção de Dependência (DIP) em
testes e mantendo atributos de módulo para compatibilidade com scripts CLI.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping

from src.core.config import constants


def _parse_optional_int(raw_value: str) -> int | None:
    """Converte variável de ambiente opcional em inteiro; string vazia vira None."""
    limpo = raw_value.strip()
    return int(limpo) if limpo else None


@dataclass(frozen=True)
class PipelineSettings:
    """
    Contrato imutável de configuração operacional das pipelines Bronze, Silver e Gold.

    Pode ser instanciado via `PipelineSettings.from_env()` para produção ou
    construído diretamente com caminhos temporários (`tmp_path`) em testes.
    """

    # Diretórios base das camadas Medalhão
    base_dir: str = str(constants.PROJECT_ROOT)
    bronze_dir: str = str(constants.BRONZE_DIR)
    silver_dir: str = str(constants.SILVER_DIR)
    gold_dir: str = str(constants.GOLD_DIR)
    inpe_dir: str = str(constants.INPE_DIR)
    ibge_dir: str = str(constants.IBGE_DIR)
    dim_dir: str = str(constants.DIMENSIONS_DIR)

    # Ingestão de focos brutos do INPE
    raw_focos: str = os.path.join(str(constants.INPE_DIR), "focos_incendio_brutos.csv")
    csv_encoding: str = "utf-8"
    chunk_size_focos: int = 10000
    limite_linhas_teste: int | None = None

    # Caminhos dos CSVs de dimensões processadas na Silver
    dim_funai: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_terras_indigenas.csv")
    dim_municipios_coord: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_municipios_coordenadas.csv")
    dim_rodovias: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_rodovias_federais.csv")
    dim_linhas_ons: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_ons_linhas_transmissao.csv")
    dim_subestacoes: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_ons_subestacoes.csv")
    dim_sistemas_iso: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_ons_sistemas_isolados.csv")
    dim_hospitais: str = os.path.join(str(constants.DIMENSIONS_DIR), "dim_hospitais_cnes.csv")

    # Projeções e faixas de distância (EPSG:4326 p/ Deck.gl e EPSG:5880 métrico p/ distâncias no Brasil)
    epsg_gps: int = constants.EPSG_GPS
    epsg_metrico: int = constants.EPSG_METRICO
    limites_distancia_km: list[int] = field(default_factory=lambda: list(constants.DISTANCE_LIMITS_KM))

    # Mensageria Apache Kafka
    kafka_broker: str = constants.DEFAULT_KAFKA_BROKER
    topico_kafka: str = constants.DEFAULT_KAFKA_TOPIC_FOCOS
    topico_kafka_eventos: str = constants.DEFAULT_KAFKA_TOPIC_EVENTOS
    kafka_client_id: str = constants.DEFAULT_KAFKA_CLIENT_ID
    kafka_client_id_eventos: str = constants.DEFAULT_KAFKA_CLIENT_ID_EVENTOS
    kafka_linger_ms: int = 20
    kafka_batch_size: int = 65536
    kafka_compression: str = "gzip"

    # Hiperparâmetros do ST-DBSCAN (janelas operacionais curtas para eventos fechados no Druid)
    eventos_eps_km: float = 5.0
    eventos_eps_dias: float = 2.0
    eventos_min_samples: int = 3
    eventos_max_duration_days: float = 7.0
    eventos_area_buffer_km: float = 0.5

    # Apache Druid OLAP
    druid_datasource_fato: str = constants.DEFAULT_DRUID_DATASOURCE_FATO
    druid_datasource_eventos: str = constants.DEFAULT_DRUID_DATASOURCE_EVENTOS
    druid_supervisor_url: str = constants.DEFAULT_DRUID_SUPERVISOR_URL
    kafka_broker_druid: str = constants.DEFAULT_KAFKA_BROKER_DRUID

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> PipelineSettings:
        """Constrói a configuração lendo overrides do ambiente (`os.environ` por padrão)."""
        source = env if env is not None else os.environ
        inpe_dir = str(constants.INPE_DIR)
        dim_dir = str(constants.DIMENSIONS_DIR)

        return cls(
            raw_focos=source.get("RAW_FOCOS", os.path.join(inpe_dir, "focos_incendio_brutos.csv")),
            csv_encoding=source.get("CSV_ENCODING", "utf-8"),
            chunk_size_focos=int(source.get("CHUNK_SIZE_FOCOS", "10000")),
            limite_linhas_teste=_parse_optional_int(source.get("LIMITE_LINHAS_TESTE", "")),
            dim_funai=os.path.join(dim_dir, "dim_terras_indigenas.csv"),
            dim_municipios_coord=os.path.join(dim_dir, "dim_municipios_coordenadas.csv"),
            dim_rodovias=os.path.join(dim_dir, "dim_rodovias_federais.csv"),
            dim_linhas_ons=os.path.join(dim_dir, "dim_ons_linhas_transmissao.csv"),
            dim_subestacoes=os.path.join(dim_dir, "dim_ons_subestacoes.csv"),
            dim_sistemas_iso=os.path.join(dim_dir, "dim_ons_sistemas_isolados.csv"),
            dim_hospitais=os.path.join(dim_dir, "dim_hospitais_cnes.csv"),
            kafka_broker=source.get("KAFKA_BROKER", constants.DEFAULT_KAFKA_BROKER),
            topico_kafka=source.get("TOPICO_KAFKA", constants.DEFAULT_KAFKA_TOPIC_FOCOS),
            topico_kafka_eventos=source.get("TOPICO_KAFKA_EVENTOS", constants.DEFAULT_KAFKA_TOPIC_EVENTOS),
            kafka_client_id=source.get("KAFKA_CLIENT_ID", constants.DEFAULT_KAFKA_CLIENT_ID),
            kafka_client_id_eventos=source.get("KAFKA_CLIENT_ID_EVENTOS", constants.DEFAULT_KAFKA_CLIENT_ID_EVENTOS),
            kafka_linger_ms=int(source.get("KAFKA_LINGER_MS", "20")),
            kafka_batch_size=int(source.get("KAFKA_BATCH_SIZE", "65536")),
            kafka_compression=source.get("KAFKA_COMPRESSION", "gzip"),
            eventos_eps_km=float(source.get("EVENTOS_EPS_KM", "5.0")),
            eventos_eps_dias=float(source.get("EVENTOS_EPS_DIAS", "2.0")),
            eventos_min_samples=int(source.get("EVENTOS_MIN_SAMPLES", "3")),
            eventos_max_duration_days=float(source.get("EVENTOS_MAX_DURATION_DAYS", "7.0")),
            eventos_area_buffer_km=float(source.get("EVENTOS_AREA_BUFFER_KM", "0.5")),
            druid_datasource_fato=source.get("DRUID_DATASOURCE_FATO", constants.DEFAULT_DRUID_DATASOURCE_FATO),
            druid_datasource_eventos=source.get("DRUID_DATASOURCE_EVENTOS", constants.DEFAULT_DRUID_DATASOURCE_EVENTOS),
            druid_supervisor_url=source.get("DRUID_SUPERVISOR_URL", constants.DEFAULT_DRUID_SUPERVISOR_URL),
            kafka_broker_druid=source.get("KAFKA_BROKER_DRUID", constants.DEFAULT_KAFKA_BROKER_DRUID),
        )

    def arquivos_obrigatorios(self) -> dict[str, str]:
        """Mapeia os arquivos de entrada/dimensão exigidos antes da carga de streaming."""
        return {
            "RAW_FOCOS": self.raw_focos,
            "DIM_FUNAI": self.dim_funai,
            "DIM_MUNICIPIOS_COORD": self.dim_municipios_coord,
            "DIM_RODOVIAS": self.dim_rodovias,
            "DIM_LINHAS_ONS": self.dim_linhas_ons,
            "DIM_SUBESTACOES": self.dim_subestacoes,
            "DIM_SISTEMAS_ISO": self.dim_sistemas_iso,
            "DIM_HOSPITAIS": self.dim_hospitais,
        }

    def verificar_arquivos_obrigatorios(self) -> bool:
        """Valida a presença física dos CSVs de dimensão e focos antes de iniciar o produtor."""
        faltando = [
            (nome, caminho)
            for nome, caminho in self.arquivos_obrigatorios().items()
            if not os.path.exists(caminho)
        ]

        if faltando:
            print("⚠️ Arquivos obrigatórios não encontrados:")
            for nome, caminho in faltando:
                print(f" - {nome}: {caminho}")
            return False

        print("✅ Todos os arquivos obrigatórios foram encontrados.")
        return True


# Instância padrão inicializada a partir do ambiente para uso direto e retrocompatibilidade
DEFAULT_SETTINGS = PipelineSettings.from_env()

BASE_DIR = DEFAULT_SETTINGS.base_dir
BRONZE_DIR = DEFAULT_SETTINGS.bronze_dir
SILVER_DIR = DEFAULT_SETTINGS.silver_dir
GOLD_DIR = DEFAULT_SETTINGS.gold_dir
INPE_DIR = DEFAULT_SETTINGS.inpe_dir
IBGE_DIR = DEFAULT_SETTINGS.ibge_dir
DIM_DIR = DEFAULT_SETTINGS.dim_dir

RAW_FOCOS = DEFAULT_SETTINGS.raw_focos
CSV_ENCODING = DEFAULT_SETTINGS.csv_encoding
CHUNK_SIZE_FOCOS = DEFAULT_SETTINGS.chunk_size_focos
LIMITE_LINHAS_TESTE = DEFAULT_SETTINGS.limite_linhas_teste

DIM_FUNAI = DEFAULT_SETTINGS.dim_funai
DIM_MUNICIPIOS_COORD = DEFAULT_SETTINGS.dim_municipios_coord
DIM_RODOVIAS = DEFAULT_SETTINGS.dim_rodovias
DIM_LINHAS_ONS = DEFAULT_SETTINGS.dim_linhas_ons
DIM_SUBESTACOES = DEFAULT_SETTINGS.dim_subestacoes
DIM_SISTEMAS_ISO = DEFAULT_SETTINGS.dim_sistemas_iso
DIM_HOSPITAIS = DEFAULT_SETTINGS.dim_hospitais

EPSG_GPS = DEFAULT_SETTINGS.epsg_gps
EPSG_METRICO = DEFAULT_SETTINGS.epsg_metrico
LIMITES_DISTANCIA_KM = DEFAULT_SETTINGS.limites_distancia_km

KAFKA_BROKER = DEFAULT_SETTINGS.kafka_broker
TOPICO_KAFKA = DEFAULT_SETTINGS.topico_kafka
TOPICO_KAFKA_EVENTOS = DEFAULT_SETTINGS.topico_kafka_eventos
KAFKA_CLIENT_ID = DEFAULT_SETTINGS.kafka_client_id
KAFKA_CLIENT_ID_EVENTOS = DEFAULT_SETTINGS.kafka_client_id_eventos
KAFKA_LINGER_MS = DEFAULT_SETTINGS.kafka_linger_ms
KAFKA_BATCH_SIZE = DEFAULT_SETTINGS.kafka_batch_size
KAFKA_COMPRESSION = DEFAULT_SETTINGS.kafka_compression

EVENTOS_EPS_KM = DEFAULT_SETTINGS.eventos_eps_km
EVENTOS_EPS_DIAS = DEFAULT_SETTINGS.eventos_eps_dias
EVENTOS_MIN_SAMPLES = DEFAULT_SETTINGS.eventos_min_samples
EVENTOS_MAX_DURATION_DAYS = DEFAULT_SETTINGS.eventos_max_duration_days
EVENTOS_AREA_BUFFER_KM = DEFAULT_SETTINGS.eventos_area_buffer_km

DRUID_DATASOURCE_FATO = DEFAULT_SETTINGS.druid_datasource_fato
DRUID_DATASOURCE_EVENTOS = DEFAULT_SETTINGS.druid_datasource_eventos
DRUID_SUPERVISOR_URL = DEFAULT_SETTINGS.druid_supervisor_url
KAFKA_BROKER_DRUID = DEFAULT_SETTINGS.kafka_broker_druid


def verificar_arquivos_obrigatorios() -> bool:
    """Verifica a existência dos arquivos essenciais delegando para a configuração ativa."""
    custom_settings = PipelineSettings(
        raw_focos=RAW_FOCOS,
        dim_funai=DIM_FUNAI,
        dim_municipios_coord=DIM_MUNICIPIOS_COORD,
        dim_rodovias=DIM_RODOVIAS,
        dim_linhas_ons=DIM_LINHAS_ONS,
        dim_subestacoes=DIM_SUBESTACOES,
        dim_sistemas_iso=DIM_SISTEMAS_ISO,
        dim_hospitais=DIM_HOSPITAIS,
    )
    return custom_settings.verificar_arquivos_obrigatorios()
