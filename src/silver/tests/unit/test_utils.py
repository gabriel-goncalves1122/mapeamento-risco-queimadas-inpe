"""
=========================================================
MÓDULO DE TESTES UNITÁRIOS: test_utils.py
---------------------------------------------------------
Testa de forma exaustiva as funções da camada de utilitários
(src.silver.utils), cobrindo parsing numérico, validação
espacial de coordenadas, blindagem de tipos e Façade pública.
=========================================================
"""
import math
import os
import pandas as pd
from shapely.geometry import Polygon

from src.core.config.constants import NOT_INFORMED, UNKNOWN_UF
import src.silver.utils as silver_utils
from src.silver.utils.cleaners import (
    gerar_chave_join,
    limpar_numero,
    limpar_texto_druid,
    limpar_valor_numerico,
    limpar_valor_numerico_nullable,
    limpar_wkt,
)
from src.silver.utils.df_helpers import salvar_csv
from src.silver.utils.geo_helpers import (
    coordenada_valida,
    corrigir_geometria_invalida,
    is_coordenada_valida_brasil,
    normalizar_par_coordenadas,
    remover_consecutivos_duplicados,
    remover_repeticoes_periodicas,
)
from src.silver.utils.string_helpers import (
    extrair_popup_valor,
    extrair_uf_nome_linha,
    extrair_uf_popup,
    limpar_codigo,
)


def test_coordenada_valida_casos_positivos():
    """Valida coordenadas no globo terrestre com diferentes formatos."""
    assert coordenada_valida(-22.5, -45.0) is True
    assert coordenada_valida("-22.5", "-45.0") is True
    assert coordenada_valida("-22,5", "-45,0") is True
    assert coordenada_valida(-90, -180) is True
    assert coordenada_valida(90, 180) is True


def test_coordenada_valida_casos_negativos():
    """Valida rejeição de coordenadas nulas, fora do globo, textos e ponto zero."""
    assert coordenada_valida(0.0, 0.0) is False
    assert coordenada_valida("0", "0") is False
    assert coordenada_valida(None, -45.0) is False
    assert coordenada_valida(-22.5, None) is False
    assert coordenada_valida(float("nan"), -45.0) is False
    assert coordenada_valida(-22.5, float("inf")) is False
    assert coordenada_valida(-90.1, 0.0) is False
    assert coordenada_valida(0.0, 180.1) is False
    assert coordenada_valida("ABC", "DEF") is False
    assert coordenada_valida("", "") is False


def test_is_coordenada_valida_brasil():
    """Valida o enquadramento na bounding box do território brasileiro."""
    # Pontos conhecidos no Brasil
    assert is_coordenada_valida_brasil(-23.55, -46.63) is True  # São Paulo
    assert is_coordenada_valida_brasil("-22.25", "-45.70") is True  # Itajubá / MG
    assert is_coordenada_valida_brasil(-3.1, -60.0) is True  # Manaus / AM

    # Pontos fora do Brasil
    assert is_coordenada_valida_brasil(48.85, 2.35) is False  # Paris
    assert is_coordenada_valida_brasil(0.0, 0.0) is False
    assert is_coordenada_valida_brasil(-22.5, 10.0) is False  # Oceano Atlântico Leste
    assert is_coordenada_valida_brasil(None, None) is False


def test_normalizar_par_coordenadas_inversoes_e_strings():
    """Testa recuperação de coordenadas invertidas ou com sinais trocados."""
    # Inversão lon/lat (-45.7, -22.25 -> latitude=-22.25, longitude=-45.7)
    res = normalizar_par_coordenadas(-45.7, -22.25)
    assert res["latitude"] == -22.25
    assert res["longitude"] == -45.7

    # Sinais invertidos (22.25, 45.70)
    res2 = normalizar_par_coordenadas(22.25, 45.70)
    assert res2["latitude"] == -22.25
    assert res2["longitude"] == -45.70

    # Entradas em formato string com vírgula (sem disparar TypeError)
    res3 = normalizar_par_coordenadas("-22,25", "-45,70")
    assert res3["latitude"] == -22.25
    assert res3["longitude"] == -45.70

    # Coordenadas impossíveis
    res_invalido = normalizar_par_coordenadas(999, 999)
    assert res_invalido["latitude"] is None
    assert res_invalido["longitude"] is None


def test_limpar_numero_e_cleaners():
    """Valida conversão robusta de strings sujas em float e fallbacks."""
    assert limpar_numero(12.5) == 12.5
    assert limpar_numero("12,5") == 12.5
    assert limpar_numero("  138.00 kV ") == 138.0
    assert limpar_numero("-500,25") == -500.25
    assert limpar_numero(None, default=-1.0) == -1.0
    assert limpar_numero("texto invalido", default=0.0) == 0.0
    assert limpar_numero(float("nan"), default=99.0) == 99.0


def test_limpar_valor_numerico_nullable():
    """Valida comportamento estrito nullable para satélites/INPE."""
    assert limpar_valor_numerico_nullable("15,7") == 15.7
    assert limpar_valor_numerico_nullable("-999.0") is None
    assert limpar_valor_numerico_nullable("-999") is None
    assert limpar_valor_numerico_nullable(None) is None
    assert limpar_valor_numerico_nullable("") is None
    assert limpar_valor_numerico_nullable("letras") is None


def test_salvar_csv_cria_diretorios(tmp_path):
    """Testa se salvar_csv cria pastas intermediárias automaticamente."""
    arquivo_saida = tmp_path / "subdiretorio" / "novo_nivel" / "saida.csv"
    df = pd.DataFrame({"coluna_a": [1, 2], "coluna_b": ["x", "y"]})

    assert not arquivo_saida.parent.exists()
    salvar_csv(df, str(arquivo_saida))
    assert arquivo_saida.exists()

    df_lido = pd.read_csv(arquivo_saida)
    assert len(df_lido) == 2


def test_string_helpers_popups_e_linhas():
    """Valida extratores de metadados de KML ONS e nomes de ativos."""
    html_sample = "<b>SUBESTACAO:</b> ITAJUBA 500KV<br/><b>TENSAO:</b> 500<br/>"
    assert extrair_popup_valor(html_sample, "SUBESTACAO") == "ITAJUBA 500KV"
    assert extrair_popup_valor(html_sample, "TENSAO") == "500"
    assert extrair_popup_valor(html_sample, "INEXISTENTE") == ""

    assert extrair_uf_popup("SUBESTACAO RIO VERDE - GO") == "GO"
    assert extrair_uf_popup("SUBESTACAO SEM UF") == UNKNOWN_UF

    assert extrair_uf_nome_linha("LT 500 KV XINGU / ESTREITO - MG") == "MG"
    assert extrair_uf_nome_linha("LT 230 KV TUCURUI / MARABA - PA") == "PA"

    assert limpar_codigo("3132404.0") == "3132404"
    assert limpar_codigo(None) == NOT_INFORMED


def test_corrigir_geometria_invalida():
    """Valida autocorreção de polígono com auto-interseção (bowtie polygon)."""
    bowtie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    assert not bowtie.is_valid
    corrigida = corrigir_geometria_invalida(bowtie)
    assert corrigida is not None
    assert corrigida.is_valid


def test_facade_reexporta_todos_os_simbolos():
    """Valida se a Façade src.silver.utils exporta todos os 28 símbolos sem nulos."""
    for simbolo in silver_utils.__all__:
        assert hasattr(silver_utils, simbolo), f"Símbolo ausente na Façade: {simbolo}"
        assert getattr(silver_utils, simbolo) is not None
