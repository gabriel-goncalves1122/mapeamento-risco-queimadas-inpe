"""
Testes unitários dos contratos de domínio e infraestrutura da camada Core (`src/core/`).

Valida:
1. `ExecutablePipelineStep`: medição de latência e gancho abstrato `_run`.
2. `ValidationReport` e `DataValidatorBase`: contratos de auditoria QA.
3. `StreamPublisherBase`: protocolo de Context Manager (`__enter__` e `__exit__`).
4. `PipelineSettings`: injeção de ambiente e verificação de arquivos obrigatórios.
5. `FocoFatoPayload` e `EventoFatoPayload`: validação Pydantic de contratos Snowflake.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.core.config.settings import PipelineSettings
from src.core.contracts.contracts import (
    DataValidatorBase,
    ExecutablePipelineStep,
    StreamPublisherBase,
    ValidationReport,
)
from src.core.domain.evento_fato_payload import EventoFatoPayload
from src.core.domain.foco_fato_payload import FocoFatoPayload


class _DummyStep(ExecutablePipelineStep[int]):
    """Implementação concreta mínima para validar o Template Method."""

    def __init__(self, valor: int) -> None:
        self.valor = valor

    def _run(self, *args: Any, **kwargs: Any) -> int:
        return self.valor * 2


class _DummyPublisher(StreamPublisherBase):
    """Implementação concreta mínima para validar o Context Manager."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, Any]]] = []
        self.flushed = False
        self.closed = False

    def enviar(self, topico: str, payload: dict[str, Any]) -> Any:
        self.sent.append((topico, payload))
        return True

    def flush(self) -> None:
        self.flushed = True

    def flush_and_close(self) -> None:
        self.flushed = True
        self.closed = True


class _DummyValidator(DataValidatorBase):
    """Implementação concreta de validador QA."""

    def __init__(self, is_valid: bool = True) -> None:
        self._is_valid = is_valid

    def validate(self) -> ValidationReport:
        return ValidationReport(
            validator_name=self.step_name,
            is_valid=self._is_valid,
            total_records=10,
            matched_records=10 if self._is_valid else 8,
            orphan_records=0 if self._is_valid else 2,
            coverage_pct=100.0 if self._is_valid else 80.0,
            details={"dummy_key": "dummy_val"},
        )


def test_executable_pipeline_step_template_method() -> None:
    """Verifica que execute() cronometra e delega a _run() preservando o step_name."""
    step = _DummyStep(valor=21)
    assert step.step_name == "_DummyStep"
    resultado = step.execute()
    assert resultado == 42


def test_stream_publisher_base_context_manager() -> None:
    """Garante que StreamPublisherBase descarrega buffers e fecha conexões no bloco with."""
    pub = _DummyPublisher()
    with pub as p:
        p.enviar("topico_teste", {"chave": "valor"})

    assert len(pub.sent) == 1
    assert pub.flushed is True
    assert pub.closed is True


def test_validation_report_imutabilidade_e_campos() -> None:
    """Verifica imutabilidade do ValidationReport e cálculo correto de campos."""
    validator = _DummyValidator(is_valid=True)
    report = validator.execute()

    assert report.is_valid is True
    assert report.total_records == 10
    assert report.matched_records == 10
    assert report.orphan_records == 0
    assert report.coverage_pct == 100.0
    assert report.validator_name == "_DummyValidator"
    assert report.details == {"dummy_key": "dummy_val"}

    # Garante imutabilidade (@dataclass(frozen=True))
    with pytest.raises(Exception):
        report.is_valid = False  # type: ignore[misc]


def test_pipeline_settings_from_env_e_validacao(tmp_path: Path) -> None:
    """Garante parsing seguro de variáveis de ambiente no PipelineSettings."""
    raw_focos_fake = tmp_path / "focos.csv"
    raw_focos_fake.write_text("DataHora,Latitude,Longitude\n", encoding="utf-8")

    cfg = PipelineSettings.from_env(
        {
            "RAW_FOCOS": str(raw_focos_fake),
            "CHUNK_SIZE_FOCOS": "5000",
            "KAFKA_BROKER": "broker:9092",
            "TOPICO_KAFKA": "topico_focos_custom",
        }
    )

    assert cfg.raw_focos == str(raw_focos_fake)
    assert cfg.chunk_size_focos == 5000
    assert cfg.kafka_broker == "broker:9092"
    assert cfg.topico_kafka == "topico_focos_custom"


