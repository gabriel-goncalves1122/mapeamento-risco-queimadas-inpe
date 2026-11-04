"""
Serviço de normalização de chaves dimensionais (`DimensionalKeyNormalizer`).

Padroniza identificadores de fontes públicas (IBGE 6/7 dígitos, CNES, FUNAI/TI e UF),
removendo sufixos decimais `.0` gerados pelo Pandas e assegurando integridade referencial
nos joins do modelo Snowflake.
"""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.core.config.constants import NOT_INFORMED, UNKNOWN_UF
from src.silver.utils.cleaners import limpar_texto_druid

UF_POR_NOME: dict[str, str] = {
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


class DimensionalKeyNormalizer:
    """Normalizador estático de chaves estrangeiras e siglas territoriais."""

    @staticmethod
    def extrair_digitos(valor: Any) -> str:
        """Extrai apenas dígitos numéricos descartando sufixos `.0` de floats serializados."""
        if pd.isna(valor):
            return ""
        texto = str(valor).strip()
        if texto.endswith(".0"):
            texto = texto[:-2]
        return re.sub(r"\D", "", texto)

    @classmethod
    def normalizar_codigo_ibge(cls, valor: Any) -> str:
        """Padroniza código municipal IBGE em 6 dígitos (padrão CNES/DATASUS) ou NAO INFORMADO."""
        digitos = cls.extrair_digitos(valor)
        if len(digitos) >= 7:
            digitos = digitos[:6]
        return digitos if len(digitos) == 6 else NOT_INFORMED

    @classmethod
    def normalizar_codigo_ibge_7digitos(cls, valor: Any) -> str:
        """Padroniza código municipal IBGE completo com dígito verificador (7 dígitos)."""
        digitos = cls.extrair_digitos(valor)
        return digitos if len(digitos) == 7 else NOT_INFORMED

    @classmethod
    def normalizar_codigo_cnes(cls, valor: Any) -> str:
        """Retorna identificador CNES preservando zeros à esquerda significativos."""
        digitos = cls.extrair_digitos(valor)
        return digitos if digitos else NOT_INFORMED

    @classmethod
    def normalizar_codigo_ti(cls, valor: Any) -> str:
        """Normaliza código oficial de Terra Indígena da FUNAI."""
        digitos = cls.extrair_digitos(valor)
        return digitos if digitos else NOT_INFORMED

    @staticmethod
    def normalizar_uf(valor: Any) -> str:
        """Converte nome por extenso ou sigla de unidade federativa em UF de 2 letras."""
        texto = limpar_texto_druid(valor)
        if texto == NOT_INFORMED:
            return UNKNOWN_UF
        if texto in UF_POR_NOME:
            return UF_POR_NOME[texto]
        texto = re.sub(r"[^A-Z]", "", texto)
        return texto[:2] if len(texto) >= 2 else UNKNOWN_UF

    @staticmethod
    def normalizar_localidade(valor: Any) -> str:
        """Normaliza nome de localidade para auditoria e comparações de QA."""
        texto = limpar_texto_druid(valor)
        if texto == NOT_INFORMED:
            return ""
        return re.sub(r"[^A-Z0-9 ]", "", texto).strip()

    @staticmethod
    def codigo_informado(valor: Any) -> bool:
        """Indica se a chave possui valor útil diferente de nulo e NAO INFORMADO."""
        return bool(valor and str(valor).strip() and str(valor).strip() != NOT_INFORMED)


_digits = DimensionalKeyNormalizer.extrair_digitos
normalizar_codigo_ibge = DimensionalKeyNormalizer.normalizar_codigo_ibge
normalizar_codigo_ibge_7digitos = DimensionalKeyNormalizer.normalizar_codigo_ibge_7digitos
normalizar_codigo_cnes = DimensionalKeyNormalizer.normalizar_codigo_cnes
normalizar_codigo_ti = DimensionalKeyNormalizer.normalizar_codigo_ti
normalizar_uf = DimensionalKeyNormalizer.normalizar_uf
normalizar_localidade = DimensionalKeyNormalizer.normalizar_localidade
codigo_informado = DimensionalKeyNormalizer.codigo_informado
