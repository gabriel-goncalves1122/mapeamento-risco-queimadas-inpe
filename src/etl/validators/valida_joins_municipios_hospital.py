"""
=========================================================
MÓDULO: valida_joins_municipios_hospital.py
---------------------------------------------------------
Função Geral: Módulo do ecossistema DataOps de geoprocessamento e inteligência analítica.
=========================================================
"""
import pandas as pd
import os
from src.config.constants import DIMENSIONS_DIR

# ==========================================
# 1. Configurações de Diretórios (Blindado)
# ==========================================
DIMENSIONS_DIR = str(DIMENSIONS_DIR)

ARQUIVO_HOSPITAIS = os.path.join(DIMENSIONS_DIR, 'dim_hospitais_cnes.csv')
ARQUIVO_MUNICIPIOS = os.path.join(DIMENSIONS_DIR, 'dim_municipios_coordenadas.csv')

print("Iniciando Validação de Integridade (QA) - Hospitais x Municípios...\n")

# ==========================================
# 2. Leitura dos Dados (Forçando STRING no IBGE)
# ==========================================
try:
    df_hospitais = pd.read_csv(ARQUIVO_HOSPITAIS, dtype={'codigo_ibge': str})
    df_municipios = pd.read_csv(ARQUIVO_MUNICIPIOS, dtype={'codigo_ibge': str})
except FileNotFoundError as e:
    print(f"ERRO: Arquivo não encontrado. Execute os scripts de pipeline primeiro.\nDetalhe: {e}")
    exit(1)

total_hospitais = len(df_hospitais)
total_municipios = len(df_municipios)

print(f"-> Base de Hospitais carregada: {total_hospitais} registros.")
print(f"-> Base de Municípios carregada: {total_municipios} registros.\n")

# ==========================================
# 3. Teste de Cruzamento (Merge)
# ==========================================
df_validacao = pd.merge(
    df_hospitais, 
    df_municipios[['codigo_ibge', 'geometria_wkt']], 
    on='codigo_ibge', 
    how='outer', 
    indicator=True
)

# ==========================================
# 4. Análise de Resultados
# ==========================================
hospitais_com_mapa = df_validacao[df_validacao['_merge'] == 'both']
hospitais_sem_mapa = df_validacao[df_validacao['_merge'] == 'left_only']

print("================ RELATÓRIO DE JOIN ================")
print(f"✅ Hospitais CONECTADOS com sucesso: {len(hospitais_com_mapa)} ({(len(hospitais_com_mapa)/total_hospitais)*100:.2f}%)")
print(f"❌ Hospitais DESCONECTADOS (Órfãos): {len(hospitais_sem_mapa)}")
print("===================================================\n")

# ==========================================
# 5. Prova da Relação 1:N 
# ==========================================
print("TOP 5 Municípios com MAIS hospitais conectados:")
top_cidades = hospitais_com_mapa.groupby(['codigo_ibge', 'municipios_nome', 'estado_sigla']).size().reset_index(name='qtd_hospitais')
top_cidades = top_cidades.sort_values(by='qtd_hospitais', ascending=False).head(5)

for index, row in top_cidades.iterrows():
    print(f"- {row['municipios_nome']} ({row['estado_sigla']}): {row['qtd_hospitais']} unidades de saúde")

print("\n---------------------------------------------------")
if len(hospitais_sem_mapa) > 0:
    print("Atenção! Abaixo estão exemplos de hospitais que não encontraram mapa:")
    amostra_orfaos = hospitais_sem_mapa[['codigo_cnes', 'nome_hospital', 'codigo_ibge', 'municipios_nome']].head(5)
    print(amostra_orfaos.to_string(index=False))
else:
    print("Mapeamento perfeito! Nenhum hospital ficou sem polígono espacial.")
