"""
Validador de integridade e unicidade das 7 dimensões espaciais Silver (`DimensionIntegrityValidator`).

Audita a unicidade estrita das Chaves Primárias (PK) exigida pelos Lookups URI do Apache Druid
e a integridade referencial das Chaves Estrangeiras (FK) para o modelo Snowflake.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.core.config.constants import DIMENSIONS_DIR, NOT_INFORMED
from src.core.contracts.contracts import DataValidatorBase, ValidationReport

logger = logging.getLogger(__name__)


class DimensionIntegrityValidator(DataValidatorBase):
    """
    Verifica a unicidade de chaves primárias e consistência referencial de FKs.

    No Apache Druid, Lookups URI (`cachedNamespace`) comportam-se de forma estritamente
    determinística apenas quando a chave (`keyColumn`) é única no arquivo CSV. Chaves
    duplicadas causam sobrescrita silenciosa.
    """

    DIMENSION_SPECS: dict[str, dict[str, Any]] = {
        "dim_municipios_coordenadas.csv": {
            "pk": "codigo_ibge",
            "fks": {},
        },
        "dim_hospitais_cnes.csv": {
            "pk": "codigo_cnes",
            "fks": {"codigo_ibge": "dim_municipios_coordenadas.csv"},
        },
        "dim_terras_indigenas.csv": {
            "pk": "codigo_ti",
            "fks": {},
        },
        "dim_ons_linhas_transmissao.csv": {
            "pk": "id_linha_transmissao",
            "fks": {},
        },
        "dim_ons_subestacoes.csv": {
            "pk": "id_subestacao",
            "fks": {"codigo_ibge": "dim_municipios_coordenadas.csv"},
        },
        "dim_ons_sistemas_isolados.csv": {
            "pk": "id_sistema_isolado",
            "fks": {},
        },
        "dim_rodovias_federais.csv": {
            "pk": "id_trecho_rodoviario",
            "fks": {},
        },
    }

    def __init__(
        self,
        dimensions_dir: str | Path = DIMENSIONS_DIR,
        specs: Mapping[str, dict[str, Any]] | None = None,
    ) -> None:
        self.dimensions_dir = Path(dimensions_dir)
        self.specs = dict(specs or self.DIMENSION_SPECS)

    def validate(self) -> ValidationReport:
        """Executa a varredura das dimensões aferindo unicidade de PK e consistência de FK."""
        total_records = 0
        total_duplicates = 0
        total_orphans = 0
        dimension_reports: dict[str, Any] = {}

        # Carrega dados com cache local para evitar releituras na checagem de FKs
        cached_dfs: dict[str, pd.DataFrame] = {}
        for filename in self.specs:
            filepath = self.dimensions_dir / filename
            if filepath.exists():
                # Força todas as colunas como string para evitar descompasso em chaves numéricas com zeros à esquerda
                df = pd.read_csv(filepath, dtype=str)
                cached_dfs[filename] = df
            else:
                logger.warning("Dimensão '%s' ausente em %s.", filename, self.dimensions_dir)

        municipios_pks: set[str] = set()
        if "dim_municipios_coordenadas.csv" in cached_dfs:
            df_mun = cached_dfs["dim_municipios_coordenadas.csv"]
            municipios_pks = set(df_mun["codigo_ibge"].dropna().unique())
            # Suporta chaves IBGE tanto no formato de 6 dígitos quanto 7 dígitos (com dígito verificador)
            if "codigo_ibge_7digitos" in df_mun.columns:
                municipios_pks.update(df_mun["codigo_ibge_7digitos"].dropna().unique())

        for filename, spec in self.specs.items():
            df = cached_dfs.get(filename)
            if df is None:
                dimension_reports[filename] = {"status": "FILE_NOT_FOUND"}
                continue

            pk_col = spec["pk"]
            count = len(df)
            total_records += count

            # 1. Checagem de unicidade da chave primária (PK)
            pk_series = df[pk_col].dropna()
            num_dups = int(pk_series.duplicated().sum())
            total_duplicates += num_dups

            # 2. Checagem de integridade referencial de chaves estrangeiras (FK)
            fk_orphans = 0
            fks_spec = spec.get("fks", {})
            if "codigo_ibge" in fks_spec and "codigo_ibge" in df.columns and municipios_pks:
                fks_series = df["codigo_ibge"].dropna()
                # Ignora sentinelas como 'NAO INFORMADO'
                fks_reais = fks_series[~fks_series.isin([NOT_INFORMED, "NI", "", "0"])]
                orfãos = (~fks_reais.isin(municipios_pks)).sum()
                fk_orphans = int(orfãos)
                total_orphans += fk_orphans

            dimension_reports[filename] = {
                "total_rows": count,
                "pk_column": pk_col,
                "duplicate_pks": num_dups,
                "orphan_fks": fk_orphans,
                "is_clean": (num_dups == 0 and fk_orphans == 0),
            }

        falhas = total_duplicates + total_orphans
        is_valid = falhas == 0
        matched_records = max(0, total_records - falhas)
        coverage_pct = round((matched_records / total_records) * 100.0, 2) if total_records > 0 else 0.0

        return ValidationReport(
            validator_name=self.step_name,
            is_valid=is_valid,
            total_records=total_records,
            matched_records=matched_records,
            orphan_records=falhas,
            coverage_pct=coverage_pct,
            details=dimension_reports,
        )
