import os
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.etl.utils.base import BaseETL

class DummyETL(BaseETL):
    """
    Implementação concreta mínima para teste de integração leve.
    """
    def transform(self, gdf):
        gdf['transformado'] = True
        return pd.DataFrame(gdf.drop(columns=['geometry']))

@pytest.fixture
def dummy_geojson(tmp_path):
    """
    Cria um GeoJSON falso para testar o carregamento base.
    """
    file_path = os.path.join(tmp_path, "dummy.geojson")
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "nome": ["A", "B"]},
        geometry=[Point(0, 0), Point(1, 1)],
        crs="EPSG:4326"
    )
    gdf.to_file(file_path, driver="GeoJSON")
    return file_path

@pytest.fixture
def dummy_output(tmp_path):
    return os.path.join(tmp_path, "saida.csv")

def test_base_etl_transformacao_sucesso(dummy_geojson, dummy_output):
    """
    Testa se o ciclo de vida do BaseETL carrega, transforma e salva
    sem levantar exceções, removendo o boilerplate padrão.
    """
    etl = DummyETL(input_path=dummy_geojson, output_path=dummy_output, expected_geom_type="Point")
    etl.execute()

    assert os.path.exists(dummy_output), "BaseETL não salvou o arquivo CSV."
    
    df_salvo = pd.read_csv(dummy_output)
    assert 'transformado' in df_salvo.columns, "O método transform() não foi chamado corretamente."
    assert len(df_salvo) == 2, "Quantidade de linhas incorreta após o pipeline."

def test_base_etl_arquivo_nao_encontrado(dummy_output):
    """
    Testa a blindagem de falha caso o arquivo GeoJSON não exista.
    Não deve crachar a orquestração do Dagster.
    """
    etl = DummyETL(input_path="caminho/invalido.geojson", output_path=dummy_output)
    
    # Executa e verifica se não lança exceção (fail-safe)
    try:
        etl.execute()
    except Exception as e:
        pytest.fail(f"O BaseETL deve engolir erros de FileNotFound suavemente. Erro: {e}")
    
    assert not os.path.exists(dummy_output)
