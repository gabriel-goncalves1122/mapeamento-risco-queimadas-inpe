"""
Produtor orientado a objetos da Fato de Eventos de Incêndio (`ProdutorEventosStreaming`).

Coordena a ingestão em janelas temporais fechadas, publica focos e eventos agregados
no Kafka e delega a escrita de telemetria/auditoria ao Context Manager
`StreamingAuditLogger` (`streaming_audit_logger.py`) (SRP / DIP).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from typing import IO, Any

import pandas as pd

from src.core.config import settings
from src.core.contracts.contracts import ExecutablePipelineStep, SpatialEngineProtocol, StreamPublisherBase
from src.core.config.settings import PipelineSettings
from src.gold.science.dbscan.evento_config import EventoConfig
from src.gold.science.dbscan.eventizador import EventizadorIncendios
from src.gold.streaming.kafka_client import KafkaStreamClient
from src.gold.streaming.streaming_audit_logger import StreamingAuditLogger
from src.silver.spatial.motor_espacial import MotorEspacial
from src.silver.streaming_processing.processador import ProcessadorFocos

logger = logging.getLogger(__name__)


def _config_eventos(cfg: Any = settings) -> EventoConfig:
    """Constrói `EventoConfig` a partir do objeto de configuração ativo."""
    return EventoConfig.from_settings(cfg)


def _abrir_auditoria(path: str | None) -> IO[str] | None:
    return StreamingAuditLogger.abrir_arquivo_texto(path)


def _abrir_progress_csv(path: str | None) -> tuple[IO[str] | None, csv.DictWriter | None]:
    return StreamingAuditLogger.abrir_progress_csv(path)


def _registrar_progresso(
    progress_jsonl: IO[str] | None,
    progress_writer: csv.DictWriter | None,
    progress_csv_fp: IO[str] | None,
    registro: dict[str, Any],
) -> None:
    if progress_jsonl is not None:
        progress_jsonl.write(json.dumps(registro, ensure_ascii=False, allow_nan=False) + "\n")
        progress_jsonl.flush()
    if progress_writer is not None and progress_csv_fp is not None:
        progress_writer.writerow(registro)
        progress_csv_fp.flush()


def _enviar_payload(
    kafka_client: StreamPublisherBase | Any,
    topico: str,
    payload: Any,
    auditoria: IO[str] | None = None,
) -> None:
    payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload
    kafka_client.enviar(topico, payload_dict)
    if auditoria is not None:
        auditoria.write(json.dumps(payload_dict, ensure_ascii=False, allow_nan=False) + "\n")


class ProdutorEventosStreaming(ExecutablePipelineStep):
    """
    Serviço produtor da tabela fato agregada de eventos (`FATO_EVENTOS_INCENDIO`).

    Mantém apenas a janela temporal ativa em buffer e despacha janelas fechadas
    ao Kafka, garantindo que o Druid ingira eventos consolidados sem necessidade de upsert.
    """

    def __init__(
        self,
        kafka_client: StreamPublisherBase | None = None,
        motor_espacial: SpatialEngineProtocol | Any | None = None,
        eventizador: EventizadorIncendios | None = None,
        processador_focos: ProcessadorFocos | None = None,
        settings_obj: PipelineSettings | Any | None = None,
        validate_files: bool = True,
    ) -> None:
        self._cfg = settings_obj or settings
        self._kafka_client = kafka_client
        self._motor_espacial = motor_espacial
        self._eventizador = eventizador
        self._processador_focos = processador_focos
        self._validate_files = validate_files

    def _run(
        self,
        debug_jsonl: str | None = None,
        progress_jsonl: str | None = None,
        progress_csv: str | None = None,
    ) -> dict[str, Any]:
        if self._validate_files and hasattr(self._cfg, "verificar_arquivos_obrigatorios"):
            if not self._cfg.verificar_arquivos_obrigatorios():
                sys.exit(1)

        kafka_client = self._kafka_client or KafkaStreamClient(settings_obj=self._cfg)
        motor = self._motor_espacial or MotorEspacial(settings_obj=self._cfg)
        eventizador = self._eventizador or EventizadorIncendios(motor, _config_eventos(self._cfg))
        processador_focos = self._processador_focos or ProcessadorFocos(motor)

        topico_focos = getattr(self._cfg, "topico_kafka", getattr(self._cfg, "TOPICO_KAFKA", settings.TOPICO_KAFKA))
        topico_eventos = getattr(
            self._cfg, "topico_kafka_eventos", getattr(self._cfg, "TOPICO_KAFKA_EVENTOS", settings.TOPICO_KAFKA_EVENTOS)
        )
        raw_focos = getattr(self._cfg, "raw_focos", getattr(self._cfg, "RAW_FOCOS", settings.RAW_FOCOS))
        chunk_size = getattr(
            self._cfg, "chunk_size_focos", getattr(self._cfg, "CHUNK_SIZE_FOCOS", settings.CHUNK_SIZE_FOCOS)
        )
        limite_teste = getattr(
            self._cfg, "limite_linhas_teste", getattr(self._cfg, "LIMITE_LINHAS_TESTE", settings.LIMITE_LINHAS_TESTE)
        )
        csv_encoding = getattr(
            self._cfg, "csv_encoding", getattr(self._cfg, "CSV_ENCODING", settings.CSV_ENCODING)
        )

        logger.info("Iniciando envio para '%s' (Focos) e '%s' (Eventos).", topico_focos, topico_eventos)

        total_lido = 0
        total_validos = 0
        total_focos_enviados = 0
        total_eventos = 0
        total_erros = 0
        buffer = pd.DataFrame()
        inicio = time.time()

        with StreamingAuditLogger(debug_jsonl, progress_jsonl, progress_csv) as audit_log, kafka_client:
            try:
                leitor_csv = pd.read_csv(
                    raw_focos,
                    chunksize=chunk_size,
                    dtype=str,
                    encoding=csv_encoding,
                    usecols=EventizadorIncendios.COLUNAS_BRUTAS,
                )

                for numero_chunk, chunk in enumerate(leitor_csv, start=1):
                    total_lido += len(chunk)
                    if limite_teste and total_lido > limite_teste:
                        excedente = total_lido - limite_teste
                        chunk = chunk.iloc[:-excedente] if excedente < len(chunk) else chunk.iloc[0:0]

                    focos_validos = eventizador.preparar_focos(chunk)
                    total_validos += len(focos_validos)
                    if focos_validos.empty:
                        if limite_teste and total_lido >= limite_teste:
                            break
                        continue

                    for _, row in focos_validos.iterrows():
                        try:
                            payload_foco = processador_focos.transformar(row.to_dict())
                            if payload_foco:
                                _enviar_payload(kafka_client, topico_focos, payload_foco, audit_log.auditoria_fp)
                                total_focos_enviados += 1
                        except Exception as exc:
                            logger.warning("Erro ao processar foco individual: %s", exc)

                    buffer = pd.concat([buffer, focos_validos], ignore_index=True)
                    janela_atual = int(buffer["janela_evento"].max())
                    janelas_fechadas = sorted(
                        buffer.loc[buffer["janela_evento"] < janela_atual, "janela_evento"].unique()
                    )

                    for janela in janelas_fechadas:
                        grupo_janela = buffer[buffer["janela_evento"] == janela].copy()
                        try:
                            for payload in eventizador.eventizar_focos(grupo_janela):
                                _enviar_payload(kafka_client, topico_eventos, payload, audit_log.auditoria_fp)
                                total_eventos += 1
                        except Exception as exc:
                            total_erros += 1
                            logger.warning("Erro ao eventizar janela %s: %s", janela, exc)

                        buffer = buffer[buffer["janela_evento"] != janela].copy()

                    kafka_client.flush()
                    tempo = time.time() - inicio
                    taxa = total_eventos / tempo if tempo > 0 else 0.0
                    registro = {
                        "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "chunk": numero_chunk,
                        "raw_lidas": total_lido,
                        "focos_validos": total_validos,
                        "eventos_enviados": total_eventos,
                        "buffer_focos": len(buffer),
                        "erros_janela": total_erros,
                        "taxa_eventos_s": round(taxa, 6),
                        "janela_atual": janela_atual,
                    }
                    audit_log.registrar_progresso(registro)

                    if limite_teste and total_lido >= limite_teste:
                        logger.info("Limite de teste atingido: %s linhas.", limite_teste)
                        break

                if not buffer.empty:
                    logger.info("Fechando buffer final com %s focos validos.", len(buffer))
                    for payload in eventizador.eventizar_focos(buffer):
                        _enviar_payload(kafka_client, topico_eventos, payload, audit_log.auditoria_fp)
                        total_eventos += 1
                    kafka_client.flush()

            except FileNotFoundError:
                logger.error("Arquivo %s nao encontrado.", raw_focos)
            except UnicodeDecodeError:
                logger.error("Falha de encoding ao ler o CSV. Tente definir CSV_ENCODING=latin-1.")
            except KeyboardInterrupt:
                logger.info("Ingestao de eventos interrompida pelo usuario.")
            except Exception as exc:
                logger.exception("Erro critico no produtor de eventos: %s", exc)

        tempo_total = time.time() - inicio
        return {
            "raw_lidas": total_lido,
            "focos_validos": total_validos,
            "focos_enviados": total_focos_enviados,
            "eventos_enviados": total_eventos,
            "erros_janela": total_erros,
            "tempo_total_s": round(tempo_total, 6),
        }


def iniciar_produtor(
    debug_jsonl: str | None = None,
    progress_jsonl: str | None = None,
    progress_csv: str | None = None,
) -> dict[str, Any]:
    """Função fachada para iniciar o replay de eventos no Kafka."""
    return ProdutorEventosStreaming().execute(
        debug_jsonl=debug_jsonl,
        progress_jsonl=progress_jsonl,
        progress_csv=progress_csv,
    )


def main() -> None:
    """Entrypoint CLI com suporte a flags de auditoria e telemetria."""
    parser = argparse.ArgumentParser(description="Publica eventos agregados de incendio no Kafka.")
    parser.add_argument("--debug-jsonl", help="Arquivo JSONL opcional para auditoria local.")
    parser.add_argument("--progress-jsonl", help="Arquivo JSONL opcional com progresso por chunk.")
    parser.add_argument("--progress-csv", help="Arquivo CSV opcional com progresso por chunk.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    iniciar_produtor(
        debug_jsonl=args.debug_jsonl,
        progress_jsonl=args.progress_jsonl,
        progress_csv=args.progress_csv,
    )


__all__ = ["ProdutorEventosStreaming", "StreamingAuditLogger", "iniciar_produtor", "main"]


if __name__ == "__main__":
    main()
