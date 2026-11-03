"""
Pipeline ETL da Dimensão de Terras Indígenas (`ETLDimTerrasIndigenas`).

Unifica polígonos fragmentados da FUNAI (`unary_union`), cruza metadados demográficos
e calcula a sobreposição territorial (`gpd.overlay`) com a malha de municípios do IBGE.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

from src.core.config.constants import DIMENSIONS_DIR, EPSG_METRICO, FUNAI_DIR, IBGE_DIR, NOT_INFORMED
from src.silver.utils.base import BaseETL
from src.silver.utils.cleaners import limpar_texto_druid
from src.silver.utils.df_helpers import limpar_numero
from src.silver.utils.geo_helpers import (
    adicionar_centroides,
    corrigir_geometria_invalida,
    geometry_para_path_json,
)
from src.silver.utils.spatial_dimensions import carregar_municipios_geo
from src.silver.utils.string_helpers import limpar_codigo

FILE_CSV = os.path.join(str(FUNAI_DIR), "tis_poligonais.csv")
FILE_GEOJSON = os.path.join(str(FUNAI_DIR), "mapa_terras_indigenas.geojson")
OUTPUT_CSV = os.path.join(str(DIMENSIONS_DIR), "dim_terras_indigenas.csv")


class ETLDimTerrasIndigenas(BaseETL):
    """ETL da dimensão socioambiental `dim_terras_indigenas.csv`."""

    def __init__(
        self,
        input_path: str | Path | None = None,
        output_path: str | Path | None = None,
        csv_path: str | Path | None = None,
        ibge_dir: str | Path | None = None,
    ) -> None:
        self.csv_path = str(csv_path or FILE_CSV)
        self.ibge_dir = str(ibge_dir or IBGE_DIR)
        super().__init__(
            input_path=input_path or FILE_GEOJSON,
            output_path=output_path or OUTPUT_CSV,
        )

    @staticmethod
    def _limpar_numero(valor: object, default: float = 0.0) -> float:
        return limpar_numero(valor, default=default)

    @staticmethod
    def _classificar_area_ti(area_hectares: float) -> str:
        if area_hectares >= 1_000_000:
            return "MUITO_GRANDE"
        if area_hectares >= 100_000:
            return "GRANDE"
        if area_hectares >= 10_000:
            return "MEDIA"
        return "PEQUENA" if area_hectares > 0 else "NAO_INFORMADA"

    @staticmethod
    def _normalizar_sim_nao(valor: object) -> str:
        texto = limpar_texto_druid(valor)
        if texto in {"SIM", "S", "YES", "Y"}:
            return "SIM"
        if texto in {"NAO", "N", "NO"}:
            return "NAO"
        return "NAO_INFORMADO"

    @staticmethod
    def _classificar_regularizacao(estagio: object) -> str:
        texto = limpar_texto_druid(estagio)
        if "REGULARIZADA" in texto:
            return "REGULARIZADA"
        if "DECLARADA" in texto:
            return "DECLARADA"
        if "DELIMITADA" in texto:
            return "DELIMITADA"
        if "IDENTIFICADA" in texto or "EM ESTUDO" in texto:
            return "EM_ESTUDO_IDENTIFICACAO"
        return texto if texto != "NAO INFORMADO" else "NAO_INFORMADO"

    @staticmethod
    def _classificar_prioridade_funai(
        estagio_regularizacao: str,
        em_faixa_fronteira: str,
        area_hectares: float,
    ) -> str:
        if em_faixa_fronteira == "SIM" and area_hectares >= 100_000:
            return "ALTA_PRIORIDADE"
        if estagio_regularizacao != "REGULARIZADA":
            return "ALTA_PRIORIDADE"
        if area_hectares >= 100_000:
            return "MEDIA_PRIORIDADE"
        return "MONITORAMENTO"

    def _calcular_municipios_interceptados(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Calcula a relação N:M entre Terras Indígenas e Municípios via `gpd.overlay`,
        ordenando os códigos IBGE pela maior área interceptada em EPSG:5880.
        """
        municipios = carregar_municipios_geo(self.ibge_dir).to_crs(epsg=EPSG_METRICO)
        terras = gdf[["codigo_ti", "geometry"]].copy().to_crs(epsg=EPSG_METRICO)

        resultado = pd.DataFrame({"codigo_ti": gdf["codigo_ti"].astype(str)})
        resultado["codigos_ibge_interceptados"] = NOT_INFORMED
        resultado["codigo_ibge_principal"] = NOT_INFORMED
        resultado["qtd_municipios_interceptados"] = 0
        resultado["percentual_area_interceptada"] = 0.0
        resultado["match_status_municipios"] = "SEM_INTERSECAO"

        if terras.empty or municipios.empty:
            return resultado

        areas_ti = terras.assign(area_ti_km2=terras.geometry.area / 1_000_000)[["codigo_ti", "area_ti_km2"]]
        inter = gpd.overlay(
            terras[["codigo_ti", "geometry"]],
            municipios[["codigo_ibge", "geometry"]],
            how="intersection",
            keep_geom_type=False,
        )

        if not inter.empty:
            inter["area_intersecao_km2"] = (inter.geometry.area / 1_000_000).round(6)
            inter = inter[inter["area_intersecao_km2"] > 0].copy()

        if not inter.empty:
            inter = inter.merge(areas_ti, on="codigo_ti", how="left")
            inter["percentual_area_ti"] = (
                (inter["area_intersecao_km2"] / inter["area_ti_km2"]).fillna(0) * 100
            ).round(6)
            inter = inter.sort_values(["codigo_ti", "area_intersecao_km2"], ascending=[True, False])

            registros = []
            for codigo_ti, grupo in inter.groupby("codigo_ti", sort=False):
                codigos = list(dict.fromkeys(grupo["codigo_ibge"].astype(str).tolist()))
                percentual = min(round(float(grupo["percentual_area_ti"].sum()), 6), 100.0)
                registros.append(
                    {
                        "codigo_ti": codigo_ti,
                        "codigos_ibge_interceptados": "|".join(codigos),
                        "codigo_ibge_principal": codigos[0] if codigos else NOT_INFORMED,
                        "qtd_municipios_interceptados": len(codigos),
                        "percentual_area_interceptada": percentual,
                        "match_status_municipios": "OK_INTERSECAO" if percentual >= 95 else "INTERSECAO_PARCIAL",
                    }
                )

            resultado = (
                resultado.drop(
                    columns=[
                        "codigos_ibge_interceptados",
                        "codigo_ibge_principal",
                        "qtd_municipios_interceptados",
                        "percentual_area_interceptada",
                        "match_status_municipios",
                    ]
                )
                .merge(pd.DataFrame(registros), on="codigo_ti", how="left")
            )
            resultado["codigos_ibge_interceptados"] = resultado["codigos_ibge_interceptados"].fillna(NOT_INFORMED)
            resultado["codigo_ibge_principal"] = resultado["codigo_ibge_principal"].fillna(NOT_INFORMED)
            resultado["qtd_municipios_interceptados"] = resultado["qtd_municipios_interceptados"].fillna(0).astype(int)
            resultado["percentual_area_interceptada"] = resultado["percentual_area_interceptada"].fillna(0.0)
            resultado["match_status_municipios"] = resultado["match_status_municipios"].fillna("SEM_INTERSECAO")

        sem_intersecao = resultado["codigo_ibge_principal"] == NOT_INFORMED
        if sem_intersecao.any():
            terras_sem = terras[terras["codigo_ti"].isin(resultado.loc[sem_intersecao, "codigo_ti"])]
            nearest = gpd.sjoin_nearest(
                terras_sem[["codigo_ti", "geometry"]],
                municipios[["codigo_ibge", "geometry"]],
                how="left",
            ).drop_duplicates(subset=["codigo_ti"])
            mapa_fallback = nearest.set_index("codigo_ti")["codigo_ibge"].to_dict()
            for idx, row in resultado[sem_intersecao].iterrows():
                codigo = mapa_fallback.get(row["codigo_ti"], NOT_INFORMED)
                if codigo != NOT_INFORMED:
                    resultado.loc[idx, "codigos_ibge_interceptados"] = codigo
                    resultado.loc[idx, "codigo_ibge_principal"] = codigo
                    resultado.loc[idx, "qtd_municipios_interceptados"] = 1
                    resultado.loc[idx, "match_status_municipios"] = "FALLBACK_MUNICIPIO_PROXIMO"

        return resultado

    def extract(self) -> gpd.GeoDataFrame:
        """Une o GeoJSON poligonal com o CSV cadastral da FUNAI por `codigo_ti`."""
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"GeoJSON não encontrado: {self.input_path}")
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV não encontrado: {self.csv_path}")

        with open(self.input_path, "r", encoding="utf-8") as fp:
            geojson_data = json.load(fp)

        dicionario_geo: dict[str, list[object]] = {}
        for feature in geojson_data.get("features", []):
            codigo_ti = limpar_codigo(feature.get("properties", {}).get("codigo_ti", ""))
            if codigo_ti == "NAO INFORMADO":
                continue
            try:
                geom = corrigir_geometria_invalida(shape(feature.get("geometry")))
                if geom:
                    dicionario_geo.setdefault(codigo_ti, []).append(geom)
            except Exception:
                continue

        registros_geo = []
        for codigo_ti, geoms in dicionario_geo.items():
            geom_unificada = corrigir_geometria_invalida(unary_union(geoms))
            if geom_unificada:
                registros_geo.append({"codigo_ti": codigo_ti, "geometry": geom_unificada})

        gdf_geo = gpd.GeoDataFrame(registros_geo, crs="EPSG:4326")

        df_csv = pd.read_csv(self.csv_path, dtype=str)
        df_csv["codigo_ti"] = df_csv["terrai_codigo"].apply(limpar_codigo)

        renames = {
            "terrai_nome": "nome_terra_indigena",
            "etnia_nome": "etnia",
            "municipio_nome": "municipios",
            "uf_sigla": "estado_sigla",
            "superficie_perimetro_ha": "area_hectares",
            "fase_ti": "estagio_regularizacao",
            "modalidade_ti": "modalidade",
            "cr": "coordenacao_regional",
            "faixa_fronteira": "em_faixa_fronteira",
        }
        df_csv = df_csv.rename(columns=renames)

        colunas_necessarias = [
            "codigo_ti", "nome_terra_indigena", "etnia", "municipios", "estado_sigla",
            "area_hectares", "estagio_regularizacao", "modalidade",
            "coordenacao_regional", "em_faixa_fronteira",
        ]

        colunas_texto = {
            "nome_terra_indigena", "etnia", "municipios", "estado_sigla",
            "estagio_regularizacao", "modalidade", "coordenacao_regional",
        }
        for col in colunas_necessarias:
            if col not in df_csv.columns:
                df_csv[col] = "NAO INFORMADO"
            elif col in colunas_texto:
                df_csv[col] = df_csv[col].apply(limpar_texto_druid)

        df_csv["area_hectares"] = df_csv["area_hectares"].apply(self._limpar_numero).round(2)
        df_csv["em_faixa_fronteira"] = df_csv["em_faixa_fronteira"].apply(self._normalizar_sim_nao)
        df_csv["estagio_regularizacao"] = df_csv["estagio_regularizacao"].apply(self._classificar_regularizacao)
        df_csv_final = df_csv.drop_duplicates(subset=["codigo_ti"])[colunas_necessarias]

        df_merged = pd.merge(df_csv_final, gdf_geo, on="codigo_ti", how="inner")
        return gpd.GeoDataFrame(df_merged, geometry="geometry", crs="EPSG:4326")

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Gera centroides, `path_json`, prioridade FUNAI e municípios interceptados."""
        gdf = adicionar_centroides(gdf)
        gdf["path_json"] = gdf.geometry.apply(geometry_para_path_json)

        gdf["classe_area_ti"] = gdf["area_hectares"].apply(self._classificar_area_ti)
        gdf["prioridade_funai"] = gdf.apply(
            lambda r: self._classificar_prioridade_funai(
                r["estagio_regularizacao"], r["em_faixa_fronteira"], r["area_hectares"]
            ),
            axis=1,
        )
        rel_municipios = self._calcular_municipios_interceptados(gdf)
        gdf = gdf.merge(rel_municipios, on="codigo_ti", how="left")
        gdf = gdf.fillna("NAO INFORMADO")

        colunas_finais = [
            "codigo_ti", "nome_terra_indigena", "etnia", "estado_sigla",
            "area_hectares", "classe_area_ti", "estagio_regularizacao", "modalidade",
            "coordenacao_regional", "em_faixa_fronteira", "prioridade_funai",
            "codigos_ibge_interceptados", "codigo_ibge_principal",
            "qtd_municipios_interceptados", "percentual_area_interceptada",
            "latitude", "longitude", "path_json",
        ]
        return pd.DataFrame(gdf[colunas_finais])


def executar() -> pd.DataFrame | None:
    """Ponto de entrada CLI e de orquestração."""
    return ETLDimTerrasIndigenas().execute()


main = executar


if __name__ == "__main__":
    executar()
