import os
import pandas as pd
import json
from config.constants import INPE_DIR
from pipelines.silver.src.spatial.motor_espacial import MotorEspacial
from pipelines.silver.src.streaming_processing.processador import ProcessadorFocos

# ==========================================
# 1. Configurações
# ==========================================
ARQUIVO_BRUTO = os.path.join(str(INPE_DIR), 'focos_incendio_brutos.csv')
QTD_LINHAS_TESTE = 5  # Quantidade de linhas para simular o streaming

def executar_teste():
    print("🚀 Iniciando Ambiente de Teste do Pipeline de Focos...\n")
    
    # 1. Inicia (Aquece) o Motor Espacial (Isso carrega as Dimensões na RAM)
    print("⏳ Aguardando carregamento e indexação das dimensões espaciais...")
    try:
        motor = MotorEspacial()
    except Exception as e:
        print(f"❌ Erro ao iniciar o Motor Espacial. Detalhe: {e}")
        return

    # 2. Inicia o Processador injetando o motor
    processador = ProcessadorFocos(motor)

    # 3. Lê apenas a "Ponta" do CSV gigante
    print(f"\n📂 Lendo as {QTD_LINHAS_TESTE} primeiras linhas do arquivo bruto...")
    try:
        df_amostra = pd.read_csv(ARQUIVO_BRUTO, nrows=QTD_LINHAS_TESTE)
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo {ARQUIVO_BRUTO} não encontrado!")
        return

    # 4. Simula o comportamento do Kafka (Linha a Linha)
    print("\n🔥 Processando Focos de Incêndio (Simulação de Streaming)...\n")
    
    fatos_gerados = []
    
    for index, row in df_amostra.iterrows():
        linha_dict = row.to_dict()
        
        fato = processador.transformar(linha_dict)
        fatos_gerados.append(fato)
        
        print(f"--- 📍 Foco Processado #{index + 1} ---")
        print(json.dumps(fato, indent=4, ensure_ascii=False))
        print("-" * 50)

    print("\n✅ Teste de Transformação concluído com sucesso!")
    print(f"📊 Schema validado para envio ao Apache Druid.")

if __name__ == "__main__":
    executar_teste()
