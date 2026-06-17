import json

import pandas as pd
from shapely.geometry import GeometryCollection, LineString, MultiLineString, Point, Polygon

from src.config.constants import GEOMETRY_WKT_COLUMN, PATH_JSON_COLUMN
from src.etl.utils.geo_helpers import geometry_para_path_json, limpar_linestring_geometry
from src.spatial.layers import SpatialLayer


def test_geometry_para_path_json_para_point_e_linestring():
    assert json.loads(geometry_para_path_json(Point(-45.1, -22.2))) == [[-45.1, -22.2]]
    assert json.loads(geometry_para_path_json(LineString([(0, 0), (1.2345678, 2)]))) == [
        [0.0, 0.0],
        [1.234568, 2.0],
    ]


def test_spatial_layer_aceita_wkt_como_geometria_tecnica(tmp_path):
    csv_path = tmp_path / "dim.csv"
    pd.DataFrame(
        {
            "id": ["A"],
            GEOMETRY_WKT_COLUMN: ["POINT (-45.1 -22.2)"],
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
