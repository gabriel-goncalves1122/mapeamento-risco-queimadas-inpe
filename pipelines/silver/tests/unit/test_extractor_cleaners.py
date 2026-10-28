import json

from config.constants import DEFAULT_EPOCH, NOT_INFORMED
from pipelines.silver.src.streaming_processing.processors.extractor import FogoExtractor
from pipelines.silver.utils.cleaners import gerar_chave_join, limpar_texto_druid, limpar_valor_numerico, limpar_wkt


def test_extractor_rejeita_coordenada_invalida():
    lat, lon, flag = FogoExtractor.extrair_coordenadas({"Latitude": "0", "Longitude": "0"})

    assert (lat, lon, flag) == (None, None, 0)


def test_extractor_gera_point_geojson_compacto():
    ponto = FogoExtractor.foco_point(-22.1234567, -45.7654321, 1)

    assert json.loads(ponto) == {
        "type": "Point",
        "coordinates": [-45.765432, -22.123457],
    }


def test_extractor_data_invalida_usa_epoch_padrao():
    assert FogoExtractor.extrair_data("sem data")["data_hora"] == DEFAULT_EPOCH


def test_cleaners_padronizam_texto_e_numero():
    assert limpar_texto_druid(" São João\n") == "SAO JOAO"
    assert limpar_texto_druid("") == NOT_INFORMED
    assert limpar_valor_numerico("-999") == 0.0


def test_limpar_valor_numerico_nullable_cobre_casos_sujos_do_inpe():
    casos_nulos = [None, "", " ", float("nan"), float("inf"), "-999", "texto"]

    for valor in casos_nulos:
        assert FogoExtractor.limpar_valor_numerico_nullable(valor) is None

    assert FogoExtractor.limpar_valor_numerico_nullable("12,5") == 12.5
    assert FogoExtractor.limpar_valor_numerico_nullable("7.25") == 7.25


def test_extrair_coordenadas_aceita_limites_geograficos_validos():
    assert FogoExtractor.extrair_coordenadas({"Latitude": "-90", "Longitude": "-180"}) == (-90.0, -180.0, 1)
    assert FogoExtractor.extrair_coordenadas({"Latitude": "90", "Longitude": "180"}) == (90.0, 180.0, 1)


def test_extrair_coordenadas_rejeita_fora_do_globo_e_texto():
    casos_invalidos = [
        {"Latitude": "-90.1", "Longitude": "0"},
        {"Latitude": "0", "Longitude": "180.1"},
        {"Latitude": "abc", "Longitude": "-45"},
    ]

    for linha in casos_invalidos:
        assert FogoExtractor.extrair_coordenadas(linha) == (None, None, 0)


def test_calcular_grids_normaliza_coordenada_valida_e_invalida():
    grids = FogoExtractor.calcular_grids(-22.123, -45.987, 1)

    assert grids == {
        "lat_grid_02": -22.2,
        "lon_grid_02": -46.0,
        "lat_grid_01": -22.2,
        "lon_grid_01": -46.0,
        "lat_grid_001": -22.13,
        "lon_grid_001": -45.99,
    }
    assert all(valor is None for valor in FogoExtractor.calcular_grids(None, None, 0).values())


def test_limpar_wkt_remove_quebras_sem_mudar_geometria():
    assert limpar_wkt("POINT (\n-45 -22\r)") == "POINT (-45 -22)"


def test_gerar_chave_join_remove_acentos_parenteses_e_especiais():
    assert gerar_chave_join("São João (1201) / Setor-2!") == "SAO JOAO"
