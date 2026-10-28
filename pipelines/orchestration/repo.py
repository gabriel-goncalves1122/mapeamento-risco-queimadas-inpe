"""
=========================================================
MÓDULO: repo.py
---------------------------------------------------------
Função Geral: Repositório do Apache Dagster. Modela os scripts como Software-Defined Assets (SDA).
=========================================================
"""
import os
import sys
import subprocess
from dagster import asset, Definitions, AssetExecutionContext
from config.constants import PROJECT_ROOT

# Helper para rodar scripts como subprocesso (para isolar os ambientes se necessário)
def run_python_script(context: AssetExecutionContext, script_path: str):
    context.log.info(f"Rodando script: {script_path}")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        context.log.error(result.stdout)
        context.log.error(result.stderr)
        raise Exception(f"Falha ao executar {script_path}")
    context.log.info(result.stdout)

# Caminhos absolutos
BRONZE_SRC = os.path.join(str(PROJECT_ROOT), 'pipelines', 'bronze', 'src')
ETL_DIR = os.path.join(str(PROJECT_ROOT), 'pipelines', 'silver', 'src', 'etl_dimensions')
SCIENCE_DIR = os.path.join(str(PROJECT_ROOT), 'pipelines', 'gold', 'src', 'science')

# ==========================================
# 1. Assets Iniciais (Raw -> Dimensions Básicas)
# ==========================================
@asset(group_name="dimensions", compute_kind="python")
def dim_municipios(context: AssetExecutionContext):
    """Dimensão de Municípios em path_json para Druid/Superset"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_municipios.py'))

@asset(group_name="dimensions", compute_kind="python")
def dim_hospitais(context: AssetExecutionContext):
    """Dimensão de Hospitais em path_json para Druid/Superset"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_hospitais.py'))

@asset(group_name="dimensions", compute_kind="python")
def dim_terras_indigenas(context: AssetExecutionContext):
    """Dimensão de Terras Indígenas em path_json para Druid/Superset"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_terras_indigenas.py'))

@asset(group_name="dimensions", compute_kind="python")
def dim_rodovias_federais(context: AssetExecutionContext):
    """Dimensão de Rodovias Federais em path_json para Druid/Superset"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_rodovias_federais.py'))

# ==========================================
# 2. Infraestrutura ONS (Linear e Pontual)
# ==========================================
@asset(group_name="infra_ons", compute_kind="python")
def aneel_ons_data(context: AssetExecutionContext):
    """Extrai malhas de transmissão via ArcGIS REST da ANEEL"""
    run_python_script(context, os.path.join(BRONZE_SRC, 'ingestao_aneel.py'))

@asset(deps=[aneel_ons_data], group_name="infra_ons", compute_kind="python")
def dim_linhas_transmissao(context: AssetExecutionContext):
    """Processa linhas de transmissão"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_ons_linhas_transmissao.py'))

@asset(deps=[aneel_ons_data], group_name="infra_ons", compute_kind="python")
def dim_subestacoes(context: AssetExecutionContext):
    """Processa subestações e gera pontos"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_ons_subestacoes.py'))

@asset(deps=[aneel_ons_data], group_name="infra_ons", compute_kind="python")
def dim_sistemas_isolados(context: AssetExecutionContext):
    """Processa sistemas isolados e gera pontos"""
    run_python_script(context, os.path.join(ETL_DIR, 'etl_dim_ons_sistemas_isolados.py'))

# ==========================================
# 3. Network Science (Centralidade em Redes ONS)
# ==========================================
@asset(deps=[dim_linhas_transmissao, dim_subestacoes], group_name="science_models", compute_kind="networkx")
def network_centrality_model(context: AssetExecutionContext):
    """Calcula Betweenness Centrality e Risco em Cascata usando NetworkX"""
    run_python_script(context, os.path.join(SCIENCE_DIR, 'networkx', 'network_builder.py'))

# ==========================================
# 4. Spatio-Temporal Clustering (Incêndios)
# ==========================================
@asset(group_name="science_models", compute_kind="scikit-learn")
def st_dbscan_fire_events(context: AssetExecutionContext):
    """Agrupa focos isolados em Eventos Dinâmicos de Incêndio (Convex Hull)"""
    run_python_script(context, os.path.join(SCIENCE_DIR, 'dbscan', 'eventizador.py'))

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
        st_dbscan_fire_events
    ],
)
