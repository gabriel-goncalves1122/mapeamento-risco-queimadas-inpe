"""
Pipeline ETL da Dimensão de Municípios (`ETLDimMunicipios`).

Processa a malha oficial do IBGE, deriva códigos de 6 e 7 dígitos, siglas de UF,
macrorregiões, centroides métricos e geometrias `path_json` para o Apache Druid/Superset.
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

from src.core.config.constants import DIMENSIONS_DIR, IBGE_DIR
from src.silver.utils.base import BaseETL
from src.silver.utils.cleaners import limpar_texto_druid
from src.silver.utils.geo_helpers import adicionar_centroides, geometry_para_path_json

MAPA_ESTADOS_NOME: dict[str, str] = {
    "11": "RONDONIA", "12": "ACRE", "13": "AMAZONAS", "14": "RORAIMA",
    "15": "PARA", "16": "AMAPA", "17": "TOCANTINS", "21": "MARANHAO",
    "22": "PIAUI", "23": "CEARA", "24": "RIO GRANDE DO NORTE", "25": "PARAIBA",
    "26": "PERNAMBUCO", "27": "ALAGOAS", "28": "SERGIPE", "29": "BAHIA",
    "31": "MINAS GERAIS", "32": "ESPIRITO SANTO", "33": "RIO DE JANEIRO",
    "35": "SAO PAULO", "41": "PARANA", "42": "SANTA CATARINA",
    "43": "RIO GRANDE DO SUL", "50": "MATO GROSSO DO SUL", "51": "MATO GROSSO",
    "52": "GOIAS", "53": "DISTRITO FEDERAL",
}

MAPA_ESTADOS_SIGLA: dict[str, str] = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}

MAPA_REGIAO: dict[str, str] = {
    "11": "NORTE", "12": "NORTE", "13": "NORTE", "14": "NORTE", "15": "NORTE",
    "16": "NORTE", "17": "NORTE", "21": "NORDESTE", "22": "NORDESTE", "23": "NORDESTE",
    "24": "NORDESTE", "25": "NORDESTE", "26": "NORDESTE", "27": "NORDESTE",
    "28": "NORDESTE", "29": "NORDESTE", "31": "SUDESTE", "32": "SUDESTE",
    "33": "SUDESTE", "35": "SUDESTE", "41": "SUL", "42": "SUL", "43": "SUL",
    "50": "CENTRO-OESTE", "51": "CENTRO-OESTE", "52": "CENTRO-OESTE", "53": "CENTRO-OESTE",
}


class ETLDimMunicipios(BaseETL):
    """ETL da dimensão territorial `dim_municipios_coordenadas.csv`."""

    def __init__(
        self,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> None:
        super().__init__(
            input_path=input_path or os.path.join(str(IBGE_DIR), "municipios_br.geojson"),
            output_path=output_path or os.path.join(str(DIMENSIONS_DIR), "dim_municipios_coordenadas.csv"),
        )

    @staticmethod
    def _validar_codigo_ibge(codigo: object) -> str:
        return "" if pd.isna(codigo) else str(codigo).strip()

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Enriquece polígonos municipais com hierarquia regional e serializa `path_json`."""
        gdf["codigo_ibge_7digitos"] = gdf["id"].apply(self._validar_codigo_ibge)
        # O código de 6 dígitos (sem dígito verificador) é o padrão de join com o CNES/DATASUS
        gdf["codigo_ibge"] = gdf["codigo_ibge_7digitos"].str[:6]
        gdf["cod_estado"] = gdf["codigo_ibge_7digitos"].str[:2]

        gdf["estado_nome"] = gdf["cod_estado"].map(MAPA_ESTADOS_NOME).fillna("NAO INFORMADO")
        gdf["estado_sigla"] = gdf["cod_estado"].map(MAPA_ESTADOS_SIGLA).fillna("NI")
        gdf["regiao_brasil"] = gdf["cod_estado"].map(MAPA_REGIAO).fillna("NAO INFORMADO")

        gdf["municipios_nome"] = gdf["name"].apply(limpar_texto_druid)
        gdf["chave_localidade"] = gdf["estado_nome"] + "_" + gdf["municipios_nome"]

        gdf["geometry"] = gdf.geometry.buffer(0)
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

        gdf = adicionar_centroides(gdf)
        gdf["path_json"] = gdf.geometry.apply(geometry_para_path_json)

        colunas_finais = [
            "codigo_ibge", "codigo_ibge_7digitos", "chave_localidade",
            "estado_nome", "estado_sigla", "regiao_brasil", "municipios_nome",
            "latitude", "longitude", "path_json",
        ]

        df_dim = pd.DataFrame(gdf[colunas_finais]).copy()
        df_dim = df_dim.dropna(subset=["codigo_ibge", "municipios_nome"])
        df_dim = df_dim[df_dim["codigo_ibge"].astype(str).str.len() == 6].copy()
        return df_dim.drop_duplicates(subset=["codigo_ibge"])


def executar() -> pd.DataFrame | None:
    """Ponto de entrada CLI e de orquestração."""
    return ETLDimMunicipios().execute()


if __name__ == "__main__":
    executar()
