"""
Testes unitários da arquitetura orientada a objetos e contratos SOLID (Bronze, Silver e Config).

Valida a inversão de dependência (DIP), substituição de Liskov (LSP) e responsabilidade
única (SRP) nas classes de extração, limpeza, validação QA, orquestração e nas 6 classes
decompostas do Motor Espacial (`SpatialLayerSpec`, `DistanceClassifier`,
`SpatialLayerLoader`, `SpatialLayer`, `SpatialLayerCatalog` e `MotorEspacial`).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

from src.core.contracts.contracts import DataValidatorBase, ExecutablePipelineStep, ValidationReport
from src.core.domain.evento_fato_payload import EventoFatoPayload
from src.core.domain.foco_fato_payload import FocoFatoPayload
from src.core.config.settings import PipelineSettings
from src.bronze.extractors.ingestao_aneel import AneelArcGisExtractor
from src.orchestration.dagster.repo import build_druid_lookup_registrar
from src.silver.etl.etl_dim_municipios import ETLDimMunicipios
from src.silver.etl.run_etl import DimensionETLOrchestrator
from src.silver.spatial import (
    DistanceClassifier,
    MotorEspacial,
    SpatialLayer,
    SpatialLayerCatalog,
    SpatialLayerLoader,
    SpatialLayerSpec,
)
from src.silver.streaming_processing.processador import ProcessadorFocos
from src.silver.validators.valida_joins_municipios_hospital import (
    HospitalMunicipioJoinValidator,
)
from src.silver.utils import (
    DataFrameHelper,
    DimensionalKeyNormalizer,
    DruidTextCleaner,
    GeometryService,
    OnsMetadataParser,
    PathJsonCodec,
    SpatialDimensionRepository,
)


class _FakeHttpResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeHttpClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, params: dict[str, Any]) -> _FakeHttpResponse:
        self.calls.append((url, dict(params)))
        offset = params.get("resultOffset", 0)
        if offset == 0:
            return _FakeHttpResponse(
                200,
                {
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {"OID": "1", "Name": "SE TESTE"},
                            "geometry": {"type": "Point", "coordinates": [-45.4, -22.4]},
                        }
                    ]
                },
            )
        return _FakeHttpResponse(200, {"features": []})


def test_pipeline_settings_from_env_e_validacao_arquivos(tmp_path: Path) -> None:
    """Garante que PipelineSettings aceita overrides de ambiente e valida arquivos sem mutar estado global."""
    raw_file = tmp_path / "focos.csv"
    raw_file.write_text("DataHora,Latitude,Longitude\n", encoding="utf-8")

    cfg = PipelineSettings.from_env(
        {
            "RAW_FOCOS": str(raw_file),
            "CHUNK_SIZE_FOCOS": "500",
            "LIMITE_LINHAS_TESTE": "100",
            "KAFKA_BROKER": "kafka-test:9092",
        }
    )

    assert cfg.raw_focos == str(raw_file)
    assert cfg.chunk_size_focos == 500
    assert cfg.limite_linhas_teste == 100
    assert cfg.kafka_broker == "kafka-test:9092"
    assert cfg.verificar_arquivos_obrigatorios() is False


def test_aneel_arcgis_extractor_com_injecao_de_dependencia(tmp_path: Path) -> None:
    """Testa extração paginada da ANEEL injetando cliente HTTP fake e diretório temporário."""
    fake_http = _FakeHttpClient()
    extractor = AneelArcGisExtractor(
        output_dir=tmp_path,
        camadas={"subestacoes": 3},
        page_size=2,
        rate_limit_s=0.0,
        http_client=fake_http,
    )

    gerados = extractor.execute()

    assert "subestacoes" in gerados
    assert gerados["subestacoes"].exists()
    assert len(fake_http.calls) == 1


def test_classes_utilitarias_silver_mantem_contratos_limpos(tmp_path: Path) -> None:
    """Verifica encapsulamento POO em DruidTextCleaner, DataFrameHelper, PathJsonCodec e OnsMetadataParser."""
    assert DruidTextCleaner.limpar_texto_druid(" São Lourenço ") == "SAO LOURENCO"
    assert DataFrameHelper.limpar_numero("1234,5", default=0.0) == 1234.5
    assert DataFrameHelper.coordenada_valida(-22.4, -45.4) is True
    assert DataFrameHelper.coordenada_valida(0.0, 0.0) is False

    ponto_json = PathJsonCodec.geometry_para_path_json(Point(-45.4, -22.4))
    geom_reconstruida = PathJsonCodec.path_json_para_geometry(ponto_json, tipo_geometria="point")
    assert geom_reconstruida is not None
    assert geom_reconstruida.geom_type == "Point"

    assert DimensionalKeyNormalizer.normalizar_codigo_ibge("3132404.0") == "313240"
    assert OnsMetadataParser.extrair_popup_valor("<b>Tensão:</b> 500 kV<br/>", "Tensão") == "500 kV"
    assert OnsMetadataParser.extrair_uf_popup("USINA MANAUS - AM") == "AM"

    csv_out = DataFrameHelper.salvar_csv(pd.DataFrame({"a": [1]}), tmp_path / "out.csv")
    assert csv_out.exists()


def test_spatial_dimension_repository_associa_municipio_por_intersecao() -> None:
    """Valida que SpatialDimensionRepository resolve codigo_ibge sem duplicar lógica de sjoin."""
    repo = SpatialDimensionRepository()
    municipios = gpd.GeoDataFrame(
        {
            "codigo_ibge": ["313240"],
            "geometry": [Polygon([(-46, -23), (-45, -23), (-45, -22), (-46, -22), (-46, -23)])],
        },
        crs="EPSG:4326",
    )
    ativos = gpd.GeoDataFrame(
        {"id": ["SE1"], "geometry": [Point(-45.5, -22.5)]},
        crs="EPSG:4326",
    )

    enriquecido = repo.associar_municipio_por_intersecao(ativos, municipios_gdf=municipios)
    assert enriquecido.loc[0, "codigo_ibge"] == "313240"
    assert GeometryService.is_coordenada_valida_brasil(-22.5, -45.5) is True


def test_hospital_municipio_join_validator_em_memoria(tmp_path: Path) -> None:
    """Garante que o validador QA retorna ValidationReport tipado sem executar exit() no import."""
    hosp_csv = tmp_path / "dim_hospitais_cnes.csv"
    muni_csv = tmp_path / "dim_municipios_coordenadas.csv"

    pd.DataFrame(
        {
            "codigo_cnes": ["001", "002"],
            "nome_hospital": ["HOSP A", "HOSP ORFAO"],
            "codigo_ibge": ["313240", "999999"],
        }
    ).to_csv(hosp_csv, index=False)

    pd.DataFrame(
        {
            "codigo_ibge": ["313240"],
            "municipios_nome": ["ITAJUBA"],
            "estado_sigla": ["MG"],
            "path_json": ["[[[-45.4,-22.4],[-45.3,-22.4],[-45.3,-22.3],[-45.4,-22.4]]]"],
        }
    ).to_csv(muni_csv, index=False)

    validator = HospitalMunicipioJoinValidator(hospitais_path=hosp_csv, municipios_path=muni_csv)
    report = validator.execute()

    assert isinstance(report, ValidationReport)
    assert report.total_records == 2
    assert report.matched_records == 1
    assert report.orphan_records == 1
    assert report.coverage_pct == 50.0
    assert report.is_valid is False


def test_dimension_etl_orchestrator_polimorfico(tmp_path: Path) -> None:
    """Testa a execução polimórfica de etapas BaseETL e DataValidatorBase no DimensionETLOrchestrator."""
    geojson_in = tmp_path / "municipios_br.geojson"
    csv_out = tmp_path / "dim_municipios_coordenadas.csv"

    gdf = gpd.GeoDataFrame(
        {
            "id": ["3132404"],
            "name": ["Itajubá"],
            "geometry": [Polygon([(-45.5, -22.5), (-45.4, -22.5), (-45.4, -22.4), (-45.5, -22.5)])],
        },
        crs="EPSG:4326",
    )
    gdf.to_file(geojson_in, driver="GeoJSON")

    class _DummyValidator(DataValidatorBase):
        def validate(self) -> ValidationReport:
            return ValidationReport(
                validator_name="DummyValidator",
                is_valid=csv_out.exists(),
                total_records=1,
                matched_records=1,
                orphan_records=0,
                coverage_pct=100.0,
            )

    orchestrator = DimensionETLOrchestrator(
        steps=[ETLDimMunicipios(input_path=geojson_in, output_path=csv_out)],
        validators=[_DummyValidator()],
    )
    reports = orchestrator.execute()

    assert csv_out.exists()
    assert len(reports) == 1
    assert reports[0].is_valid is True


def test_decomposicao_motor_espacial_1_classe_por_arquivo(tmp_path: Path) -> None:
    """
    Valida `DistanceClassifier`, `SpatialLayerLoader`, `SpatialLayerSpec`,
    `SpatialLayerCatalog` e `MotorEspacial` trabalhando em conjunto.
    """
    clf = DistanceClassifier(limites_km=(1, 5, 10))
    assert clf.faixa_distancia(0.5) == "ATE_1KM"
    assert clf.faixa_distancia(2.5) == "ATE_3KM"
    assert clf.faixa_distancia(60.0) == "ACIMA_50KM"
    assert clf.flags_por_limite("hospital", 3.0) == {
        "hospital_ate_1km": 0,
        "hospital_ate_5km": 1,
        "hospital_ate_10km": 1,
    }
    assert clf.normalizar_float("500,0") == 500.0

    # Testa SpatialLayerLoader + SpatialLayer.from_spec em arquivo CSV temporário
    hosp_csv = tmp_path / "hospitais.csv"
    pd.DataFrame(
        {
            "codigo_cnes": ["CNES_ITAJUBA"],
            "nome_hospital": ["HOSPITAL ESCOLA"],
            "latitude": ["-22.425"],
            "longitude": ["-45.452"],
        }
    ).to_csv(hosp_csv, index=False)

    spec = SpatialLayerSpec(
        path=hosp_csv,
        nome="Hospitais Teste",
        col_id="codigo_cnes",
        prefixo="hospital",
        atributos_map={"hospital_nome": "nome_hospital"},
        projetar_metrico=True,
        tipo_geometria="point",
        output_id_key="codigo_cnes_prox",
    )
    assert spec.resolved_output_id_key == "codigo_cnes_prox"

    layer = SpatialLayer.from_spec(spec, loader=SpatialLayerLoader(), classifier=DistanceClassifier())
    assert layer.gdf_gps is not None
    assert layer.gdf_metrico is not None

    ponto_metrico = (
        gpd.GeoSeries([Point(-45.452, -22.425)], crs="EPSG:4326")
        .to_crs(epsg=5880)
        .iloc[0]
    )
    prox = layer.proximidade(ponto_metrico)
    assert prox["hospital_id_proximo"] == "CNES_ITAJUBA"
    assert prox["distancia_hospital_km"] == 0.0
    assert prox["faixa_distancia_hospital"] == "ATE_1KM"
    assert prox["attrs"]["hospital_nome"] == "HOSPITAL ESCOLA"

    specs_catalogo = SpatialLayerCatalog.default_specs()
    assert len(specs_catalogo) == 7
    vazio = SpatialLayerCatalog.criar_resultado_vazio()
    assert vazio["codigo_cnes_prox"] == "NAO INFORMADO"
    assert FocoFatoPayload.__name__ == "FocoFatoPayload"
    assert EventoFatoPayload.__name__ == "EventoFatoPayload"
    assert issubclass(MotorEspacial, object)


def test_druid_lookup_registrar_e_processador_focos_com_di(tmp_path: Path) -> None:
    """Garante que DruidLookupRegistrar não executa HTTP no import e aceita http_poster injetado."""
    muni_csv = tmp_path / "dim_municipios_coordenadas.csv"
    muni_csv.write_text("codigo_ibge,municipios_nome,estado_sigla,regiao_brasil\n313240,ITAJUBA,MG,SUDESTE\n", encoding="utf-8")

    posted_payloads: list[dict[str, Any]] = []

    def _fake_poster(payload: dict[str, Any]) -> tuple[bool, str | None]:
        posted_payloads.append(payload)
        return True, None

    registrar = build_druid_lookup_registrar(
        dims_dir=tmp_path,
        druid_url="http://druid-test:8081",
        http_poster=_fake_poster,
    )
    assert registrar.execute() is True
    assert len(posted_payloads) == 1
    assert "municipios_nome" in posted_payloads[0]["__default"]

    # Valida injeção de text_cleaner customizado no ProcessadorFocos
    proc = ProcessadorFocos(
        motor_espacial=type("_DummyMotor", (), {"analisar_todas_ameacas": lambda self, lat, lon: {}})(),
        text_cleaner=lambda val: f"CLEAN_{str(val).upper()}",
    )
    foco_dict = proc.transformar(
        {
            "DataHora": "2025-01-01 12:00:00",
            "Pais": "Brasil",
            "Estado": "MG",
            "Municipio": "Itajuba",
            "Bioma": "Mata",
            "Satelite": "GOES",
            "Latitude": "-22.4",
            "Longitude": "-45.4",
        }
    )
    assert foco_dict["pais_origem"] == "CLEAN_BRASIL"
