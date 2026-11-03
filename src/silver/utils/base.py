"""
Contrato base orientado a objetos para pipelines ETL de dimensões estáticas (`BaseETL`).

Implementa o padrão Template Method sobre `ExecutablePipelineStep`, padronizando
extração geográfica, reprojeção WGS84 (EPSG:4326), filtragem topológica e
persistência CSV com injeção do exportador (LSP / DIP).
"""
from __future__ import annotations

import logging
import os
from abc import abstractmethod
from pathlib import Path
from typing import Any, Callable

import geopandas as gpd
import pandas as pd

from src.core.contracts.contracts import ExecutablePipelineStep
from src.silver.utils.df_helpers import salvar_csv
from src.silver.utils.geo_helpers import garantir_crs_4326

logger = logging.getLogger(__name__)


class BaseETL(ExecutablePipelineStep):
    """
    Classe base abstrata para construção das dimensões espaciais na Camada Silver.

    Subclasses implementam `transform(gdf)` (e opcionalmente sobrescrevem `extract()`)
    sem repetir código de leitura, reprojeção CRS ou escrita em disco.
    """

    def __init__(
        self,
        input_path: str | Path,
        output_path: str | Path,
        expected_geom_type: str | None = None,
        csv_saver: Callable[[pd.DataFrame, str | Path], Any] = salvar_csv,
    ) -> None:
        self.input_path = str(input_path)
        self.output_path = str(output_path)
        self.expected_geom_type = expected_geom_type
        self._csv_saver = csv_saver

    def extract(self) -> gpd.GeoDataFrame:
        """Lê o arquivo geoespacial de entrada (`GeoJSON`/`Shapefile`)."""
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.input_path}")
        return gpd.read_file(self.input_path)

    @abstractmethod
    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Aplica as regras de domínio e formatação da dimensão sobre o GeoDataFrame em EPSG:4326."""

    def _run(self, *args: Any, **kwargs: Any) -> pd.DataFrame | None:
        """
        Orquestra o ciclo Extração -> Pré-processamento CRS/Geometria -> Transformação -> Carga.
        """
        logger.info("Iniciando pipeline ETL para: %s", os.path.basename(self.output_path))

        try:
            gdf = self.extract()
        except Exception as exc:
            logger.warning("Erro ao extrair dados: %s", exc)
            return None

        if gdf.empty:
            logger.warning("GeoJSON de entrada está vazio.")
            return None

        gdf = garantir_crs_4326(gdf)
        gdf = gdf[gdf.geometry.notna()].copy()

        if self.expected_geom_type:
            gdf = gdf[gdf.geometry.geom_type == self.expected_geom_type].copy()
            if gdf.empty:
                logger.warning("Nenhuma geometria válida do tipo %s encontrada.", self.expected_geom_type)
                return None

        try:
            df_final = self.transform(gdf)
        except Exception as exc:
            logger.warning("Erro durante a transformação (.transform): %s", exc)
            return None

        if df_final is None or df_final.empty:
            logger.warning("Transformação resultou em um DataFrame vazio. Arquivo não será salvo.")
            return None

        try:
            self._csv_saver(df_final, self.output_path)
            logger.info(
                "Pipeline concluído com sucesso. Salvo em: %s (%s registros)",
                self.output_path,
                len(df_final),
            )
            return df_final
        except Exception as exc:
            logger.warning("Erro ao salvar arquivo CSV: %s", exc)
            return None
