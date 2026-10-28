"""
=========================================================
MÓDULO: produtor_focos.py
---------------------------------------------------------
Função Geral: Pipeline de Ingestão Contínua (Kafka). Processa anomalias térmicas brutos em tempo real.
=========================================================
"""
import os
import sys
import time
import json
import logging

import pandas as pd

from pipelines.silver.src.spatial.motor_espacial import MotorEspacial
from pipelines.silver.src.streaming_processing.processador import ProcessadorFocos
from pipelines.gold.src.streaming.kafka_client import KafkaStreamClient
from config import settings

logger = logging.getLogger(__name__)

def linha_para_dict(linha):
    return linha._asdict()

def validar_payload_json(payload):
    json.dumps(payload, ensure_ascii=False, allow_nan=False)
    return True

def iniciar_produtor():
    """
    Orquestrador de Streaming:
    Lê o CSV, enriquece com Motor/Processador e envia ao Kafka.
    """
    if hasattr(settings, "verificar_arquivos_obrigatorios"):
        if not settings.verificar_arquivos_obrigatorios():
            sys.exit(1)

    kafka_client = KafkaStreamClient()

    logger.info("Carregando motor espacial em memória.")
    motor = MotorEspacial()
    processador = ProcessadorFocos(motor)

    logger.info("Iniciando envio para o tópico '%s'.", settings.TOPICO_KAFKA)

    total_lido = 0
    total_enviado = 0
    total_erros = 0
    total_coord_invalidas = 0

    chunk_size = getattr(settings, "CHUNK_SIZE_FOCOS", 10000)
    limite_linhas_teste = getattr(settings, "LIMITE_LINHAS_TESTE", None)
    csv_encoding = getattr(settings, "CSV_ENCODING", "utf-8")

    inicio = time.time()

    try:
        leitor_csv = pd.read_csv(
            settings.RAW_FOCOS,
            chunksize=chunk_size,
            dtype=str,
            encoding=csv_encoding
        )

        for numero_chunk, chunk in enumerate(leitor_csv, start=1):
            logger.info("Processando chunk %s com %s linhas.", numero_chunk, len(chunk))

            for linha in chunk.itertuples(index=False):
                total_lido += 1

                if limite_linhas_teste and total_lido > limite_linhas_teste:
                    logger.info("Limite de teste atingido: %s linhas.", limite_linhas_teste)
                    raise StopIteration

                try:
                    linha_dict = linha_para_dict(linha)
                    payload_final = processador.transformar(linha_dict)
                    validar_payload_json(payload_final)

                    if payload_final.get("coordenada_valida", 0) == 0:
                        total_coord_invalidas += 1

                    kafka_client.enviar(settings.TOPICO_KAFKA, payload_final)
                    total_enviado += 1

                except Exception as e:
                    total_erros += 1
                    if total_erros <= 20:
                        logger.warning("Erro ao processar linha %s: %s", total_lido, e)

                if total_lido % 10000 == 0:
                    tempo_decorrido = time.time() - inicio
                    taxa = total_enviado / tempo_decorrido if tempo_decorrido > 0 else 0
                    logger.info(
                        "Lidas: %s | Enviadas: %s | Erros: %s | Coord. inválidas: %s | Taxa: %.2f msg/s",
                        total_lido,
                        total_enviado,
                        total_erros,
                        total_coord_invalidas,
                        taxa,
                    )

            kafka_client.flush()

    except StopIteration:
        pass
    except UnicodeDecodeError:
        logger.error("Falha de encoding ao ler o CSV. Tente definir CSV_ENCODING=latin-1.")
    except FileNotFoundError:
        logger.error("Arquivo %s não encontrado.", settings.RAW_FOCOS)
    except KeyboardInterrupt:
        logger.info("Ingestão interrompida pelo usuário.")
    except Exception as e:
        logger.exception("Erro crítico no pipeline: %s", e)
    finally:
        kafka_client.flush_and_close()

    tempo_total = time.time() - inicio
    taxa_final = total_enviado / tempo_total if tempo_total > 0 else 0

    logger.info("Fluxo de streaming encerrado.")
    logger.info("Total lido: %s", total_lido)
    logger.info("Total enviado: %s", total_enviado)
    logger.info("Total de erros: %s", total_erros)
    logger.info("Coordenadas inválidas: %s", total_coord_invalidas)
    logger.info("Tempo total: %.2fs", tempo_total)
    logger.info("Taxa média: %.2f msg/s", taxa_final)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    iniciar_produtor()
