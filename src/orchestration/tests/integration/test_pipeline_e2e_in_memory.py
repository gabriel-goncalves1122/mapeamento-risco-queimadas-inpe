"""
Teste de Integração Ponta-a-Ponta Sintético em Memória (E2E).

Percorre o ciclo de vida analítico completo da Arquitetura Medalhão sem qualquer
dependência de containers externos (Docker/Kafka/Druid) em menos de 3 segundos:
1. Bronze: Extração atômica via `InpeQueimadasExtractor` com HTTP mockado.
2. Silver: ETLs de dimensões, validação de QA com `DimensionIntegrityValidator` e montagem do `MotorEspacial`.
3. Gold: Transformação e enriquecimento de fatos via `ProcessadorFocos` e clusterização via `EventizadorIncendios`.
4. Contratos: Validação estrita dos payloads Snowflake (`FocoFatoPayload` e `EventoFatoPayload`).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, Polygon

from src.bronze.extractors.inpe_queimadas_extractor import InpeQueimadasExtractor
from src.core.contracts.contracts import StreamPublisherBase
from src.core.domain.evento_fato_payload import EventoFatoPayload
from src.core.domain.foco_fato_payload import FocoFatoPayload
from src.gold.science.dbscan.eventizador import EventizadorIncendios
from src.gold.science.dbscan.evento_config import EventoConfig
from src.silver.etl.etl_dim_municipios import ETLDimMunicipios
from src.silver.spatial import DistanceClassifier, MotorEspacial, SpatialLayer, SpatialLayerLoader, SpatialLayerSpec
from src.silver.streaming_processing.processador import ProcessadorFocos
from src.silver.utils.path_json_codec import PathJsonCodec
from src.silver.validators.dimensao_integridade_validator import DimensionIntegrityValidator


class _InMemoryStreamPublisher(StreamPublisherBase):
    """Produtor de mensagens em memória para auditoria de payloads."""

    def __init__(self) -> None:
        self.publicados: list[tuple[str, dict]] = []
        self.flushed = False
        self.closed = False

    def enviar(self, topico: str, payload: dict) -> None:
        self.publicados.append((topico, payload))

    def flush(self) -> None:
        self.flushed = True

    def flush_and_close(self) -> None:
        self.flushed = True
        self.closed = True


def test_pipeline_completo_medallion_e2e_in_memory(tmp_path: Path) -> None:
    """Valida o fluxo Medalhão ponta-a-ponta (Bronze -> Silver -> Gold) com dados sintéticos."""
    bronze_dir = tmp_path / "bronze" / "inpe"
    silver_dims_dir = tmp_path / "silver" / "dimensions"
    silver_dims_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. CAMADA BRONZE: Ingestão de Focos Brutos via InpeQueimadasExtractor
    # -------------------------------------------------------------------------
    csv_raw_content = (
        "DataHora,Satelite,Pais,Estado,Municipio,Bioma,DiaSemChuva,Precipitacao,RiscoFogo,FRP,Latitude,Longitude\n"
        "2024-09-15 12:00:00,AQUA_M-T,Brasil,MG,Itajuba,Mata Atlantica,15,0.0,0.85,35.0,-22.425,-45.452\n"
        "2024-09-15 12:05:00,AQUA_M-T,Brasil,MG,Itajuba,Mata Atlantica,15,0.0,0.90,40.0,-22.426,-45.451\n"
        "2024-09-15 12:10:00,AQUA_M-T,Brasil,MG,Itajuba,Mata Atlantica,15,0.0,0.88,38.0,-22.424,-45.453\n"
    ).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content.return_value = [csv_raw_content]
    mock_http = MagicMock()
    mock_http.get.return_value = mock_resp

    bronze_extractor = InpeQueimadasExtractor(
        output_dir=bronze_dir,
        modo="diario",
        data_ref="20240915",
        http_client=mock_http,
    )
    raw_csv_path = bronze_extractor.execute()
    assert raw_csv_path.exists()
    assert raw_csv_path.stat().st_size > 0

    # -------------------------------------------------------------------------
    # 2. CAMADA SILVER: Materialização das Dimensões Espaciais & QA
    # -------------------------------------------------------------------------
    # Cria GeoJSON sintético de Municípios (Itajubá cobrindo -45.45, -22.42)
    muni_geojson = tmp_path / "geo_municipios.geojson"
    gdf_muni = gpd.GeoDataFrame(
        {
            "id": ["3132404"],
            "name": ["Itajubá"],
            "geometry": [Polygon([(-45.50, -22.45), (-45.40, -22.45), (-45.40, -22.40), (-45.50, -22.40)])],
        },
        crs="EPSG:4326",
    )
    gdf_muni.to_file(muni_geojson, driver="GeoJSON")

    # Executa ETL de Municípios (GeoJSON -> CSV Dimensional em path_json)
    muni_csv = silver_dims_dir / "dim_municipios_coordenadas.csv"
    etl_muni = ETLDimMunicipios(input_path=muni_geojson, output_path=muni_csv)
    etl_muni.execute()
    assert muni_csv.exists()

    # Prepara geometrias Shapely para serialização path_json
    p_hosp = Point(-45.452, -22.425)
    poly_ti = Polygon([(-45.40, -22.40), (-45.35, -22.40), (-45.35, -22.35), (-45.40, -22.40)])
    line_lt = LineString([(-45.46, -22.43), (-45.40, -22.40)])
    line_br = LineString([(-45.47, -22.44), (-45.43, -22.41)])

    # Gera arquivos com FKs e path_json compatíveis com Deck.gl / Druid
    pd.DataFrame(
        {
            "codigo_cnes": ["CNES_ITAJUBA_01"],
            "nome_hospital": ["Hospital Escola Itajubá"],
            "codigo_ibge": ["313240"],
            "latitude": ["-22.425"],
            "longitude": ["-45.452"],
            "path_json": [PathJsonCodec.geometry_para_path_json(p_hosp)],
        }
    ).to_csv(silver_dims_dir / "dim_hospitais_cnes.csv", index=False)

    pd.DataFrame(
        {
            "codigo_ti": ["TI_01"],
            "nome_terra_indigena": ["TI Sul de Minas"],
            "path_json": [PathJsonCodec.geometry_para_path_json(poly_ti)],
        }
    ).to_csv(silver_dims_dir / "dim_terras_indigenas.csv", index=False)

    pd.DataFrame(
        {
            "id_linha_transmissao": ["LT_01"],
            "nome_linha": ["LT 500kV Itajubá"],
            "path_json": [PathJsonCodec.geometry_para_path_json(line_lt)],
        }
    ).to_csv(silver_dims_dir / "dim_ons_linhas_transmissao.csv", index=False)

    pd.DataFrame(
        {
            "id_subestacao": ["SE_01"],
            "nome_subestacao": ["SE Itajubá"],
            "codigo_ibge": ["313240"],
            "latitude": ["-22.42"],
            "longitude": ["-45.45"],
            "path_json": [PathJsonCodec.geometry_para_path_json(Point(-45.45, -22.42))],
        }
    ).to_csv(silver_dims_dir / "dim_ons_subestacoes.csv", index=False)

    pd.DataFrame(
        {
            "id_sistema_isolado": ["SIS_01"],
            "nome_sistema_isolado": ["SIS Sul"],
            "latitude": ["-22.41"],
            "longitude": ["-45.44"],
            "path_json": [PathJsonCodec.geometry_para_path_json(Point(-45.44, -22.41))],
        }
    ).to_csv(silver_dims_dir / "dim_ons_sistemas_isolados.csv", index=False)

    pd.DataFrame(
        {
            "id_trecho_rodoviario": ["BR_01"],
            "codigo_rodovia": ["BR-459"],
            "path_json": [PathJsonCodec.geometry_para_path_json(line_br)],
        }
    ).to_csv(silver_dims_dir / "dim_rodovias_federais.csv", index=False)

    # Validação QA de Integridade Dimensional
    validator = DimensionIntegrityValidator(dimensions_dir=silver_dims_dir)
    report = validator.execute()
    assert report.is_valid is True
    assert report.orphan_records == 0

    # -------------------------------------------------------------------------
    # 3. CAMADA GOLD: Enriquecimento Espacial via MotorEspacial & ProcessadorFocos
    # -------------------------------------------------------------------------
    test_specs = {
        "camada_municipios": SpatialLayerSpec(
            path=muni_csv,
            nome="Municípios",
            col_id="codigo_ibge",
            prefixo="municipio",
            atributos_map={"municipio_nome": "municipios_nome"},
            tipo_geometria="polygon",
            output_id_key="codigo_ibge_espacial",
        ),
        "camada_hospitais": SpatialLayerSpec(
            path=silver_dims_dir / "dim_hospitais_cnes.csv",
            nome="Hospitais",
            col_id="codigo_cnes",
            prefixo="hospital",
            atributos_map={"hospital_nome": "nome_hospital"},
            projetar_metrico=True,
            tipo_geometria="point",
            output_id_key="codigo_cnes_prox",
        ),
        "camada_funai": SpatialLayerSpec(
            path=silver_dims_dir / "dim_terras_indigenas.csv",
            nome="FUNAI",
            col_id="codigo_ti",
            prefixo="terra_indigena",
            atributos_map={},
            projetar_metrico=True,
            tipo_geometria="polygon",
            output_id_key="codigo_ti_proxima",
        ),
        "camada_linhas": SpatialLayerSpec(
            path=silver_dims_dir / "dim_ons_linhas_transmissao.csv",
            nome="Linhas",
            col_id="id_linha_transmissao",
            prefixo="linha",
            atributos_map={},
            projetar_metrico=True,
            tipo_geometria="line",
            output_id_key="id_linha_transmissao",
        ),
        "camada_subestacoes": SpatialLayerSpec(
            path=silver_dims_dir / "dim_ons_subestacoes.csv",
            nome="Subestações",
            col_id="id_subestacao",
            prefixo="subestacao",
            atributos_map={},
            projetar_metrico=True,
            tipo_geometria="point",
            output_id_key="id_subestacao",
        ),
        "camada_sistemas": SpatialLayerSpec(
            path=silver_dims_dir / "dim_ons_sistemas_isolados.csv",
            nome="Sistemas Isolados",
            col_id="id_sistema_isolado",
            prefixo="sistema_isolado",
            atributos_map={},
            projetar_metrico=True,
            tipo_geometria="point",
            output_id_key="id_sistema_isolado",
        ),
        "camada_rodovias": SpatialLayerSpec(
            path=silver_dims_dir / "dim_rodovias_federais.csv",
            nome="Rodovias",
            col_id="id_trecho_rodoviario",
            prefixo="rodovia",
            atributos_map={},
            projetar_metrico=True,
            tipo_geometria="line",
            output_id_key="id_trecho_rodoviario",
        ),
    }

    loader = SpatialLayerLoader()
    classifier = DistanceClassifier()
    camadas_construidas = {
        k: SpatialLayer.from_spec(spec, loader=loader, classifier=classifier)
        for k, spec in test_specs.items()
    }
    motor = MotorEspacial(camadas=camadas_construidas)

    # Ingestão e enriquecimento via ProcessadorFocos
    processador = ProcessadorFocos(motor_espacial=motor)
    df_raw = pd.read_csv(raw_csv_path, dtype=str)

    publisher = _InMemoryStreamPublisher()
    with publisher:
        for row in df_raw.itertuples(index=False):
            foco_dict = processador.transformar(row._asdict())
            payload_validado = FocoFatoPayload(**foco_dict)
            publisher.enviar("streaming_focos_incendio", payload_validado.model_dump(mode="json"))

    assert len(publisher.publicados) == 3
    assert publisher.closed is True
    topico, primeiro_foco = publisher.publicados[0]
    assert topico == "streaming_focos_incendio"

    # Verificações de Blindagem Arquitetural (Sem Strings Descritivas na Fato Snowflake)
    assert primeiro_foco["fk_municipio_espacial"] == "313240"
    assert primeiro_foco["fk_hospital_proximo"] == "CNES_ITAJUBA_01"
    assert "nome_hospital" not in primeiro_foco
    assert "nome_municipio" not in primeiro_foco
    assert primeiro_foco["distancia_hospital_km"] is not None
    assert primeiro_foco["distancia_hospital_km"] < 1.0

    # -------------------------------------------------------------------------
    # 4. CIÊNCIA DE DADOS: Eventização de Queimadas via ST-DBSCAN
    # -------------------------------------------------------------------------
    eventizador = EventizadorIncendios(
        motor_espacial=motor,
        config=EventoConfig(
            eps_km=10.0,
            eps_dias=1.0,
            min_samples=2,
            max_duration_days=5,
        ),
    )

    eventos = eventizador.eventizar_focos(df_raw)
    assert len(eventos) >= 1

    for dict_evento in eventos:
        # Validação estrita do contrato de Evento Snowflake
        payload_evento = EventoFatoPayload(**dict_evento)
        assert payload_evento.fk_municipio_principal == "313240"
        assert payload_evento.total_focos >= 2
        assert payload_evento.path_json is not None
        assert payload_evento.duracao_horas >= 0.0
