"""
Testes unitários das classes POO da Camada Gold e Orquestração Dagster.

Valida `SINNetworkCentralityModel`, `EventoConfig`, `EventGeometryBuilder`,
`KafkaStreamClient` (Context Manager), `StreamingAuditLogger`,
`ProdutorFocosStreaming`, `ProdutorEventosStreaming` e a execução em memória
dos assets no Dagster.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.contracts.contracts import ExecutablePipelineStep, StreamPublisherBase
from src.core.config.settings import PipelineSettings
from src.gold.science.dbscan.event_geometry_builder import EventGeometryBuilder
from src.gold.science.dbscan.evento_config import EventoConfig
from src.gold.science.networkx.network_builder import SINNetworkCentralityModel
from src.gold.streaming.kafka_client import KafkaStreamClient
from src.gold.streaming.produtor_eventos import ProdutorEventosStreaming
from src.gold.streaming.produtor_focos import ProdutorFocosStreaming
from src.gold.streaming.streaming_audit_logger import StreamingAuditLogger
from src.orchestration.dagster.repo import execute_pipeline_step


class _FakeKafkaDriver:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.sent: list[tuple[str, dict[str, Any]]] = []
        self.flushed = False
        self.closed = False

    def send(self, topico: str, value: dict[str, Any]) -> Any:
        self.sent.append((topico, value))
        return object()

    def flush(self) -> None:
        self.flushed = True

    def close(self) -> None:
        self.closed = True


class _FakeStreamPublisher(StreamPublisherBase):
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []
        self.flushed = 0
        self.closed = False

    def enviar(self, topico: str, payload: dict[str, Any]) -> None:
        self.messages.append((topico, payload))

    def flush(self) -> None:
        self.flushed += 1

    def flush_and_close(self) -> None:
        self.flushed += 1
        self.closed = True


class _FakeMotorEspacial:
    def analisar_todas_ameacas(self, latitude: float, longitude: float) -> dict[str, Any]:
        return {
            "codigo_ibge_espacial": "313240",
            "codigo_ti": "NAO INFORMADO",
            "codigo_ti_proxima": "TI_1",
            "id_trecho_rodoviario": "ROD_1",
            "id_linha_transmissao": "LT_1",
            "id_subestacao": "SE_1",
            "id_sistema_isolado": "SIS_1",
            "codigo_cnes_prox": "CNES_1",
            "distancia_rodovia_km": 2.0,
            "distancia_linha_km": 3.0,
            "distancia_subestacao_km": 4.0,
            "distancia_sistema_isolado_km": 10.0,
            "distancia_hospital_km": 1.5,
            "distancia_terra_indigena_km": 25.0,
            "linha_tensao_kv": 500.0,
            "subestacao_capacidade_mw": 1000.0,
        }

    def intersecoes_camada(self, nome_camada: str, coordenadas: Any) -> list[str]:
        return ["313240"] if nome_camada == "camada_municipios" else []


def test_sin_network_centrality_model_calcula_betweenness_e_cascata(tmp_path: Path) -> None:
    """Verifica que SINNetworkCentralityModel infere arestas e classifica risco de cascata."""
    sub_csv = tmp_path / "dim_ons_subestacoes.csv"
    lin_csv = tmp_path / "dim_ons_linhas_transmissao.csv"

    pd.DataFrame(
        {
            "id_subestacao": ["SE_A", "SE_B", "SE_C"],
            "nome_subestacao": ["SUB A", "SUB B CENTRAL", "SUB C"],
            "longitude": [-45.0, -45.02, -45.04],
            "latitude": [-22.0, -22.0, -22.0],
        }
    ).to_csv(sub_csv, index=False)

    pd.DataFrame(
        {
            "id_linha_transmissao": ["LT_1", "LT_2"],
            "path_json": [
                "[[-45.0, -22.0], [-45.02, -22.0]]",
                "[[-45.02, -22.0], [-45.04, -22.0]]",
            ],
        }
    ).to_csv(lin_csv, index=False)

    model = SINNetworkCentralityModel(subestacoes_path=sub_csv, linhas_path=lin_csv)
    df_enriquecido = model.execute()

    assert df_enriquecido is not None
    assert "betweenness_score_norm" in df_enriquecido.columns
    assert "risco_cascata" in df_enriquecido.columns
    se_central = df_enriquecido.loc[df_enriquecido["id_subestacao"] == "SE_B"].iloc[0]
    assert se_central["betweenness_score_norm"] == 100.0
    assert se_central["risco_cascata"] == "EXTREMO"


def test_evento_config_e_event_geometry_builder_isolados() -> None:
    """Garante que EventoConfig.from_settings e EventGeometryBuilder operam de forma independente."""
    cfg_settings = PipelineSettings(eventos_eps_km=8.0, eventos_min_samples=4)
    ev_cfg = EventoConfig.from_settings(cfg_settings)
    assert ev_cfg.eps_km == 8.0
    assert ev_cfg.min_samples == 4

    builder = EventGeometryBuilder(area_buffer_km=0.5)
    df_cluster = pd.DataFrame(
        {
            "latitude": [-22.400, -22.401, -22.402],
            "longitude": [-45.400, -45.401, -45.402],
        }
    )
    geom_gps, lat_c, lon_c, area_km2 = builder.construir_geometria(df_cluster)
    path_json = builder.serializar_path_json(geom_gps)

    assert area_km2 > 0.0
    assert -23.0 < lat_c < -22.0
    assert -46.0 < lon_c < -45.0
    assert path_json.startswith("[[")


def test_kafka_stream_client_context_manager_fecha_conexao() -> None:
    """Garante que o protocolo `with KafkaStreamClient(...)` executa flush_and_close ao sair."""
    drivers: list[_FakeKafkaDriver] = []

    def _factory(**kwargs: Any) -> _FakeKafkaDriver:
        drv = _FakeKafkaDriver(**kwargs)
        drivers.append(drv)
        return drv

    with KafkaStreamClient(bootstrap_servers="localhost:29092", producer_factory=_factory) as client:
        client.enviar("topico_teste", {"chave": 1})

    assert len(drivers) == 1
    assert drivers[0].sent == [("topico_teste", {"chave": 1})]
    assert drivers[0].flushed is True
    assert drivers[0].closed is True


def test_produtor_focos_e_eventos_streaming_com_injecao_de_dependencia(tmp_path: Path) -> None:
    """Valida ProdutorFocosStreaming e ProdutorEventosStreaming usando publisher e motor injetados."""
    raw_csv = tmp_path / "focos_brutos.csv"
    pd.DataFrame(
        [
            {
                "DataHora": "2025-01-01 00:00:00",
                "Satelite": "GOES",
                "Pais": "Brasil",
                "Estado": "MG",
                "Municipio": "Itajuba",
                "Bioma": "Mata Atlantica",
                "DiaSemChuva": "5",
                "Precipitacao": "0.0",
                "RiscoFogo": "0.8",
                "FRP": "25.0",
                "Latitude": "-22.400",
                "Longitude": "-45.400",
            },
            {
                "DataHora": "2025-01-01 00:10:00",
                "Satelite": "GOES",
                "Pais": "Brasil",
                "Estado": "MG",
                "Municipio": "Itajuba",
                "Bioma": "Mata Atlantica",
                "DiaSemChuva": "5",
                "Precipitacao": "0.0",
                "RiscoFogo": "0.9",
                "FRP": "30.0",
                "Latitude": "-22.401",
                "Longitude": "-45.401",
            },
            {
                "DataHora": "2025-01-01 00:20:00",
                "Satelite": "GOES",
                "Pais": "Brasil",
                "Estado": "MG",
                "Municipio": "Itajuba",
                "Bioma": "Mata Atlantica",
                "DiaSemChuva": "5",
                "Precipitacao": "0.0",
                "RiscoFogo": "0.95",
                "FRP": "45.0",
                "Latitude": "-22.402",
                "Longitude": "-45.402",
            },
        ]
    ).to_csv(raw_csv, index=False)

    cfg = PipelineSettings(
        raw_focos=str(raw_csv),
        chunk_size_focos=10,
        topico_kafka="topico_focos_test",
        topico_kafka_eventos="topico_eventos_test",
        eventos_min_samples=3,
    )

    pub_focos = _FakeStreamPublisher()
    res_focos = ProdutorFocosStreaming(
        kafka_client=pub_focos,
        motor_espacial=_FakeMotorEspacial(),
        settings_obj=cfg,
        validate_files=False,
    ).execute()

    assert res_focos["total_lido"] == 3
    assert res_focos["total_enviado"] == 3
    assert pub_focos.closed is True

    pub_eventos = _FakeStreamPublisher()
    debug_jsonl = tmp_path / "debug.jsonl"
    progress_csv = tmp_path / "progress.csv"
    res_eventos = ProdutorEventosStreaming(
        kafka_client=pub_eventos,
        motor_espacial=_FakeMotorEspacial(),
        settings_obj=cfg,
        validate_files=False,
    ).execute(debug_jsonl=str(debug_jsonl), progress_csv=str(progress_csv))

    assert res_eventos["focos_validos"] == 3
    assert res_eventos["focos_enviados"] == 3
    assert res_eventos["eventos_enviados"] == 1
    assert pub_eventos.closed is True
    assert debug_jsonl.exists()
    assert progress_csv.exists()


def test_dagster_execute_pipeline_step_em_memoria() -> None:
    """Confirma que o helper do Dagster executa contratos ExecutablePipelineStep diretamente."""

    class _Step(ExecutablePipelineStep):
        def _run(self) -> list[int]:
            return [1, 2, 3]

    assert execute_pipeline_step(None, _Step()) == [1, 2, 3]
    with StreamingAuditLogger() as logger_vazio:
        assert logger_vazio.auditoria_fp is None
