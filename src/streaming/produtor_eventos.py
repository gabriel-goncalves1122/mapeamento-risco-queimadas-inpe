"""
Produtor Kafka da fato agregada de eventos de incendio.

Le o CSV bruto do INPE, fecha eventos operacionais em janelas temporais e
publica somente os eventos finalizados no topico consumido pelo supervisor Druid.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

import pandas as pd

from src.config import settings
from src.spatial.motor_espacial import MotorEspacial
from src.streaming.eventos.eventizador import EventoConfig, EventizadorIncendios
from src.streaming.kafka_client import KafkaStreamClient

logger = logging.getLogger(__name__)


def _config_eventos() -> EventoConfig:
    return EventoConfig(
        eps_km=settings.EVENTOS_EPS_KM,
        eps_dias=settings.EVENTOS_EPS_DIAS,
        min_samples=settings.EVENTOS_MIN_SAMPLES,
        max_duration_days=settings.EVENTOS_MAX_DURATION_DAYS,
        area_buffer_km=settings.EVENTOS_AREA_BUFFER_KM,
    )


def _abrir_auditoria(path: str | None):
    if not path:
        return None
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    return destino.open("w", encoding="utf-8")


def _abrir_progress_csv(path: str | None):
    if not path:
        return None, None
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fp = destino.open("w", encoding="utf-8", newline="")
    campos = [
        "timestamp",
        "chunk",
        "raw_lidas",
        "focos_validos",
        "eventos_enviados",
        "buffer_focos",
        "erros_janela",
        "taxa_eventos_s",
        "janela_atual",
    ]
    writer = csv.DictWriter(fp, fieldnames=campos)
    writer.writeheader()
    return fp, writer


def _registrar_progresso(progress_jsonl, progress_writer, progress_csv_fp, registro):
    if progress_jsonl is not None:
        progress_jsonl.write(json.dumps(registro, ensure_ascii=False, allow_nan=False) + "\n")
        progress_jsonl.flush()
    if progress_writer is not None:
        progress_writer.writerow(registro)
        progress_csv_fp.flush()


def _enviar_payload(kafka_client, topico: str, payload: dict, auditoria=None):
    json.dumps(payload, ensure_ascii=False, allow_nan=False)
    kafka_client.enviar(topico, payload)
    if auditoria is not None:
        auditoria.write(json.dumps(payload, ensure_ascii=False, allow_nan=False) + "\n")


def iniciar_produtor(
    debug_jsonl: str | None = None,
    progress_jsonl: str | None = None,
    progress_csv: str | None = None,
):
    """
    Executa o replay streaming do arquivo bruto para Kafka.

    O buffer guarda somente a janela operacional ativa. Janelas anteriores sao
    fechadas e enviadas, evitando que o Druid receba eventos parciais que depois
    precisariam de upsert.
    """
    if hasattr(settings, "verificar_arquivos_obrigatorios"):
        if not settings.verificar_arquivos_obrigatorios():
            sys.exit(1)

    kafka_client = KafkaStreamClient()
    auditoria = _abrir_auditoria(debug_jsonl)
    progresso_jsonl = _abrir_auditoria(progress_jsonl)
    progresso_csv_fp, progresso_csv_writer = _abrir_progress_csv(progress_csv)

    logger.info("Carregando motor espacial para enriquecer eventos.")
    motor = MotorEspacial()
    eventizador = EventizadorIncendios(motor, _config_eventos())

    topico = settings.TOPICO_KAFKA_EVENTOS
    logger.info("Iniciando envio de eventos para o topico '%s'.", topico)

    total_lido = 0
    total_validos = 0
    total_eventos = 0
    total_erros = 0
    buffer = pd.DataFrame()
    inicio = time.time()

    try:
        leitor_csv = pd.read_csv(
            settings.RAW_FOCOS,
            chunksize=settings.CHUNK_SIZE_FOCOS,
            dtype=str,
            encoding=settings.CSV_ENCODING,
            usecols=EventizadorIncendios.COLUNAS_BRUTAS,
        )

        for numero_chunk, chunk in enumerate(leitor_csv, start=1):
            total_lido += len(chunk)
            if settings.LIMITE_LINHAS_TESTE and total_lido > settings.LIMITE_LINHAS_TESTE:
                excedente = total_lido - settings.LIMITE_LINHAS_TESTE
                chunk = chunk.iloc[:-excedente] if excedente < len(chunk) else chunk.iloc[0:0]

            focos_validos = eventizador.preparar_focos(chunk)
            total_validos += len(focos_validos)
            if focos_validos.empty:
                if settings.LIMITE_LINHAS_TESTE and total_lido >= settings.LIMITE_LINHAS_TESTE:
                    break
                continue

            buffer = pd.concat([buffer, focos_validos], ignore_index=True)
            janela_atual = int(buffer["janela_evento"].max())
            janelas_fechadas = sorted(buffer.loc[buffer["janela_evento"] < janela_atual, "janela_evento"].unique())

            for janela in janelas_fechadas:
                grupo_janela = buffer[buffer["janela_evento"] == janela].copy()
                try:
                    for payload in eventizador.eventizar_focos(grupo_janela):
                        _enviar_payload(kafka_client, topico, payload, auditoria)
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
            _registrar_progresso(progresso_jsonl, progresso_csv_writer, progresso_csv_fp, registro)
            logger.info(
                "Chunk %s | lidas=%s | validas=%s | eventos=%s | buffer=%s | erros=%s | %.2f evt/s",
                numero_chunk,
                total_lido,
                total_validos,
                total_eventos,
                len(buffer),
                total_erros,
                taxa,
            )

            if settings.LIMITE_LINHAS_TESTE and total_lido >= settings.LIMITE_LINHAS_TESTE:
                logger.info("Limite de teste atingido: %s linhas.", settings.LIMITE_LINHAS_TESTE)
                break

        if not buffer.empty:
            logger.info("Fechando buffer final com %s focos validos.", len(buffer))
            for payload in eventizador.eventizar_focos(buffer):
                _enviar_payload(kafka_client, topico, payload, auditoria)
                total_eventos += 1
            kafka_client.flush()

    except FileNotFoundError:
        logger.error("Arquivo %s nao encontrado.", settings.RAW_FOCOS)
    except UnicodeDecodeError:
        logger.error("Falha de encoding ao ler o CSV. Tente definir CSV_ENCODING=latin-1.")
    except KeyboardInterrupt:
        logger.info("Ingestao de eventos interrompida pelo usuario.")
    except Exception as exc:
        logger.exception("Erro critico no produtor de eventos: %s", exc)
    finally:
        if auditoria is not None:
            auditoria.close()
        if progresso_jsonl is not None:
            progresso_jsonl.close()
        if progresso_csv_fp is not None:
            progresso_csv_fp.close()
        kafka_client.flush_and_close()

    tempo_total = time.time() - inicio
    logger.info("Fluxo de eventos encerrado.")
    logger.info("Total lido: %s", total_lido)
    logger.info("Focos validos: %s", total_validos)
    logger.info("Eventos enviados: %s", total_eventos)
    logger.info("Erros de janela: %s", total_erros)
    logger.info("Tempo total: %.2fs", tempo_total)
    return {
        "raw_lidas": total_lido,
        "focos_validos": total_validos,
        "eventos_enviados": total_eventos,
        "erros_janela": total_erros,
        "tempo_total_s": round(tempo_total, 6),
    }


def main():
    parser = argparse.ArgumentParser(description="Publica eventos agregados de incendio no Kafka.")
    parser.add_argument(
        "--debug-jsonl",
        help="Arquivo JSONL opcional para auditoria local. Por padrao nada e gravado.",
    )
    parser.add_argument(
        "--progress-jsonl",
        help="Arquivo JSONL opcional com progresso por chunk.",
    )
    parser.add_argument(
        "--progress-csv",
        help="Arquivo CSV opcional com progresso por chunk.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    iniciar_produtor(
        debug_jsonl=args.debug_jsonl,
        progress_jsonl=args.progress_jsonl,
        progress_csv=args.progress_csv,
    )


if __name__ == "__main__":
    main()
