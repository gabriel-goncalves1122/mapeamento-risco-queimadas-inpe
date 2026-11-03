"""
Repositório de Software-Defined Assets (SDA) do Apache Dagster (`repo.py`).

Orquestra as classes de domínio das camadas Bronze, Silver e Gold diretamente
em memória sobre o contrato `ExecutablePipelineStep` (DIP / LSP), eliminando
overhead de subprocessos e registrando telemetria nativa no `AssetExecutionContext`.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

_ROOT = str(Path(__file__).resolve().parents[3])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dagster import AssetExecutionContext, Definitions, asset

from src.core.config.constants import PROJECT_ROOT
from src.core.contracts.contracts import ExecutablePipelineStep
from src.bronze.extractors.ingestao_aneel import AneelArcGisExtractor
from src.gold.science.dbscan.eventizador import EventizadorIncendios
from src.gold.science.networkx.network_builder import SINNetworkCentralityModel
from src.silver.etl.etl_dim_hospitais import ETLDimHospitais
from src.silver.etl.etl_dim_municipios import ETLDimMunicipios
from src.silver.etl.etl_dim_ons_linhas_transmissao import ETLDimLinhasTransmissao
from src.silver.etl.etl_dim_ons_sistemas_isolados import ETLDimSistemasIsolados
from src.silver.etl.etl_dim_ons_subestacoes import ETLDimSubestacoes
from src.silver.etl.etl_dim_rodovias_federais import ETLDimRodoviasFederais
from src.silver.etl.etl_dim_terras_indigenas import ETLDimTerrasIndigenas

BRONZE_SRC = os.path.join(str(PROJECT_ROOT), "src", "bronze", "extractors")
ETL_DIR = os.path.join(str(PROJECT_ROOT), "src", "silver", "etl")
SCIENCE_DIR = os.path.join(str(PROJECT_ROOT), "src", "gold", "science")


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


def run_python_script(context: AssetExecutionContext, script_path: str) -> None:
    """Fallback de execução isolada via subprocesso."""
    context.log.info(f"Rodando script: {script_path}")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        context.log.error(result.stdout)
        context.log.error(result.stderr)
        raise RuntimeError(f"Falha ao executar {script_path}")
    context.log.info(result.stdout)


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


def build_druid_lookup_registrar(**kwargs: Any) -> ExecutablePipelineStep:
    """Carrega dinamicamente `DruidLookupRegistrar` de `scripts/run/04_druid_lookups.py`."""
    script_path = os.path.join(str(PROJECT_ROOT), "scripts", "run", "04_druid_lookups.py")
    spec = importlib.util.spec_from_file_location("druid_lookups_step", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DruidLookupRegistrar(**kwargs)


defs = Definitions(
    assets=[
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
    ],
)
