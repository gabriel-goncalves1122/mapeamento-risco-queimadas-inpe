import csv
import json
from pathlib import Path

from config.constants import PROJECT_ROOT, DIMENSIONS_DIR, SILVER_DIR
from config.domain.models import EventoFatoPayload, FocoFatoPayload

# Colunas geradas exclusivamente pelo transformSpec do Druid (não existem no Pydantic)
DRUID_GENERATED_COLS = {"sample_bucket"}


DIMENSION_SPECS = {
    "dim_hospitais_cnes.json": "dim_hospitais_cnes.csv",
    "dim_municipios_coordenadas.json": "dim_municipios_coordenadas.csv",
    "dim_ons_linhas_transmissao.json": "dim_ons_linhas_transmissao.csv",
    "dim_ons_sistemas_isolados.json": "dim_ons_sistemas_isolados.csv",
    "dim_ons_subestacoes.json": "dim_ons_subestacoes.csv",
    "dim_rodovias_federais.json": "dim_rodovias_federais.csv",
    "dim_terras_indigenas_funai.json": "dim_terras_indigenas.csv",
}

BATCH_FACT_SPECS = {
    "fogo_eventos_stdbscan.json": ("fatos", "fogo_eventos_stdbscan.csv"),
}


def _spec_dimensions(path: Path):
    spec = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["name"]
        for item in spec["spec"]["dataSchema"]["dimensionsSpec"]["dimensions"]
    }


def _load_spec(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_header(path: Path):
    with path.open(encoding="utf-8", newline="") as fp:
        return set(next(csv.reader(fp)))


def test_specs_druid_de_dimensoes_referenciam_apenas_colunas_existentes():
    specs_dir = PROJECT_ROOT / "infrastructure" / "druid" / "specs"
    dimensions_dir = DIMENSIONS_DIR

    for spec_name, csv_name in DIMENSION_SPECS.items():
        spec_cols = _spec_dimensions(specs_dir / spec_name)
        csv_cols = _csv_header(dimensions_dir / csv_name)

        assert "geometria_wkt" not in spec_cols
        assert spec_cols.issubset(csv_cols), f"{spec_name} referencia colunas ausentes: {spec_cols - csv_cols}"


def test_specs_druid_de_fatos_batch_referenciam_apenas_colunas_existentes():
    specs_dir = PROJECT_ROOT / "infrastructure" / "druid" / "specs"
    gold_dir = Path(__file__).resolve().parent.parent.parent.parent / "pipelines" / "gold" / "data"

    for spec_name, (subdir, csv_name) in BATCH_FACT_SPECS.items():
        spec = _load_spec(specs_dir / spec_name)
        spec_cols = _spec_dimensions(specs_dir / spec_name)
        csv_cols = _csv_header(gold_dir / subdir / csv_name)
        timestamp_col = spec["spec"]["dataSchema"]["timestampSpec"]["column"]

        assert "geometria_wkt" not in spec_cols
        assert timestamp_col in csv_cols
        assert spec_cols.issubset(csv_cols), f"{spec_name} referencia colunas ausentes: {spec_cols - csv_cols}"


def test_spec_druid_da_fato_reflete_payload_pydantic_enxuto():
    spec_cols = _spec_dimensions(PROJECT_ROOT / "infrastructure" / "druid" / "specs" / "fato_focos_incendio.json")
    payload_cols = set(FocoFatoPayload.model_fields) - {"data_hora"}

    assert "geometria_wkt" not in spec_cols
    assert spec_cols - DRUID_GENERATED_COLS == payload_cols


def test_spec_druid_da_fato_de_eventos_usa_kafka_e_payload_pydantic():
    spec = _load_spec(PROJECT_ROOT / "infrastructure" / "druid" / "specs" / "fato_eventos_incendio.json")
    spec_cols = _spec_dimensions(PROJECT_ROOT / "infrastructure" / "druid" / "specs" / "fato_eventos_incendio.json")
    payload_cols = set(EventoFatoPayload.model_fields) - {"data_inicio"}

    assert spec["type"] == "kafka"
    assert spec["spec"]["ioConfig"]["type"] == "kafka"
    assert "inputSource" not in spec["spec"]["ioConfig"]
    assert spec["spec"]["ioConfig"]["topic"] == "streaming_eventos_incendio"
    assert spec["spec"]["dataSchema"]["dataSource"] == "fato_eventos_incendio"
    assert spec["spec"]["dataSchema"]["timestampSpec"]["column"] == "data_inicio"
    assert spec["spec"]["ioConfig"]["taskDuration"] == "PT15M"
    assert spec["spec"]["tuningConfig"]["intermediatePersistPeriod"] == "PT5M"
    assert "geometria_wkt" not in spec_cols
    assert spec_cols - DRUID_GENERATED_COLS == payload_cols


def test_granularidade_druid_evita_tiny_segments_nas_fatos_e_usa_all_nas_dimensoes():
    specs_dir = PROJECT_ROOT / "infrastructure" / "druid" / "specs"

    for spec_name in DIMENSION_SPECS:
        spec = _load_spec(specs_dir / spec_name)
        assert spec["spec"]["dataSchema"]["granularitySpec"]["segmentGranularity"] == "ALL"

    fato_streaming = _load_spec(specs_dir / "fato_focos_incendio.json")
    fato_eventos = _load_spec(specs_dir / "fato_eventos_incendio.json")
    eventos_batch = _load_spec(specs_dir / "fogo_eventos_stdbscan.json")

    assert fato_streaming["spec"]["dataSchema"]["granularitySpec"]["segmentGranularity"] == "DAY"
    assert fato_eventos["spec"]["dataSchema"]["granularitySpec"]["segmentGranularity"] == "DAY"
    assert fato_eventos["spec"]["dataSchema"]["granularitySpec"]["queryGranularity"] == "NONE"
    assert eventos_batch["spec"]["dataSchema"]["granularitySpec"]["segmentGranularity"] == "MONTH"
    assert fato_streaming["spec"]["tuningConfig"]["maxRowsPerSegment"] >= 3000000
    assert fato_eventos["spec"]["tuningConfig"]["maxRowsPerSegment"] >= 3000000
    assert eventos_batch["spec"]["tuningConfig"]["maxRowsPerSegment"] >= 3000000


def test_specs_druid_refletem_relacoes_dimensionais_nativas():
    specs_dir = PROJECT_ROOT / "infrastructure" / "druid" / "specs"

    hospitais_cols = _spec_dimensions(specs_dir / "dim_hospitais_cnes.json")
    terras_spec = _load_spec(specs_dir / "dim_terras_indigenas_funai.json")
    terras_cols = _spec_dimensions(specs_dir / "dim_terras_indigenas_funai.json")
    terras_dims = terras_spec["spec"]["dataSchema"]["dimensionsSpec"]["dimensions"]
    codigos_dim = next(item for item in terras_dims if item["name"] == "codigos_ibge_interceptados")

    assert {
        "codigo_ibge",
        "codigo_ti_proxima",
        "distancia_ti_km",
    }.issubset(hospitais_cols)
    assert {
        "codigos_ibge_interceptados",
        "codigo_ibge_principal",
        "qtd_municipios_interceptados",
        "percentual_area_interceptada",
    }.issubset(terras_cols)
    assert terras_spec["spec"]["ioConfig"]["inputFormat"]["listDelimiter"] == "|"
    assert codigos_dim["multiValueHandling"] == "SORTED_SET"
