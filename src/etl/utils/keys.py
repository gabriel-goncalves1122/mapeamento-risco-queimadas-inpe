"""
Normalizacao de chaves dimensionais usadas nos ETLs.

As fontes publicas misturam codigos numericos, strings com casas decimais e
texto livre. Centralizar essas regras evita que joins entre dimensoes quebrem
por detalhes de formato.
"""
import re

import pandas as pd

from src.config.constants import NOT_INFORMED, UNKNOWN_UF
from src.utils.cleaners import limpar_texto_druid

UF_POR_NOME = {
    "ACRE": "AC",
    "ALAGOAS": "AL",
    "AMAPA": "AP",
    "AMAZONAS": "AM",
    "BAHIA": "BA",
    "CEARA": "CE",
    "DISTRITO FEDERAL": "DF",
    "ESPIRITO SANTO": "ES",
    "GOIAS": "GO",
    "MARANHAO": "MA",
    "MATO GROSSO": "MT",
    "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG",
    "PARA": "PA",
    "PARAIBA": "PB",
    "PARANA": "PR",
    "PERNAMBUCO": "PE",
    "PIAUI": "PI",
    "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS",
    "RONDONIA": "RO",
    "RORAIMA": "RR",
    "SANTA CATARINA": "SC",
    "SAO PAULO": "SP",
    "SERGIPE": "SE",
    "TOCANTINS": "TO",
}


def _digits(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return re.sub(r"\D", "", texto)


def normalizar_codigo_ibge(valor):
    """Retorna codigo IBGE municipal com 6 digitos, ou NAO INFORMADO."""
    digitos = _digits(valor)
    if len(digitos) >= 7:
        digitos = digitos[:6]
    if len(digitos) == 6:
        return digitos
    return NOT_INFORMED


def normalizar_codigo_ibge_7digitos(valor):
    """Retorna codigo IBGE completo com 7 digitos, ou NAO INFORMADO."""
    digitos = _digits(valor)
    if len(digitos) == 7:
        return digitos
    return NOT_INFORMED


def normalizar_codigo_cnes(valor):
    """Retorna CNES preservando zeros significativos quando existirem."""
    digitos = _digits(valor)
    return digitos if digitos else NOT_INFORMED


def normalizar_codigo_ti(valor):
    """Retorna codigo FUNAI/TI sem sufixos decimais artificiais."""
    digitos = _digits(valor)
    return digitos if digitos else NOT_INFORMED


def normalizar_uf(valor):
    texto = limpar_texto_druid(valor)
    if texto == NOT_INFORMED:
        return UNKNOWN_UF
    if texto in UF_POR_NOME:
        return UF_POR_NOME[texto]
    texto = re.sub(r"[^A-Z]", "", texto)
    return texto[:2] if len(texto) >= 2 else UNKNOWN_UF


def normalizar_localidade(valor):
    """Normaliza texto de localidade para comparacoes auxiliares de QA."""
    texto = limpar_texto_druid(valor)
    if texto == NOT_INFORMED:
        return ""
    return re.sub(r"[^A-Z0-9 ]", "", texto).strip()


def codigo_informado(valor):
    return bool(valor and str(valor).strip() and str(valor).strip() != NOT_INFORMED)
