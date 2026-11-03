"""
Pipeline ETL da Dimensão de Rodovias Federais (`ETLDimRodoviasFederais`).

Processa a malha viária do DNIT, simplifica LineStrings redundantes, gera chaves
determinísticas por trecho (`ROD_<md5>`) e classifica criticidade logística.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.core.config.constants import DIMENSIONS_DIR, DNIT_DIR
from src.silver.utils.base import BaseETL
from src.silver.utils.geo_helpers import (
    adicionar_centroides,
    garantir_crs_4326,
    geometry_para_path_json,
    limpar_linestring_geometry,
)
from src.silver.utils.string_helpers import limpar_codigo


class ETLDimRodoviasFederais(BaseETL):
    """ETL da dimensão viária `dim_rodovias_federais.csv`."""

    def __init__(
        self,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> None:
        super().__init__(
            input_path=input_path or os.path.join(str(DNIT_DIR), "mapa_rodovias_federais.geojson"),
            output_path=output_path or os.path.join(str(DIMENSIONS_DIR), "dim_rodovias_federais.csv"),
        )

    @staticmethod
    def _classificar_revestimento(revestimento: object) -> str:
        rev = limpar_codigo(revestimento)
        if "NAO PAVIMENTADO" in rev:
            return "NAO_PAVIMENTADO"
        if "PAVIMENTADO" in rev:
            return "PAVIMENTADO"
        if "IMPLANTADO" in rev:
            return "IMPLANTADO"
        return "NAO_INFORMADO" if rev == "NAO INFORMADO" else "OUTROS"

    @staticmethod
    def _classificar_operacao(status_operacional: object) -> str:
        status = limpar_codigo(status_operacional)
        if status in {"SIM", "S", "OPERACIONAL", "EM OPERACAO", "EM OPERAÇÃO"}:
            return "OPERACIONAL"
        if status in {"NAO", "N", "NÃO", "NAO OPERACIONAL", "NÃO OPERACIONAL"}:
            return "NAO_OPERACIONAL"
        return status if status != "NAO INFORMADO" else "NAO_INFORMADO"

    @staticmethod
    def _classificar_situacao(situacao_fisica: object) -> str:
        sit = limpar_codigo(situacao_fisica)
        if "CONSTRUIDA" in sit:
            return "CONSTRUIDA"
        if "PLANEJADA" in sit:
            return "PLANEJADA"
        if "EM OBRAS" in sit:
            return "EM_OBRAS"
        if "LEITO NATURAL" in sit:
            return "LEITO_NATURAL"
        return sit if sit != "NAO INFORMADO" else "NAO_INFORMADO"

    @staticmethod
    def _classificar_criticidade_rodovia(
        revestimento_classe: str,
        situacao_classe: str,
        operacao_classe: str,
    ) -> str:
        if operacao_classe == "OPERACIONAL" and revestimento_classe == "PAVIMENTADO":
            return "ALTA_RELEVANCIA"
        if operacao_classe == "OPERACIONAL":
            return "MEDIA_RELEVANCIA"
        if situacao_classe in {"EM_OBRAS", "PLANEJADA"}:
            return "BAIXA_RELEVANCIA"
        return "BAIXA_RELEVANCIA" if operacao_classe != "NAO_INFORMADO" else "NAO_INFORMADA"

    @staticmethod
    def _normalizar_codigo_rodovia(valor: object) -> str:
        codigo = limpar_codigo(valor).replace(" ", "")
        if codigo.startswith("BR") and not codigo.startswith("BR-"):
            return codigo.replace("BR", "BR-", 1)
        return codigo

    @staticmethod
    def _gerar_id_trecho_unico(row: pd.Series, indice: object) -> str:
        """Gera PK sintética determinística (`ROD_<hash>`) quando o trecho DNIT não traz ID único."""
        base = (
            f"{row.get('id_trecho_rodoviario_origem', 'NA')}_"
            f"{row.get('codigo_rodovia', 'NA')}_"
            f"{row.get('jurisdicao', 'NA')}_"
            f"{row.get('path_json', 'NA')}_{indice}"
        )
        return f"ROD_{hashlib.md5(base.encode('utf-8')).hexdigest()[:10]}"

    def transform(self, df: gpd.GeoDataFrame) -> pd.DataFrame:
        """Limpa geometrias lineares do DNIT e classifica relevância operacional."""
        if df.empty:
            return df

        gdf = garantir_crs_4326(df)

        cols_rename = {
            "vl_br": "codigo_rodovia",
            "ds_jurisdi": "jurisdicao",
            "ds_revesti": "revestimento",
            "ds_tipo_pa": "tipo_pavimento",
            "ds_situaca": "situacao_fisica",
            "ds_operaci": "status_operacional",
        }
        gdf = gdf.rename(columns={k: v for k, v in cols_rename.items() if k in gdf.columns})
        for col in cols_rename.values():
            if col not in gdf.columns:
                gdf[col] = "NAO INFORMADO"

        gdf["id_trecho_rodoviario_origem"] = gdf.get(
            "id_trecho_rodoviario", pd.Series([""] * len(gdf))
        ).astype(str)
        gdf["codigo_rodovia"] = gdf["codigo_rodovia"].apply(self._normalizar_codigo_rodovia)
        gdf["jurisdicao"] = gdf["jurisdicao"].apply(limpar_codigo)
        gdf["revestimento"] = gdf["revestimento"].apply(limpar_codigo)
        gdf["tipo_pavimento"] = gdf["tipo_pavimento"].apply(limpar_codigo)
        gdf["situacao_fisica"] = gdf["situacao_fisica"].apply(limpar_codigo)
        gdf["status_operacional"] = gdf["status_operacional"].apply(limpar_codigo)

        gdf = gdf[gdf.geometry.notna()].copy()
        gdf["geometry"] = gdf.geometry.apply(limpar_linestring_geometry)
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
        if gdf.empty:
            return gdf

        gdf["path_json"] = gdf.geometry.apply(geometry_para_path_json)
        gdf = adicionar_centroides(gdf)

        gdf = gdf.reset_index(drop=True)
        gdf["id_trecho_rodoviario"] = gdf.apply(lambda r: self._gerar_id_trecho_unico(r, r.name), axis=1)

        gdf["classe_revestimento"] = gdf["revestimento"].apply(self._classificar_revestimento)
        gdf["classe_situacao_fisica"] = gdf["situacao_fisica"].apply(self._classificar_situacao)
        gdf["classe_status_operacional"] = gdf["status_operacional"].apply(self._classificar_operacao)
        gdf["criticidade_rodovia"] = gdf.apply(
            lambda r: self._classificar_criticidade_rodovia(
                r["classe_revestimento"], r["classe_situacao_fisica"], r["classe_status_operacional"]
            ),
            axis=1,
        )

        colunas_finais = [
            "id_trecho_rodoviario", "codigo_rodovia", "jurisdicao",
            "classe_revestimento", "tipo_pavimento", "classe_situacao_fisica",
            "classe_status_operacional", "criticidade_rodovia",
            "latitude", "longitude", "path_json",
        ]

        return pd.DataFrame(gdf[colunas_finais]).drop_duplicates(
            subset=[
                "codigo_rodovia", "jurisdicao", "classe_revestimento",
                "tipo_pavimento", "classe_situacao_fisica",
                "classe_status_operacional", "path_json",
            ]
        )


# Alias preservado para retrocompatibilidade
RodoviasFederaisETL = ETLDimRodoviasFederais


def executar() -> pd.DataFrame | None:
    """Ponto de entrada CLI e de orquestração."""
    return ETLDimRodoviasFederais().execute()


if __name__ == "__main__":
    executar()
