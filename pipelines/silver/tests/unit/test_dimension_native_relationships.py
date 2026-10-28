import geopandas as gpd
from shapely.geometry import Point, Polygon

from config.constants import NOT_INFORMED
from pipelines.silver.src.etl_dimensions import etl_dim_hospitais, etl_dim_terras_indigenas
from pipelines.silver.utils.keys import (
    normalizar_codigo_cnes,
    normalizar_codigo_ibge,
    normalizar_codigo_ibge_7digitos,
    normalizar_codigo_ti,
    normalizar_localidade,
    normalizar_uf,
)


def test_normalizacao_de_chaves_dimensionais():
    assert normalizar_codigo_ibge("3132404") == "313240"
    assert normalizar_codigo_ibge("313240") == "313240"
    assert normalizar_codigo_ibge("31") == NOT_INFORMED
    assert normalizar_codigo_ibge_7digitos("3132404") == "3132404"
    assert normalizar_codigo_cnes("0001234.0") == "0001234"
    assert normalizar_codigo_ti("123.0") == "123"
    assert normalizar_uf(" Minas Gerais ") == "MG"
    assert normalizar_uf("mg") == "MG"
    assert normalizar_localidade("São João (Distrito)!") == "SAO JOAO DISTRITO"


def test_hospital_recebe_codigo_ibge_municipio_por_intersecao(monkeypatch):
    hospitais = gpd.GeoDataFrame(
        {
            "codigo_ibge_cnes": ["999999"],
            "geometry": [Point(0.5, 0.5)],
        },
        crs="EPSG:4326",
    )
    municipios = gpd.GeoDataFrame(
        {
            "codigo_ibge": ["313240"],
            "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])],
        },
        crs="EPSG:4326",
    )

    monkeypatch.setattr(etl_dim_hospitais, "carregar_municipios_geo", lambda *_: municipios)

    resultado = etl_dim_hospitais.ETLDimHospitais()._adicionar_municipio_espacial(hospitais)

    assert resultado.loc[0, "codigo_ibge_municipio"] == "313240"
    assert resultado.loc[0, "codigo_ibge"] == "313240"
    assert resultado.loc[0, "match_status_municipio"] == "OK_ESPACIAL"


def test_hospital_recebe_terra_indigena_proxima(monkeypatch):
    hospitais = gpd.GeoDataFrame(
        {"geometry": [Point(0.5, 0.5)]},
        crs="EPSG:4326",
    )
    terras = gpd.GeoDataFrame(
        {
            "codigo_ti": ["TI1"],
            "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])],
        },
        crs="EPSG:4326",
    )

    monkeypatch.setattr(etl_dim_hospitais, "carregar_terras_indigenas_geo", lambda *_: terras)

    resultado = etl_dim_hospitais.ETLDimHospitais()._adicionar_terra_indigena_proxima(hospitais)

    assert resultado.loc[0, "codigo_ti_proxima"] == "TI1"
    assert resultado.loc[0, "distancia_ti_km"] == 0
    assert resultado.loc[0, "dentro_terra_indigena"] == 1


def test_terra_indigena_recebe_multivalue_de_municipios_interceptados(monkeypatch):
    municipios = gpd.GeoDataFrame(
        {
            "codigo_ibge": ["111111", "222222"],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)]),
                Polygon([(1, 0), (3, 0), (3, 2), (1, 2), (1, 0)]),
            ],
        },
        crs="EPSG:4326",
    )
    terras = gpd.GeoDataFrame(
        {
            "codigo_ti": ["TI1"],
            "geometry": [Polygon([(0, 0), (3, 0), (3, 2), (0, 2), (0, 0)])],
        },
        crs="EPSG:4326",
    )

    monkeypatch.setattr(etl_dim_terras_indigenas, "carregar_municipios_geo", lambda *_: municipios)

    rel = etl_dim_terras_indigenas.ETLDimTerrasIndigenas()._calcular_municipios_interceptados(terras)

    assert rel.loc[0, "codigos_ibge_interceptados"] == "222222|111111"
    assert rel.loc[0, "codigo_ibge_principal"] == "222222"
    assert rel.loc[0, "qtd_municipios_interceptados"] == 2
    assert rel.loc[0, "match_status_municipios"] == "OK_INTERSECAO"
