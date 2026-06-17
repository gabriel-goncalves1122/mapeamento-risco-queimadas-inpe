import os
import glob

def get_header(file_path):
    filename = os.path.basename(file_path)
    if "etl_dim_" in filename:
        funcao = "Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid."
    elif "analytics" in file_path:
        funcao = "Abstrai e executa testes analíticos ou geração de relatórios de benchmark do Druid."
    elif "spatial" in file_path:
        funcao = "Motor de processamento espacial vetorial usando R-Tree/KDTree para cálculo de distâncias."
    elif "streaming" in file_path:
        funcao = "Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real."
    elif "orchestration" in file_path:
        funcao = "Repositório do Apache Dagster. Modela os scripts como Software-Defined Assets (SDA)."
    elif "utils" in file_path:
        funcao = "Funções auxiliares e compartilhadas de parsing, matemática e formatação."
    else:
        funcao = "Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica."
        
    return f'''"""
=========================================================
MÓDULO: {filename}
---------------------------------------------------------
Função Geral: {funcao}
=========================================================
"""
'''

for file_path in glob.glob("src/**/*.py", recursive=True):
    # skip empty init
    if os.path.basename(file_path) == "__init__.py":
        continue
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # skip if already has module docstring
    if content.startswith('"""\n==='):
        continue
        
    header = get_header(file_path)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + content)
        
print("Cabeçalhos de módulo aplicados!")
