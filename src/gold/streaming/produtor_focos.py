"""
Produtor orientado a objetos da Fato de Focos de Incêndio (`ProdutorFocosStreaming`).

Orquestra a leitura em chunks do CSV bruto do INPE, o enriquecimento via
`ProcessadorFocos` e a publicação no Apache Kafka usando Injeção de Dependência
e gerenciamento de contexto (SRP / DIP).
"""
from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

import pandas as pd

from src.core.config import settings
from src.core.contracts.contracts import ExecutablePipelineStep, SpatialEngineProtocol, StreamPublisherBase
from src.core.config.settings import PipelineSettings
from src.gold.streaming.kafka_client import KafkaStreamClient
from src.silver.spatial.motor_espacial import MotorEspacial
from src.silver.streaming_processing.processador import ProcessadorFocos

logger = logging.getLogger(__name__)


def linha_para_dict(linha: Any) -> dict[str, Any]:
    """Converte namedtuple do `itertuples()` ou dicionário em `dict` padrão."""
    if hasattr(linha, "_asdict"):
        return linha._asdict()
    return dict(linha)


def validar_payload_json(payload: dict[str, Any]) -> bool:
    """Garante que o payload não contém `NaN`/`Inf` antes de enfileirar no Kafka."""
    json.dumps(payload, ensure_ascii=False, allow_nan=False)
    return True


class ProdutorFocosStreaming(ExecutablePipelineStep):
    """
    Serviço produtor de streaming da tabela fato observacional (`FATO_FOCOS_INCENDIO`).

    Permite injetar `kafka_client`, `motor_espacial`, `processador` e `settings_obj`
    para testes unitários determinísticos sem conexão externa.
    """

    def __init__(
        self,
        kafka_client: StreamPublisherBase | None = None,
        motor_espacial: SpatialEngineProtocol | Any | None = None,
        processador: ProcessadorFocos | None = None,
        settings_obj: PipelineSettings | Any | None = None,
        validate_files: bool = True,
    ) -> None:
        self._cfg = settings_obj or settings
        self._kafka_client = kafka_client
        self._motor_espacial = motor_espacial
        self._processador = processador
        self._validate_files = validate_files

    def _run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        if self._validate_files and hasattr(self._cfg, "verificar_arquivos_obrigatorios"):
            if not self._cfg.verificar_arquivos_obrigatorios():
                sys.exit(1)

        kafka_client = self._kafka_client or KafkaStreamClient(settings_obj=self._cfg)
        motor = self._motor_espacial or MotorEspacial(settings_obj=self._cfg)
        processador = self._processador or ProcessadorFocos(motor)

        topico = getattr(self._cfg, "topico_kafka", getattr(self._cfg, "TOPICO_KAFKA", settings.TOPICO_KAFKA))
        raw_focos = getattr(self._cfg, "raw_focos", getattr(self._cfg, "RAW_FOCOS", settings.RAW_FOCOS))
        chunk_size = getattr(
            self._cfg, "chunk_size_focos", getattr(self._cfg, "CHUNK_SIZE_FOCOS", 10000)
        )
        limite_linhas_teste = getattr(
            self._cfg, "limite_linhas_teste", getattr(self._cfg, "LIMITE_LINHAS_TESTE", None)
        )
        csv_encoding = getattr(
            self._cfg, "csv_encoding", getattr(self._cfg, "CSV_ENCODING", "utf-8")
        )

        logger.info("Iniciando envio para o tópico '%s'.", topico)

        total_lido = 0
        total_enviado = 0
        total_erros = 0
        total_coord_invalidas = 0
        inicio = time.time()

        with kafka_client:
            try:
                leitor_csv = pd.read_csv(
                    raw_focos,
                    chunksize=chunk_size,
                    dtype=str,
                    encoding=csv_encoding,
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

                            kafka_client.enviar(topico, payload_final)
                            total_enviado += 1
                        except Exception as exc:
                            total_erros += 1
                            if total_erros <= 20:
                                logger.warning("Erro ao processar linha %s: %s", total_lido, exc)

                        if total_lido % 10000 == 0:
                            tempo_decorrido = time.time() - inicio
                            taxa = total_enviado / tempo_decorrido if tempo_decorrido > 0 else 0.0
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
                logger.error("Arquivo %s não encontrado.", raw_focos)
            except KeyboardInterrupt:
                logger.info("Ingestão interrompida pelo usuário.")
            except Exception as exc:
                logger.exception("Erro crítico no pipeline: %s", exc)

        tempo_total = time.time() - inicio
        taxa_final = total_enviado / tempo_total if tempo_total > 0 else 0.0

        logger.info("Fluxo de streaming encerrado.")
        logger.info("Total lido: %s | Enviado: %s | Erros: %s", total_lido, total_enviado, total_erros)
        return {
            "total_lido": total_lido,
            "total_enviado": total_enviado,
            "total_erros": total_erros,
            "total_coord_invalidas": total_coord_invalidas,
            "tempo_total_s": round(tempo_total, 6),
            "taxa_msg_s": round(taxa_final, 6),
        }


def iniciar_produtor() -> dict[str, Any]:
    """Ponto de entrada CLI do produtor de focos individuais."""
    return ProdutorFocosStreaming().execute()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    iniciar_produtor()
