"""
Contratos abstratos e protocolos do ecossistema CCO DataOps (ISP / DIP).

Segrega interfaces mínimas para execução de etapas de pipeline, consultas ao
motor espacial, publicação de mensageria e validação de qualidade (QA),
permitindo que as camadas Bronze, Silver, Gold e Orquestração dependam de
abstrações em vez de implementações concretas.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Iterable, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

TResult = TypeVar("TResult")


class ExecutablePipelineStep(ABC, Generic[TResult]):
    """
    Contrato base para componentes executáveis da Arquitetura Medalhão.

    Aplica o padrão Template Method em `execute()` para padronizar telemetria
    de tempo de processamento e rastreabilidade nos logs do Dagster/CLI.
    """

    @property
    def step_name(self) -> str:
        """Identificador legível da etapa para telemetria."""
        return self.__class__.__name__

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> TResult:
        """Gancho concreto com a regra de negócio da etapa."""

    def execute(self, *args: Any, **kwargs: Any) -> TResult:
        """Executa a etapa medindo latência em milissegundos."""
        inicio = time.perf_counter()
        logger.info("[%s] Iniciando execução...", self.step_name)
        resultado = self._run(*args, **kwargs)
        duracao_ms = (time.perf_counter() - inicio) * 1000.0
        logger.info("[%s] Concluído em %.1f ms.", self.step_name, duracao_ms)
        return resultado


@runtime_checkable
class SpatialEngineProtocol(Protocol):
    """
    Protocolo para desacoplar consumidores (ProcessadorFocos, EventizadorIncendios)
    da implementação concreta do MotorEspacial (DIP / ISP).
    """

    def analisar_todas_ameacas(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Cruza coordenada WGS84 contra todas as dimensões geoespaciais."""
        ...

    def intersecoes_camada(
        self,
        nome_camada: str,
        coordenadas: Iterable[tuple[float, float]],
    ) -> list[str]:
        """Retorna IDs únicos de polígonos interceptados por uma sequência de pares (lat, lon)."""
        ...


class StreamPublisherBase(ABC):
    """
    Contrato abstrato para clientes de publicação em streaming (ex: Kafka).

    Implementa o protocolo de Context Manager (`with`) para garantir flush e
    fechamento determinístico de sockets mesmo diante de exceções no produtor.
    """

    @abstractmethod
    def enviar(self, topico: str, payload: dict[str, Any]) -> Any:
        """Publica um payload serializável no tópico informado."""

    @abstractmethod
    def flush(self) -> None:
        """Força o esvaziamento do buffer local de mensagens pendentes."""

    @abstractmethod
    def flush_and_close(self) -> None:
        """Descarrega o buffer e encerra conexões de rede com o broker."""

    def __enter__(self) -> StreamPublisherBase:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.flush_and_close()
        return False


@dataclass(frozen=True)
class ValidationReport:
    """Resultado imutável de uma verificação de integridade de dados (QA)."""

    validator_name: str
    is_valid: bool
    total_records: int
    matched_records: int
    orphan_records: int
    coverage_pct: float
    details: dict[str, Any] = field(default_factory=dict)


class DataValidatorBase(ExecutablePipelineStep, ABC):
    """Contrato abstrato para validadores de qualidade entre dimensões/fatos."""

    @abstractmethod
    def validate(self) -> ValidationReport:
        """Executa a checagem de integridade e retorna relatório estruturado."""

    def _run(self, *args: Any, **kwargs: Any) -> ValidationReport:
        return self.validate()
