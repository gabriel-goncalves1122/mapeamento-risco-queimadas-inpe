"""
Cliente de mensageria Apache Kafka (`KafkaStreamClient`).

Herda de `StreamPublisherBase` (implementando Context Manager `__enter__`/`__exit__`)
e suporta Injeção de Dependência do `producer_factory` e `bootstrap_servers` para
testes unitários sem necessidade de broker ativo (DIP).
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Callable

from kafka import KafkaProducer

from src.core.config import settings
from src.core.contracts.contracts import StreamPublisherBase
from src.core.config.settings import PipelineSettings

logger = logging.getLogger(__name__)


class KafkaStreamClient(StreamPublisherBase):
    """
    Encapsula a conexão e o envio assíncrono de payloads JSON para o Apache Kafka.

    O `value_serializer` bloqueia `NaN`/`Inf` (`allow_nan=False`) para evitar que
    o supervisor de ingestão do Apache Druid rejeite o lote.
    """

    def __init__(
        self,
        bootstrap_servers: str | list[str] | None = None,
        producer_factory: Callable[..., Any] = KafkaProducer,
        settings_obj: PipelineSettings | Any | None = None,
        exit_on_error: bool = True,
    ) -> None:
        self._cfg = settings_obj or settings
        self._bootstrap_servers = bootstrap_servers or getattr(
            self._cfg, "kafka_broker", getattr(self._cfg, "KAFKA_BROKER", settings.KAFKA_BROKER)
        )
        self._producer_factory = producer_factory
        self._exit_on_error = exit_on_error
        self.producer = self._criar_produtor()

    def _criar_produtor(self) -> Any:
        servidores = (
            [self._bootstrap_servers]
            if isinstance(self._bootstrap_servers, str)
            else list(self._bootstrap_servers)
        )
        logger.info("Conectando ao cluster Kafka em %s.", servidores)
        try:
            return self._producer_factory(
                bootstrap_servers=servidores,
                value_serializer=lambda v: json.dumps(
                    v, ensure_ascii=False, allow_nan=False
                ).encode("utf-8"),
                acks="all",
                retries=5,
                max_in_flight_requests_per_connection=1,
                linger_ms=getattr(
                    self._cfg, "kafka_linger_ms", getattr(self._cfg, "KAFKA_LINGER_MS", 20)
                ),
                batch_size=getattr(
                    self._cfg, "kafka_batch_size", getattr(self._cfg, "KAFKA_BATCH_SIZE", 65536)
                ),
                compression_type=getattr(
                    self._cfg, "kafka_compression", getattr(self._cfg, "KAFKA_COMPRESSION", "gzip")
                ),
                request_timeout_ms=30000,
                retry_backoff_ms=500,
                reconnect_backoff_ms=500,
                reconnect_backoff_max_ms=5000,
                max_block_ms=60000,
            )
        except Exception as exc:
            logger.error("Erro ao conectar no Kafka: %s", exc)
            if self._exit_on_error:
                sys.exit(1)
            raise

    def _callback_sucesso(self, record_metadata: Any) -> None:
        pass

    def _callback_erro(self, exception: Exception) -> None:
        logger.warning("Erro assíncrono no envio Kafka: %s", exception)

    def enviar(self, topico: str, payload: dict[str, Any]) -> Any:
        """Envia o dicionário para o tópico Kafka anexando callbacks de confirmação/erro."""
        future = self.producer.send(topico, value=payload)
        if hasattr(future, "add_callback"):
            future.add_callback(self._callback_sucesso)
        if hasattr(future, "add_errback"):
            future.add_errback(self._callback_erro)
        return future

    def flush(self) -> None:
        """Descarrega mensagens pendentes no buffer local."""
        self.producer.flush()

    def flush_and_close(self) -> None:
        """Garante envio das mensagens remanescentes e fecha o socket com o broker."""
        try:
            self.producer.flush()
            self.producer.close()
        except Exception:
            logger.exception("Erro ao finalizar producer Kafka.")
