"""
=========================================================
MÓDULO: Auxiliares de Texto e Regex (string_helpers.py)
---------------------------------------------------------
Função Geral: Processa metadados brutos que vêm embutidos
em atributos estranhos (como balões HTML do KML do ONS) e
extrai apenas o valor semântico limpo para o Apache Druid.
=========================================================
"""
import re
import pandas as pd
from config.constants import NOT_INFORMED, UNKNOWN_UF
from pipelines.silver.utils.cleaners import limpar_texto_druid


def limpar_codigo(valor):
    if pd.isna(valor):
        return NOT_INFORMED

    texto = str(valor).replace('"', '').replace('\n', ' ').replace('\r', ' ').strip()
    
    if texto.endswith('.0'):
        texto = texto[:-2]

    if not texto:
        return NOT_INFORMED

    return limpar_texto_druid(texto)


def extrair_popup_valor(html, rotulo):
    """
    Busca dentro de uma string de código HTML (comum em arquivos KML da ANEEL/ONS)
    o valor correspondente a um rótulo específico via Expressão Regular.
    """
    if pd.isna(html):
        return ""

    texto = str(html)
    padrao = rf'<b>\s*{re.escape(rotulo)}\s*:\s*<\/b>\s*(.*?)(?:<br\/>|$)'
    match = re.search(padrao, texto, flags=re.IGNORECASE)

    if not match:
        return ""

    return match.group(1).strip()


def extrair_uf_popup(texto):
    if pd.isna(texto):
        return UNKNOWN_UF

    match = re.search(r'-\s*([A-Z]{2})\s*$', str(texto).upper())

    if match:
        return match.group(1)

    return UNKNOWN_UF


def extrair_uf_nome_linha(nome):
    if pd.isna(nome):
        return UNKNOWN_UF

    texto = str(nome).upper().strip()
    match = re.search(r'\b([A-Z]{2})(?:\/[A-Z]{2})?\s*$', texto)

    if match:
        return match.group(1)

    return UNKNOWN_UF