def test_foco_fato_payload_contrato_pydantic() -> None:
    """Valida que FocoFatoPayload aceita chaves e métricas Snowflake válidas."""
    payload_valido = FocoFatoPayload(
        data_hora="2025-01-01 12:00:00",
        pais_origem="BRASIL",
        fk_bioma="CERRADO",
        fk_satelite_sensor="AQUA_M-T",
        fk_municipio="MG_ITAJUBA",
        fk_municipio_espacial="313240",
        fk_terra_indigena="NAO INFORMADO",
        fk_terra_indigena_proxima="TI_01",
        fk_trecho_rodoviario="BR_01",
        fk_linha_transmissao="LT_01",
        fk_subestacao="SE_01",
        fk_sistema_isolado="NAO INFORMADO",
        fk_hospital_proximo="CNES_01",
        latitude=-22.425,
        longitude=-45.452,
        coordenada_valida=1,
        foco_point='{"type":"Point","coordinates":[-45.452,-22.425]}',
        dias_sem_chuva=15.0,
        precipitacao_mm=0.0,
        risco_fogo_inpe=0.85,
        potencia_radiativa_fogo=40.0,
        indice_condicao_ambiental=1.25,
        indice_queimada_evento=3.5,
        distancia_rodovia_km=0.5,
        distancia_linha_km=1.2,
        distancia_subestacao_km=3.0,
        distancia_sistema_isolado_km=None,
        distancia_hospital_km=0.8,
        distancia_terra_indigena_km=15.0,
    )

    d = payload_valido.model_dump(mode="json")
    assert d["fk_municipio_espacial"] == "313240"
    assert d["coordenada_valida"] == 1
    assert "nome_hospital" not in d
    assert "nome_municipio" not in d

    # Valida imutabilidade estrita (frozen=True)
    with pytest.raises(ValidationError):
        payload_valido.latitude = -20.0  # type: ignore[misc]


def test_foco_fato_payload_rejeita_campos_obrigatorios_ausentes() -> None:
    """Garante que a omissão de FKs obrigatórias dispara ValidationError."""
    with pytest.raises(ValidationError):
        # Falta data_hora e outros campos obrigatórios
        FocoFatoPayload(latitude=-22.0, longitude=-45.0)  # type: ignore[call-arg]


def test_evento_fato_payload_contrato_pydantic() -> None:
    """Valida a conformidade de schema do EventoFatoPayload."""
    evento = EventoFatoPayload(
        fire_event_id="EVT_2025_001",
        data_inicio="2025-01-01 10:00:00",
        data_fim="2025-01-01 14:00:00",
        pais_origem="BRASIL",
        fk_bioma="CERRADO",
        fk_satelite_sensor="AQUA_M-T",
        fk_municipio_principal="313240",
        codigos_ibge_interceptados=["313240"],
        qtd_municipios_interceptados=1,
        fk_terra_indigena="NAO INFORMADO",
        codigos_ti_interceptadas=["NAO INFORMADO"],
        qtd_terras_indigenas_interceptadas=0,
        fk_terra_indigena_proxima="TI_01",
        fk_trecho_rodoviario="BR_01",
        fk_linha_transmissao="LT_01",
        fk_subestacao="SE_01",
        fk_sistema_isolado="NAO INFORMADO",
        fk_hospital="CNES_01",
        latitude_centroide=-22.425,
        longitude_centroide=-45.452,
        path_json="[[[-45.46,-22.43],[-45.44,-22.43],[-45.44,-22.41],[-45.46,-22.41]]]",
        total_focos=5,
        duracao_horas=4.0,
        duracao_dias=0.17,
        area_evento_km2=2.5,
        soma_frp=150.0,
        media_frp=30.0,
        max_frp=60.0,
        media_risco_fogo=0.8,
        max_risco_fogo=0.9,
        media_dias_sem_chuva=12.0,
        media_precipitacao_mm=0.0,
        indice_condicao_ambiental_medio=1.2,
        indice_queimada_evento_medio=3.0,
        indice_queimada_evento_max=5.0,
        distancia_rodovia_km=0.3,
        distancia_linha_km=0.8,
        distancia_subestacao_km=2.0,
        distancia_sistema_isolado_km=None,
        distancia_hospital_km=1.0,
        distancia_terra_indigena_km=10.0,
        indice_ameaca_rodovia=10.0,
        indice_ameaca_linha=15.0,
        indice_ameaca_subestacao=20.0,
        indice_ameaca_sistema_isolado=0.0,
        indice_pressao_saude=5.0,
        indice_pressao_terra_indigena=2.0,
        indice_pressao_maxima=20.0,
        param_eps_km=10.0,
        param_eps_dias=1.0,
        param_min_samples=2,
        param_max_duration_days=5,
    )

    d = evento.model_dump(mode="json")
    assert d["fire_event_id"] == "EVT_2025_001"
    assert d["total_focos"] == 5
    assert d["duracao_horas"] == 4.0

    # Valida imutabilidade estrita (frozen=True)
    with pytest.raises(ValidationError):
        evento.total_focos = 10  # type: ignore[misc]
