"""
=========================================================
MÓDULO: run_etl.py
---------------------------------------------------------
Função Geral: Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica.
=========================================================
"""
import os
import sys
import subprocess
import time

# ==========================================
# 0. Pathing e Configuração
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
PIPELINES_DIR = os.path.join(CURRENT_DIR, 'pipelines')
VALIDATORS_DIR = os.path.join(CURRENT_DIR, 'validators')

# A ORDEM IMPORTA: Primeiro as dimensões base, depois as infraestruturas
SCRIPTS_PIPELINE = [
    'etl_dim_municipios.py',                # 1. Malha Base
    'etl_dim_hospitais.py',                 # 2. Saúde
    'etl_dim_terras_indigenas.py',          # 3. Terras Indígenas
    'etl_dim_rodovias_federais.py',         # 4. Rodovias
    'ingestao_aneel.py',                    # 5. Download base ONS
    'etl_dim_ons_linhas_transmissao.py',    # 6. Linhas de Transmissão
    'etl_dim_ons_subestacoes.py',           # 7. Subestações
    'etl_dim_ons_sistemas_isolados.py'      # 8. Sistemas Isolados
]

# Script de QA para rodar no final
SCRIPTS_VALIDACAO = [
    'valida_joins_municipios_hospital.py'
]

def rodar_script(caminho_script):
    """Executa um script Python como um processo isolado."""
    nome_script = os.path.basename(caminho_script)
    print(f"\n⏳ Iniciando: [ {nome_script} ] ...")
    
    inicio = time.time()
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = PROJECT_ROOT + os.pathsep + env.get('PYTHONPATH', '')
        resultado = subprocess.run(
            [sys.executable, caminho_script],
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        
        tempo_gasto = time.time() - inicio
        print(resultado.stdout)
        print(f"✅ Concluído: [ {nome_script} ] em {tempo_gasto:.2f} segundos.")
        
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(f"❌ ERRO FATAL: O script [ {nome_script} ] falhou!")
        print(f"Log do Erro:\n{e.stderr}")
        print("\n🛑 Pipeline de ETL interrompido para proteger o Data Lakehouse.")
        sys.exit(1)

def orquestrar_etl():
    print("🚀 INICIANDO ORQUESTRAÇÃO DO DATA LAKEHOUSE (ETL BATCH) 🚀")
    print("=" * 60)
    
    tempo_total_inicio = time.time()

    # 1. Executa a extração e transformação (Pipelines)
    for script in SCRIPTS_PIPELINE:
        caminho_completo = os.path.join(PIPELINES_DIR, script)
        if os.path.exists(caminho_completo):
            rodar_script(caminho_completo)
        else:
            print(f"⚠️ AVISO: Script {script} não encontrado no diretório. Pulando...")

    # 2. Executa a validação de qualidade (QA)
    print("\n" + "=" * 60)
    print("🔎 INICIANDO QUALITY ASSURANCE (QA / VALIDAÇÃO)")
    print("=" * 60)
    
    for script in SCRIPTS_VALIDACAO:
        caminho_completo = os.path.join(VALIDATORS_DIR, script)
        if os.path.exists(caminho_completo):
            rodar_script(caminho_completo)

    tempo_total = time.time() - tempo_total_inicio
    print("\n" + "=" * 60)
    print(f"🎉 SUCESSO! Todas as Dimensões geradas e validadas em {tempo_total:.2f} segundos.")
    print("O seu motor espacial já pode ser abastecido!")

if __name__ == "__main__":
    orquestrar_etl()
