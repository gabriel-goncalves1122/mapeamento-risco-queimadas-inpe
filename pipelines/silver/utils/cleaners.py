"""
=========================================================
MÓDULO: cleaners.py
---------------------------------------------------------
Função Geral: Funções auxiliares e compartilhadas de parsing, matemática e formatação.
=========================================================
"""
import math
import re
import unicodedata
import pandas as pd
from config.constants import NOT_INFORMED

def limpar_valor_numerico(valor):
    """
    Tratamento de Outliers do INPE (ex: -999.0) e conversão de NaN/Inf para 0.0,
    protegendo a quebra do JSON no Kafka/Apache Druid.
    """
    try:
        f_valor = float(valor)
        if math.isnan(f_valor) or math.isinf(f_valor) or f_valor <= -900:
            return 0.0
        return f_valor
    except (ValueError, TypeError):
        return 0.0

def limpar_texto_druid(texto):
    """
    Padroniza colunas descritivas e chaves para o Druid:
    - Sem acentos
    - UPPERCASE (Caixa alta)
    - Sem quebras de linha ou aspas que corrompem o CSV
    """
    if pd.isna(texto) or not str(texto).strip(): 
        return NOT_INFORMED
    
    # Remove aspas e quebras invisíveis
    t = str(texto).replace('"', '').replace('\n', ' ').replace('\r', ' ').strip().upper()
    
    # Remove acentos
    t_clean = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    
    return t_clean if t_clean else NOT_INFORMED

def gerar_chave_join(texto):
    """
    Limpeza extrema e estrita para colunas que farão JOIN (pd.merge).
    Remove parênteses e caracteres especiais, mantendo apenas letras, números e espaços.
    """
    if pd.isna(texto): 
        return ""
    
    t = str(texto).split('(')[0].strip().upper() # Remove coisas como "(1201)" do MapBiomas
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    t = re.sub(r'[^A-Z0-9 ]', '', t) # Mantém estritamente letras, números e espaços
    
    return t.strip()

def limpar_wkt(wkt_string):
    """
    Remove quebras de linha geradas por bibliotecas espaciais (como Shapely)
    que destroem a estrutura tabular do CSV.
    """
    if pd.isna(wkt_string):
        return ""
    return str(wkt_string).replace('\n', '').replace('\r', '').strip()
