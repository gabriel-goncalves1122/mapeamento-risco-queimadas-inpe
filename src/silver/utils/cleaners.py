"""
Módulo de funções puras de higienização textual e numérica para Apache Druid e Kafka.

Implementa o padrão Functional Core: funções sem estado para remoção de sentinelas
do INPE (-999), acentuação gráfica e caracteres incompatíveis com payloads analíticos.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

import pandas as pd

from src.core.config.constants import NOT_INFORMED


def limpar_numero(valor: Any, default: float = 0.0) -> float:
    """
    Converte strings numéricas com vírgula decimal ou sufixo de unidade (ex: '138.00 kV')
    em float finito, retornando `default` diante de nulos, NaN ou Infinito.
    """
    try:
        if valor is None or pd.isna(valor):
            return default

        texto = str(valor).strip().replace(",", ".")
        texto = re.sub(r"[^0-9.\-]", "", texto)
        if not texto:
            return default

        numero = float(texto)
        if math.isnan(numero) or math.isinf(numero):
            return default
        return numero
    except Exception:
        return default


def limpar_valor_numerico(valor: Any) -> float:
    """
    Converte outliers do INPE (<= -900, NaN, Inf) em 0.0 para evitar
    rejeição de JSON pelo serializer estrito do Kafka/Druid.
    """
    try:
        if valor is None or pd.isna(valor):
            return 0.0
        texto = str(valor).strip().replace(",", ".")
        f_valor = float(texto)
        if math.isnan(f_valor) or math.isinf(f_valor) or f_valor <= -900:
            return 0.0
        return f_valor
    except (ValueError, TypeError):
        return 0.0


def limpar_valor_numerico_nullable(valor: Any) -> float | None:
    """
    Variante nullable para telemetria satelital: retorna `None` em vez de `0.0`
    quando a leitura do sensor INPE está ausente ou marcada como inválida (<= -900).
    """
    try:
        if valor is None or pd.isna(valor):
            return None
        texto = str(valor).strip().replace(",", ".")
        if not texto:
            return None
        f_valor = float(texto)
        if math.isnan(f_valor) or math.isinf(f_valor) or f_valor <= -900:
            return None
        return f_valor
    except (ValueError, TypeError):
        return None


def limpar_texto_druid(texto: Any) -> str:
    """
    Padroniza strings descritivas para lookups e dimensões no Druid:
    caixa alta, sem acentos (NFD) e livre de aspas/quebras de linha.
    """
    if pd.isna(texto) or not str(texto).strip():
        return NOT_INFORMED

    t = str(texto).replace('"', "").replace("\n", " ").replace("\r", " ").strip().upper()
    t_clean = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return t_clean if t_clean else NOT_INFORMED


def gerar_chave_join(texto: Any) -> str:
    """
    Normaliza nomes para cruzamento tabular (`pd.merge`), descartando sufixos
    entre parênteses (ex: códigos MapBiomas) e pontuação.
    """
    if pd.isna(texto):
        return ""

    t = str(texto).split("(")[0].strip().upper()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^A-Z0-9 ]", "", t)
    return t.strip()


def limpar_wkt(wkt_string: Any) -> str:
    """Remove quebras de linha em strings WKT que quebram linhas de CSV."""
    if pd.isna(wkt_string):
        return ""
    return str(wkt_string).replace("\n", "").replace("\r", "").strip()
