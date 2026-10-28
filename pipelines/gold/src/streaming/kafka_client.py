"""
=========================================================
MÓDULO: kafka_client.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import json
import logging
import sys
from kafka import KafkaProducer
from config import settings

logger = logging.getLogger(__name__)

class KafkaStreamClient:
    """
    Encapsula a conexão e o envio de dados para o Apache Kafka.
    """

    def __init__(self):
        self.producer = self._criar_produtor()

    def _criar_produtor(self):
        logger.info("Conectando ao cluster Kafka em %s.", settings.KAFKA_BROKER)
        try:
            return KafkaProducer(
                bootstrap_servers=[settings.KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(
                    v, ensure_ascii=False, allow_nan=False
                ).encode('utf-8'),
                acks='all',
                retries=5,
                max_in_flight_requests_per_connection=1,
                linger_ms=getattr(settings, "KAFKA_LINGER_MS", 20),
                batch_size=getattr(settings, "KAFKA_BATCH_SIZE", 65536),
                compression_type=getattr(settings, "KAFKA_COMPRESSION", "gzip"),
                request_timeout_ms=30000,
                retry_backoff_ms=500,
                reconnect_backoff_ms=500,
                reconnect_backoff_max_ms=5000,
                max_block_ms=60000
            )
        except Exception as e:
            logger.error("Erro ao conectar no Kafka: %s", e)
            sys.exit(1)

    def _callback_sucesso(self, record_metadata):
        pass

    def _callback_erro(self, exception):
        logger.warning("Erro assíncrono no envio Kafka: %s", exception)

    def enviar(self, topico, payload):
        future = self.producer.send(topico, value=payload)
        future.add_callback(self._callback_sucesso)
        future.add_errback(self._callback_erro)
        return future

    def flush_and_close(self):
        try:
            self.producer.flush()
            self.producer.close()
        except Exception:
            logger.exception("Erro ao finalizar producer Kafka.")

    def flush(self):
        self.producer.flush()
