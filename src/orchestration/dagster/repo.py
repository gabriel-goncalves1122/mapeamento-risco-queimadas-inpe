"""
Repositório de Software-Defined Assets (SDA) do Apache Dagster (`repo.py`).

Orquestra as classes de domínio das camadas Bronze, Silver e Gold diretamente
em memória sobre o contrato `ExecutablePipelineStep` (DIP / LSP), eliminando
overhead de subprocessos e registrando telemetria nativa no `AssetExecutionContext`.
"""
import sys
from pathlib import Path
from typing import Any, Optional

_ROOT = str(Path(__file__).resolve().parents[3])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dagster import AssetExecutionContext, Definitions, asset

from src.core.contracts.contracts import ExecutablePipelineStep
from src.bronze.extractors.ingestao_aneel import AneelArcGisExtractor
from src.bronze.extractors.inpe_queimadas_extractor import InpeQueimadasExtractor
from src.gold.science.dbscan.eventizador import EventizadorIncendios
from src.gold.science.networkx.network_builder import SINNetworkCentralityModel
from src.silver.etl.etl_dim_hospitais import ETLDimHospitais
from src.silver.etl.etl_dim_municipios import ETLDimMunicipios
from src.silver.etl.etl_dim_ons_linhas_transmissao import ETLDimLinhasTransmissao
from src.silver.etl.etl_dim_ons_sistemas_isolados import ETLDimSistemasIsolados
from src.silver.etl.etl_dim_ons_subestacoes import ETLDimSubestacoes
from src.silver.etl.etl_dim_rodovias_federais import ETLDimRodoviasFederais
from src.silver.etl.etl_dim_terras_indigenas import ETLDimTerrasIndigenas
from src.silver.lookups.druid_lookup_registrar import DruidLookupRegistrar


def execute_pipeline_step(
    context: Optional[AssetExecutionContext],
    step: ExecutablePipelineStep,
) -> Any:
    """Executa uma etapa `ExecutablePipelineStep` em memória registrando progresso no Dagster."""
    if context is not None:
        context.log.info(f"Executando componente POO: {step.step_name}")
    resultado = step.execute()
    if context is not None:
        total = len(resultado) if hasattr(resultado, "__len__") and resultado is not None else "N/A"
        context.log.info(f"Componente {step.step_name} finalizado (registros/itens: {total}).")
    return resultado


@asset(group_name="dimensions", compute_kind="python")
def dim_municipios(context: AssetExecutionContext) -> Any:
    """Dimensão de Municípios em `path_json` para Druid/Superset."""
    return execute_pipeline_step(context, ETLDimMunicipios())


@asset(group_name="dimensions", compute_kind="python")
def dim_hospitais(context: AssetExecutionContext) -> Any:
    """Dimensão de Hospitais CNES enriquecida espacialmente para Druid/Superset."""
    return execute_pipeline_step(context, ETLDimHospitais())


@asset(group_name="dimensions", compute_kind="python")
def dim_terras_indigenas(context: AssetExecutionContext) -> Any:
    """Dimensão de Terras Indígenas FUNAI com interseção municipal N:M."""
    return execute_pipeline_step(context, ETLDimTerrasIndigenas())


@asset(group_name="dimensions", compute_kind="python")
def dim_rodovias_federais(context: AssetExecutionContext) -> Any:
    """Dimensão de Rodovias Federais DNIT simplificada em `path_json`."""
    return execute_pipeline_step(context, ETLDimRodoviasFederais())


@asset(group_name="bronze_ingestion", compute_kind="python")
def inpe_queimadas_data(context: AssetExecutionContext) -> Any:
    """Extrai focos de calor diários do repositório aberto do INPE/COIDS."""
    return execute_pipeline_step(context, InpeQueimadasExtractor())


@asset(group_name="infra_ons", compute_kind="python")
def aneel_ons_data(context: AssetExecutionContext) -> Any:
    """Extrai malhas de transmissão, subestações e sistemas isolados via ArcGIS REST da ANEEL."""
    return execute_pipeline_step(context, AneelArcGisExtractor())


@asset(deps=[aneel_ons_data], group_name="infra_ons", compute_kind="python")
def dim_linhas_transmissao(context: AssetExecutionContext) -> Any:
    """Processa linhas de transmissão ONS."""
    return execute_pipeline_step(context, ETLDimLinhasTransmissao())


@asset(deps=[aneel_ons_data], group_name="infra_ons", compute_kind="python")
def dim_subestacoes(context: AssetExecutionContext) -> Any:
    """Processa subestações ONS com enriquecimento municipal."""
    return execute_pipeline_step(context, ETLDimSubestacoes())


@asset(deps=[aneel_ons_data], group_name="infra_ons", compute_kind="python")
def dim_sistemas_isolados(context: AssetExecutionContext) -> Any:
    """Processa sistemas isolados ONS na Amazônia Legal."""
    return execute_pipeline_step(context, ETLDimSistemasIsolados())


@asset(deps=[dim_linhas_transmissao, dim_subestacoes], group_name="science_models", compute_kind="networkx")
def network_centrality_model(context: AssetExecutionContext) -> Any:
    """Calcula Betweenness Centrality e Risco em Cascata usando NetworkX."""
    return execute_pipeline_step(context, SINNetworkCentralityModel())


@asset(group_name="science_models", compute_kind="scikit-learn")
def st_dbscan_fire_events(context: AssetExecutionContext) -> Any:
    """Agrupa focos isolados em Eventos Dinâmicos de Incêndio (Convex Hull ST-DBSCAN)."""
    return execute_pipeline_step(context, EventizadorIncendios())


@asset(
    deps=[
        dim_municipios,
        dim_hospitais,
        dim_terras_indigenas,
        dim_linhas_transmissao,
        dim_subestacoes,
        dim_sistemas_isolados,
        dim_rodovias_federais,
    ],
    group_name="druid_sync",
    compute_kind="apache_druid",
)
def druid_lookups(context: AssetExecutionContext) -> Any:
    """Registra mapas de lookups URI em memória no Apache Druid Coordinator."""
    return execute_pipeline_step(context, DruidLookupRegistrar())


def build_druid_lookup_registrar(**kwargs: Any) -> DruidLookupRegistrar:
    """Instancia `DruidLookupRegistrar` para retrocompatibilidade com testes e orquestrações customizadas."""
    return DruidLookupRegistrar(**kwargs)


defs = Definitions(
    assets=[
        inpe_queimadas_data,
        dim_municipios,
        dim_hospitais,
        dim_terras_indigenas,
        aneel_ons_data,
        dim_linhas_transmissao,
        dim_rodovias_federais,
        dim_subestacoes,
        dim_sistemas_isolados,
        network_centrality_model,
        st_dbscan_fire_events,
        druid_lookups,
    ],
)
