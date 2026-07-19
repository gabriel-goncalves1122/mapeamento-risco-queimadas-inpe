import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import GeometryCollection, LineString, MultiLineString, Point, Polygon

from src.config.constants import PATH_JSON_COLUMN
from src.etl.utils.geo_helpers import geometry_para_path_json, limpar_linestring_geometry
from src.science.network_builder import path_json_para_linhas
from src.spatial.layers import SpatialLayer


def test_geometry_para_path_json_para_point_e_linestring():
    assert json.loads(geometry_para_path_json(Point(-45.1, -22.2))) == [[-45.1, -22.2]]
    assert json.loads(geometry_para_path_json(LineString([(0, 0), (1.2345678, 2)]))) == [
        [0.0, 0.0],
        [1.234568, 2.0],
    ]


def test_spatial_layer_reconstroi_point_de_path_json(tmp_path):
    csv_path = tmp_path / "dim.csv"
    pd.DataFrame(
        {
            "id": ["A"],
            PATH_JSON_COLUMN: ['[[-45.1,-22.2]]'],
        }
    ).to_csv(csv_path, index=False)

    camada = SpatialLayer(
        path=csv_path,
        nome="Teste",
        col_id="id",
        prefixo="teste",
        atributos_map={},
        projetar_metrico=True,
        tipo_geometria="point",
    )

    assert camada.gdf_gps is not None
    assert len(camada.gdf_gps) == 1
    assert camada.gdf_gps.iloc[0].geometry.wkt == "POINT (-45.1 -22.2)"


def test_geometry_para_path_json_para_polygon_multiline_e_vazio():
    poligono = Polygon([(0, 0), (1.2345678, 0), (1, 1), (0, 0)])
    multilinha = MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3.3333339, 3)]])

    assert json.loads(geometry_para_path_json(poligono)) == [
        [[0.0, 0.0], [1.234568, 0.0], [1.0, 1.0], [0.0, 0.0]]
    ]
    assert json.loads(geometry_para_path_json(multilinha)) == [
        [[0.0, 0.0], [1.0, 1.0]],
        [[2.0, 2.0], [3.333334, 3.0]],
    ]
    assert geometry_para_path_json(GeometryCollection()) == "[]"


def test_limpar_linestring_geometry_remove_duplicados_e_descarta_linha_invalida():
    linha = LineString([(0, 0), (0, 0), (1, 1), (1, 1), (2, 2)])
    limpa = limpar_linestring_geometry(linha)

    assert list(limpa.coords) == [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
    assert limpar_linestring_geometry(LineString([(0, 0), (0, 0)])) is None


def test_spatial_layer_filtra_lat_lon_invalidas_e_normaliza_atributo_numerico(tmp_path):
    csv_path = tmp_path / "dim_latlon.csv"
    pd.DataFrame(
        {
            "id": ["ok", "lat_invalida", "zero_zero"],
            "latitude": ["-22.5", "95", "0"],
            "longitude": ["-45.5", "-45", "0"],
            "capacidade_mw": ["12,5", "99", "88"],
        }
    ).to_csv(csv_path, index=False)

    camada = SpatialLayer(
        path=csv_path,
        nome="LatLon",
        col_id="id",
        prefixo="ativo",
        atributos_map={"ativo_capacidade_mw": "capacidade_mw"},
        projetar_metrico=True,
    )

    assert camada.gdf_gps is not None
    assert camada.gdf_gps["id"].tolist() == ["ok"]

    resultado = camada.proximidade(camada.gdf_metrico.iloc[0].geometry)
    assert resultado["ativo_id_proximo"] == "ok"
    assert resultado["attrs"]["ativo_capacidade_mw"] == 12.5


def test_spatial_layer_intersecao_reconstroi_polygon_de_path_json(tmp_path):
    csv_path = tmp_path / "dim_polygon.csv"
    poligono = Polygon([(-46, -23), (-44, -23), (-44, -21), (-46, -21), (-46, -23)])
    pd.DataFrame(
        {
            "id": ["MUN_1"],
            "nome": ["MUNICIPIO TESTE"],
            PATH_JSON_COLUMN: [geometry_para_path_json(poligono)],
        }
    ).to_csv(csv_path, index=False)

    camada = SpatialLayer(
        path=csv_path,
        nome="Municipio",
        col_id="id",
        prefixo="municipio",
        atributos_map={"municipio_nome": "nome"},
        tipo_geometria="polygon",
    )

    resultado = camada.intersecao(Point(-45, -22))

    assert resultado["id"] == "MUN_1"
    assert resultado["flag"] == 1
    assert resultado["attrs"]["municipio_nome"] == "MUNICIPIO TESTE"


def test_spatial_layer_proximidade_reconstroi_linha_real_de_path_json(tmp_path):
    csv_path = tmp_path / "dim_linha.csv"
    linha = LineString([(-45, -22), (-45, -23)])
    pd.DataFrame(
        {
            "id": ["LT_1"],
            "tensao_kv": ["500,0"],
            PATH_JSON_COLUMN: [geometry_para_path_json(linha)],
        }
    ).to_csv(csv_path, index=False)

    camada = SpatialLayer(
        path=csv_path,
        nome="Linha",
        col_id="id",
        prefixo="linha",
        atributos_map={"linha_tensao_kv": "tensao_kv"},
        projetar_metrico=True,
        tipo_geometria="line",
    )
    ponto_metrico = gpd.GeoSeries([Point(-45, -22)], crs="EPSG:4326").to_crs(epsg=5880).iloc[0]

    resultado = camada.proximidade(ponto_metrico)

    assert resultado["linha_id_proximo"] == "LT_1"
    assert resultado["distancia_linha_km"] == 0
    assert resultado["attrs"]["linha_tensao_kv"] == 500.0


def test_network_builder_reconstroi_linhas_de_path_json():
    linha = LineString([(-45, -22), (-45, -23)])
    geom = path_json_para_linhas(geometry_para_path_json(linha))

    assert geom.geom_type == "LineString"
    assert list(geom.coords) == [(-45.0, -22.0), (-45.0, -23.0)]
