"""
=========================================================
MÓDULO: base.py
---------------------------------------------------------
Função Geral: Funções auxiliares e compartilhadas de parsing, matemática e formatação.
=========================================================
"""
import os
import pandas as pd
import geopandas as gpd
import logging
from abc import ABC, abstractmethod

from pipelines.silver.utils.geo_helpers import garantir_crs_4326
from pipelines.silver.utils.df_helpers import salvar_csv

logger = logging.getLogger(__name__)


class BaseETL(ABC):
    """
    Classe base para padronizar os pipelines de ETL estático.
    Remove o boilerplate de carregamento de arquivos geográficos,
    validação de geometria, projeção EPSG:4326 e persistência em CSV.
    """

    def __init__(self, input_path: str, output_path: str, expected_geom_type: str = None):
        """
        Inicializa o pipeline base.

        Args:
            input_path: Caminho completo para o GeoJSON/Shapefile de entrada.
            output_path: Caminho completo para salvar o CSV de saída.
            expected_geom_type: 'Point', 'LineString', 'MultiLineString' ou 'Polygon'. 
                                Se fornecido, filtra geometrias estritamente por este tipo.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.expected_geom_type = expected_geom_type

    def extract(self) -> gpd.GeoDataFrame:
        """
        Extrai os dados da fonte. O comportamento padrão é ler o GeoJSON/Shapefile
        do self.input_path. Subclasses podem sobrescrever para origens múltiplas.
        """
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.input_path}")
        return gpd.read_file(self.input_path)

    @abstractmethod
    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Método abstrato que deve ser implementado pelas subclasses.
        Aplica a lógica de negócio específica de cada dimensão.
        
        Args:
            gdf: GeoDataFrame bruto recém carregado, já projetado em 4326 e sem geometrias nulas.
            
        Returns:
            DataFrame: Pandas DataFrame pronto para ser persistido em CSV.
        """
        pass

    def execute(self) -> None:
        """
        Orquestra o ciclo de vida do ETL: Extracao -> Transformacao -> Carga
        """
        logger.info("Iniciando pipeline ETL para: %s", os.path.basename(self.output_path))

        # 1. Extracao e checagem
        try:
            gdf = self.extract()
        except Exception as e:
            logger.warning("Erro ao extrair dados: %s", e)
            return

        if gdf.empty:
            logger.warning("GeoJSON de entrada está vazio.")
            return

        # 2. Pre-processamento Global Geografico
        gdf = garantir_crs_4326(gdf)
        gdf = gdf[gdf.geometry.notna()].copy()

        if self.expected_geom_type:
            gdf = gdf[gdf.geometry.geom_type == self.expected_geom_type].copy()
            if gdf.empty:
                logger.warning("Nenhuma geometria válida do tipo %s encontrada.", self.expected_geom_type)
                return

        # 3. Transformacao (Delega para a Subclasse)
        try:
            df_final = self.transform(gdf)
        except Exception as e:
            logger.warning("Erro durante a transformação (.transform): %s", e)
            return

        if df_final is None or df_final.empty:
            logger.warning("Transformação resultou em um DataFrame vazio. Arquivo não será salvo.")
            return

        # 4. Carga (Load)
        try:
            salvar_csv(df_final, self.output_path)
            logger.info("Pipeline concluído com sucesso. Salvo em: %s (%s registros)", self.output_path, len(df_final))
        except Exception as e:
            logger.warning("Erro ao salvar arquivo CSV: %s", e)
