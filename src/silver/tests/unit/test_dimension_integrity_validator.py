"""
Testes unitários do validador de integridade e unicidade dimensional (`DimensionIntegrityValidator`).

Verifica a aderência aos contratos de dados da Arquitetura Snowflake e do Apache Druid
(unicidade estrita de Chaves Primárias e integridade referencial de Chaves Estrangeiras).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.silver.validators.dimensao_integridade_validator import DimensionIntegrityValidator


def test_validador_com_dimensoes_limpas(tmp_path: Path) -> None:
    """Verifica que dimensões sem duplicatas e com FKs válidas retornam relatório 100% íntegro."""
    # Cria dimensão de municípios
    df_mun = pd.DataFrame({
        "codigo_ibge": ["3132404", "3550308"],
        "municipios_nome": ["Itajubá", "São Paulo"],
    })
    df_mun.to_csv(tmp_path / "dim_municipios_coordenadas.csv", index=False)

    # Cria dimensão de hospitais com FK válida para municípios
    df_hosp = pd.DataFrame({
        "codigo_cnes": ["CNES01", "CNES02"],
        "codigo_ibge": ["3132404", "3550308"],
    })
    df_hosp.to_csv(tmp_path / "dim_hospitais_cnes.csv", index=False)

    validador = DimensionIntegrityValidator(dimensions_dir=tmp_path)
    report = validador.validate()

    assert report.is_valid is True
    assert report.orphan_records == 0
    assert report.coverage_pct == 100.0
    assert report.details["dim_municipios_coordenadas.csv"]["duplicate_pks"] == 0
    assert report.details["dim_hospitais_cnes.csv"]["orphan_fks"] == 0


def test_validador_detecta_duplicatas_de_chave_primaria(tmp_path: Path) -> None:
    """Garante que duplicatas de PK são detectadas para evitar corrupção em lookups do Druid."""
    # Município com chave duplicada
    df_mun = pd.DataFrame({
        "codigo_ibge": ["3132404", "3132404"],
        "municipios_nome": ["Itajubá 1", "Itajubá 2"],
    })
    df_mun.to_csv(tmp_path / "dim_municipios_coordenadas.csv", index=False)

    validador = DimensionIntegrityValidator(dimensions_dir=tmp_path)
    report = validador.validate()

    assert report.is_valid is False
    assert report.orphan_records >= 1
    assert report.details["dim_municipios_coordenadas.csv"]["duplicate_pks"] == 1
    assert report.details["dim_municipios_coordenadas.csv"]["is_clean"] is False


def test_validador_detecta_chave_estrangeira_orfa(tmp_path: Path) -> None:
    """Garante que referências a municípios inexistentes são computadas como órfãs."""
    df_mun = pd.DataFrame({
        "codigo_ibge": ["3132404"],
        "municipios_nome": ["Itajubá"],
    })
    df_mun.to_csv(tmp_path / "dim_municipios_coordenadas.csv", index=False)

    # Subestação apontando para município 9999999 inexistente
    df_sub = pd.DataFrame({
        "id_subestacao": ["SUB01"],
        "codigo_ibge": ["9999999"],
    })
    df_sub.to_csv(tmp_path / "dim_ons_subestacoes.csv", index=False)

    validador = DimensionIntegrityValidator(dimensions_dir=tmp_path)
    report = validador.validate()

    assert report.is_valid is False
    assert report.details["dim_ons_subestacoes.csv"]["orphan_fks"] == 1
    assert report.details["dim_ons_subestacoes.csv"]["is_clean"] is False


def test_validador_lida_com_arquivos_ausentes_com_graciosidade(tmp_path: Path) -> None:
    """Garante que a ausência de arquivos não dispara exceção não tratada."""
    validador = DimensionIntegrityValidator(dimensions_dir=tmp_path)
    report = validador.validate()

    assert report.is_valid is True
    assert report.total_records == 0
    assert report.details["dim_municipios_coordenadas.csv"]["status"] == "FILE_NOT_FOUND"
