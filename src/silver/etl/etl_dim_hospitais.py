"""
Pipeline ETL da Dimensão de Hospitais e Unidades de Saúde (`ETLDimHospitais`).

Integra as tabelas brutas do CNES/DATASUS, corrige coordenadas invertidas no
território brasileiro, classifica capacidade assistencial e resolve FKs espaciais
contra Municípios (IBGE) e Terras Indígenas (FUNAI) no padrão Functional Core / OO Shell.
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.core.config.constants import (
    DATASUS_DIR,
    DIMENSIONS_DIR,
    EPSG_METRICO,
    FUNAI_DIR,
    IBGE_DIR,
    NOT_INFORMED,
)
from src.silver.utils.base import BaseETL
from src.silver.utils.cleaners import limpar_texto_druid
from src.silver.utils.geo_helpers import (
    geometry_para_path_json,
    is_coordenada_valida_brasil,
    normalizar_par_coordenadas,
)
from src.silver.utils.keys import normalizar_codigo_cnes, normalizar_codigo_ibge
from src.silver.utils.spatial_dimensions import carregar_municipios_geo, carregar_terras_indigenas_geo
from src.silver.utils.string_helpers import limpar_codigo

AUX_DIR = os.path.join(str(DATASUS_DIR), "cnes_aux")
ARQUIVO_PRINCIPAL = "tbEstabelecimento202603.csv"
ARQUIVO_MUNICIPIOS = "tbMunicipio202603.csv"
ARQUIVO_TIPO_UNIDADE = "tbTipoUnidade202603.csv"
OUTPUT_CSV = os.path.join(str(DIMENSIONS_DIR), "dim_hospitais_cnes.csv")


# ==============================================================================
# NÚCLEO FUNCIONAL (Functional Core) - Funções puras de transformação e limpeza
# ==============================================================================


def limpar_coord(valor: object) -> float | None:
    """Converte strings com vírgula ou números para float, tratando nulos com segurança."""
    if pd.isna(valor):
        return None
    try:
        return float(str(valor).strip().replace(",", "."))
    except ValueError:
        return None


def classificar_categoria_unidade(codigo_tipo: object, tipo_unidade: object) -> str:
    """Agrupa códigos TP_UNIDADE do CNES em categorias táticas de resposta a emergências."""
    codigo = limpar_codigo(codigo_tipo)
    tipo = limpar_texto_druid(tipo_unidade)
    hospitais = {"05", "07", "15", "20", "21", "61", "62", "73"}
    atencao_basica = {"01", "02", "71", "72"}
    apoio_diagnostico = {"39", "67", "80"}
    regulacao_gestao = {"64", "68", "76", "81", "82", "84"}
    unidade_movel = {"32", "40", "42"}
    vigilancia = {"50", "85", "83"}
    consultorios = {"04", "22", "36", "77", "78", "79"}
    farmacia = {"43"}

    if codigo in hospitais or "HOSPITAL" in tipo or "PRONTO" in tipo:
        return "HOSPITAL_URGENCIA_EMERGENCIA"
    if codigo in atencao_basica:
        return "ATENCAO_BASICA"
    if codigo in apoio_diagnostico:
        return "APOIO_DIAGNOSTICO_LABORATORIAL"
    if codigo in regulacao_gestao:
        return "REGULACAO_GESTAO"
    if codigo in unidade_movel:
        return "UNIDADE_MOVEL"
    if codigo in vigilancia:
        return "VIGILANCIA_IMUNIZACAO"
    if codigo in consultorios:
        return "CONSULTORIO_ESPECIALIDADE"
    if codigo in farmacia:
        return "FARMACIA"
    if "SAUDE INDIGENA" in tipo:
        return "SAUDE_INDIGENA"
    return "OUTROS"


def classificar_unidade_critica(categoria: str, funciona_24h: str) -> str:
    """Determina se o estabelecimento possui operação ininterrupta ou perfil crítico."""
    if categoria in {"HOSPITAL_URGENCIA_EMERGENCIA", "UNIDADE_MOVEL", "SAUDE_INDIGENA"} or funciona_24h == "S":
        return "SIM"
    return "NAO"


def classificar_capacidade_saude(categoria: str, funciona_24h: str) -> str:
    """Classifica o escalonamento da capacidade médica e de internação."""
    if categoria == "HOSPITAL_URGENCIA_EMERGENCIA" and funciona_24h == "S":
        return "ALTA_CAPACIDADE"
    if categoria == "HOSPITAL_URGENCIA_EMERGENCIA":
        return "MEDIA_CAPACIDADE"
    if categoria == "UNIDADE_MOVEL":
        return "RESPOSTA_MOVEL"
    if categoria == "SAUDE_INDIGENA":
        return "SAUDE_INDIGENA"
    if categoria == "ATENCAO_BASICA":
        return "ATENCAO_LOCAL"
    return "SUPORTE"


def classificar_atendimento(categoria: str, funciona_24h: str) -> str:
    """Padroniza a tipologia de atendimento para o dashboard analítico Superset."""
    if funciona_24h == "S" and categoria == "HOSPITAL_URGENCIA_EMERGENCIA":
        return "CRITICO_24H"
    if categoria == "HOSPITAL_URGENCIA_EMERGENCIA":
        return "CRITICO"
    if categoria == "UNIDADE_MOVEL":
        return "MOBILIDADE_ASSISTENCIAL"
    if categoria == "SAUDE_INDIGENA":
        return "SAUDE_INDIGENA"
    if categoria == "ATENCAO_BASICA":
        return "ATENCAO_LOCAL"
    return "SUPORTE"


# ==============================================================================
# CASCA ORIENTADA A OBJETOS (OO Shell) - Orquestração de I/O e Ciclo de Vida ETL
# ==============================================================================


class ETLDimHospitais(BaseETL):
    """ETL da dimensão assistencial `dim_hospitais_cnes.csv` com enriquecimento geográfico."""

    def __init__(
        self,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
        aux_dir: str | Path | None = None,
        ibge_dir: str | Path | None = None,
        funai_dir: str | Path | None = None,
    ) -> None:
        self.aux_dir = str(aux_dir or AUX_DIR)
        self.ibge_dir = str(ibge_dir or IBGE_DIR)
        self.funai_dir = str(funai_dir or FUNAI_DIR)
        super().__init__(
            input_path=input_path or os.path.join(self.aux_dir, ARQUIVO_PRINCIPAL),
            output_path=output_path or OUTPUT_CSV,
            expected_geom_type="Point",
        )

    def _adicionar_municipio_espacial(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Determina o `codigo_ibge` real da unidade via interseção espacial, usando
        `sjoin_nearest` métrico (EPSG:5880) para unidades costeiras/fronteiriças fora da malha.
        """
        municipios = carregar_municipios_geo(self.ibge_dir)
        pontos = gdf.reset_index(names="_rowid")[["_rowid", "geometry"]]
        join = gpd.sjoin(pontos, municipios, how="left", predicate="intersects")
        join = join.drop_duplicates(subset=["_rowid"]).set_index("_rowid")

        codigo_espacial = join["codigo_ibge"].reindex(gdf.index).fillna(NOT_INFORMED)
        gdf["codigo_ibge_municipio"] = codigo_espacial.values
        gdf["match_status_municipio"] = "OK_ESPACIAL"

        sem_espacial = gdf["codigo_ibge_municipio"] == NOT_INFORMED
        if sem_espacial.any():
            pontos_m = (
                gdf.loc[sem_espacial]
                .reset_index(names="_rowid")[["_rowid", "geometry"]]
                .to_crs(epsg=EPSG_METRICO)
            )
            municipios_m = municipios.to_crs(epsg=EPSG_METRICO)
            nearest = (
                gpd.sjoin_nearest(
                    pontos_m,
                    municipios_m[["codigo_ibge", "geometry"]],
                    how="left",
                )
                .drop_duplicates(subset=["_rowid"])
                .set_index("_rowid")
            )
            gdf.loc[nearest.index, "codigo_ibge_municipio"] = nearest["codigo_ibge"].fillna(NOT_INFORMED)
            gdf.loc[nearest.index, "match_status_municipio"] = "FALLBACK_MUNICIPIO_PROXIMO"

        gdf.loc[gdf["codigo_ibge_municipio"] == NOT_INFORMED, "match_status_municipio"] = "SEM_MUNICIPIO"
        gdf["codigo_ibge"] = gdf["codigo_ibge_municipio"]
        return gdf

    def _adicionar_terra_indigena_proxima(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calcula a distância em km até a Terra Indígena mais próxima em projeção métrica."""
        terras = carregar_terras_indigenas_geo(self.funai_dir)
        gdf["codigo_ti_proxima"] = NOT_INFORMED
        gdf["distancia_ti_km"] = None
        gdf["dentro_terra_indigena"] = 0

        if terras.empty or gdf.empty:
            return gdf

        pontos_m = gdf.reset_index(names="_rowid")[["_rowid", "geometry"]].to_crs(epsg=EPSG_METRICO)
        terras_m = terras.to_crs(epsg=EPSG_METRICO)
        nearest = (
            gpd.sjoin_nearest(
                pontos_m,
                terras_m[["codigo_ti", "geometry"]],
                how="left",
                distance_col="distancia_m",
            )
            .drop_duplicates(subset=["_rowid"])
            .set_index("_rowid")
        )

        gdf["codigo_ti_proxima"] = nearest["codigo_ti"].reindex(gdf.index).fillna(NOT_INFORMED).values
        distancia_m = nearest["distancia_m"].reindex(gdf.index)
        gdf["distancia_ti_km"] = (distancia_m / 1000.0).round(3).values
        gdf["dentro_terra_indigena"] = distancia_m.fillna(-1).eq(0).astype(int).values
        return gdf

    def extract(self) -> gpd.GeoDataFrame:
        """Lê os 3 CSVs relacionais do CNES e reconstrói os pontos geográficos."""
        try:
            df_estab = pd.read_csv(self.input_path, sep=";", dtype=str, encoding="latin-1")
            df_muni = pd.read_csv(
                os.path.join(self.aux_dir, ARQUIVO_MUNICIPIOS), sep=";", dtype=str, encoding="latin-1"
            )
            df_tipo = pd.read_csv(
                os.path.join(self.aux_dir, ARQUIVO_TIPO_UNIDADE), sep=";", dtype=str, encoding="latin-1"
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Erro ao ler arquivos do CNES: {exc}") from exc

        colunas_estab = [
            "CO_CNES", "NO_FANTASIA", "CO_MUNICIPIO_GESTOR",
            "TP_UNIDADE", "TP_ESTAB_SEMPRE_ABERTO", "NU_LATITUDE", "NU_LONGITUDE",
        ]
        df = df_estab[[c for c in colunas_estab if c in df_estab.columns]].copy()

        df["CO_CNES"] = df["CO_CNES"].apply(limpar_codigo)
        df["CO_MUNICIPIO_GESTOR"] = df["CO_MUNICIPIO_GESTOR"].apply(limpar_codigo)
        df["TP_UNIDADE"] = df["TP_UNIDADE"].apply(limpar_codigo)
        df["latitude"] = df["NU_LATITUDE"].apply(limpar_coord)
        df["longitude"] = df["NU_LONGITUDE"].apply(limpar_coord)
        df[["latitude", "longitude"]] = df.apply(
            lambda r: normalizar_par_coordenadas(r["latitude"], r["longitude"]),
            axis=1,
        )

        df["coordenada_valida"] = df.apply(
            lambda r: is_coordenada_valida_brasil(r["latitude"], r["longitude"]),
            axis=1,
        )
        df = df[df["coordenada_valida"]].copy()

        df_muni["CO_MUNICIPIO"] = df_muni["CO_MUNICIPIO"].apply(limpar_codigo)
        df_tipo["CO_TIPO_UNIDADE"] = df_tipo["CO_TIPO_UNIDADE"].apply(limpar_codigo)

        df = pd.merge(
            df,
            df_muni[["CO_MUNICIPIO", "NO_MUNICIPIO", "CO_SIGLA_ESTADO"]],
            left_on="CO_MUNICIPIO_GESTOR",
            right_on="CO_MUNICIPIO",
            how="left",
        )
        df = pd.merge(
            df,
            df_tipo[["CO_TIPO_UNIDADE", "DS_TIPO_UNIDADE"]],
            left_on="TP_UNIDADE",
            right_on="CO_TIPO_UNIDADE",
            how="left",
        )

        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326",
        )

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Aplica taxonomia assistencial, relacionamentos espaciais e contrato `path_json`."""
        gdf["nome_hospital"] = gdf["NO_FANTASIA"].fillna("NAO INFORMADO").apply(limpar_texto_druid)
        gdf["tipo_unidade"] = gdf["DS_TIPO_UNIDADE"].fillna("TIPO NAO INFORMADO").apply(limpar_texto_druid)
        gdf["municipios_nome"] = gdf["NO_MUNICIPIO"].fillna("DESCONHECIDO").apply(limpar_texto_druid)
        gdf["estado_sigla"] = gdf["CO_SIGLA_ESTADO"].fillna("NI").apply(limpar_texto_druid)
        gdf["funciona_24h"] = (
            gdf["TP_ESTAB_SEMPRE_ABERTO"]
            .fillna("N")
            .apply(lambda x: "SIM" if limpar_texto_druid(x) == "S" else "NAO")
        )

        gdf["categoria_unidade"] = gdf.apply(
            lambda r: classificar_categoria_unidade(r["TP_UNIDADE"], r["DS_TIPO_UNIDADE"]), axis=1
        )
        gdf["classe_capacidade_saude"] = gdf.apply(
            lambda r: classificar_capacidade_saude(r["categoria_unidade"], r["funciona_24h"]), axis=1
        )
        gdf["tipo_unidade_critica"] = gdf.apply(
            lambda r: classificar_unidade_critica(r["categoria_unidade"], r["funciona_24h"]), axis=1
        )
        gdf["categoria_atendimento"] = gdf.apply(
            lambda r: classificar_atendimento(r["categoria_unidade"], r["funciona_24h"]), axis=1
        )

        gdf["path_json"] = gdf.geometry.apply(geometry_para_path_json)
        gdf["codigo_ibge_cnes"] = gdf["CO_MUNICIPIO_GESTOR"].apply(normalizar_codigo_ibge)
        gdf["codigo_cnes"] = gdf["CO_CNES"].apply(normalizar_codigo_cnes)

        gdf = self._adicionar_municipio_espacial(gdf)
        gdf = self._adicionar_terra_indigena_proxima(gdf)

        ordem_final = [
            "codigo_cnes", "nome_hospital", "tipo_unidade", "categoria_unidade",
            "tipo_unidade_critica", "categoria_atendimento", "classe_capacidade_saude",
            "funciona_24h", "codigo_ibge",
            "codigo_ti_proxima", "distancia_ti_km", "dentro_terra_indigena",
            "latitude", "longitude", "path_json",
        ]

        df_final = pd.DataFrame(gdf[ordem_final]).copy()
        return df_final.drop_duplicates(subset=["codigo_cnes"])


def executar() -> pd.DataFrame | None:
    """Ponto de entrada CLI e de orquestração."""
    return ETLDimHospitais().execute()


if __name__ == "__main__":
    executar()
