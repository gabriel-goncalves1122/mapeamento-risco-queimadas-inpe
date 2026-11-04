"""
Extrator de focos de calor da Camada Bronze via repositório aberto do INPE (`InpeQueimadasExtractor`).

Consome os arquivos CSV públicos disponibilizados pelo Dataserver CGIP/COIDS do
Programa Queimadas (INPE), suportando frequências quase tempo-real (10min),
diária e mensal com download em streaming atômico e injeção de dependência (SRP / DIP).
"""
from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Any

import requests

from src.core.config.constants import INPE_DIR
from src.core.contracts.contracts import ExecutablePipelineStep

logger = logging.getLogger(__name__)

# Base oficial do servidor de dados abertos do Programa Queimadas (INPE/COIDS)
URL_BASE_INPE = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv"


class InpeQueimadasExtractor(ExecutablePipelineStep[Path]):
    """
    Extrator orientado a objetos para ingestão de focos de queimada do INPE.

    Aplica escrita em arquivo temporário com `replace` atômico para blindar o
    pipeline contra leituras de arquivos incompletos caso a conexão caia.
    """

    def __init__(
        self,
        output_dir: str | Path = INPE_DIR,
        modo: str = "diario",
        data_ref: str | None = None,
        satelite_filtro: str | None = None,
        url_base: str = URL_BASE_INPE,
        timeout_s: float = 30.0,
        chunk_size: int = 65536,
        http_client: Any | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.modo = modo.lower().strip()
        self.data_ref = data_ref
        self.satelite_filtro = satelite_filtro
        self.url_base = url_base.rstrip("/")
        self.timeout_s = timeout_s
        self.chunk_size = chunk_size
        self._http_client = http_client or requests

    def resolver_nome_arquivo(self) -> str:
        """Determina o nome padronizado do arquivo no servidor INPE conforme o modo e data."""
        hoje = datetime.date.today()

        if self.modo == "diario":
            # Padrão: focos_diario_br_YYYYMMDD.csv
            data_str = self.data_ref or hoje.strftime("%Y%m%d")
            return f"focos_diario_br_{data_str}.csv"
        elif self.modo == "mensal":
            # Padrão: focos_mensal_br_YYYYMM.csv
            data_str = self.data_ref or hoje.strftime("%Y%m")
            return f"focos_mensal_br_{data_str}.csv"
        elif self.modo == "10min":
            # Padrão: focos_10min_YYYYMMDD_HHMM.csv
            data_str = self.data_ref or datetime.datetime.now().strftime("%Y%m%d_%H00")
            return f"focos_10min_{data_str}.csv"
        else:
            raise ValueError(f"Modo de extração não suportado: '{self.modo}'. Use 'diario', 'mensal' ou '10min'.")

    def construir_url(self) -> str:
        """Monta a URL completa do arquivo no Dataserver do INPE."""
        nome_arquivo = self.resolver_nome_arquivo()
        if self.modo == "diario":
            return f"{self.url_base}/diario/Brasil/{nome_arquivo}"
        elif self.modo == "mensal":
            return f"{self.url_base}/mensal/Brasil/{nome_arquivo}"
        else:
            return f"{self.url_base}/10min/{nome_arquivo}"

    def _run(self, *args: Any, **kwargs: Any) -> Path:
        """Executa o download em streaming com escrita em arquivo atômico."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        url = self.construir_url()
        nome_arquivo = self.resolver_nome_arquivo()
        destino = self.output_dir / nome_arquivo
        destino_tmp = self.output_dir / f"{nome_arquivo}.tmp"

        logger.info("Baixando focos do INPE [%s] via URL: %s", self.modo, url)

        # Download em streaming evita alocar arquivos de centenas de MB em memória RAM
        resp = self._http_client.get(url, stream=True, timeout=self.timeout_s)
        if resp.status_code != 200:
            msg = f"Falha ao baixar dados do INPE. HTTP {resp.status_code} na URL: {url}"
            logger.error(msg)
            raise RuntimeError(msg)

        bytes_gravados = 0
        with open(destino_tmp, "wb") as fp:
            if hasattr(resp, "iter_content"):
                for chunk in resp.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        fp.write(chunk)
                        bytes_gravados += len(chunk)
            else:
                conteudo = resp.content if hasattr(resp, "content") else resp.text.encode("utf-8")
                fp.write(conteudo)
                bytes_gravados = len(conteudo)

        # Substituição atômica garante que nenhum consumidor lerá um CSV pela metade
        destino_tmp.replace(destino)
        logger.info(
            "Download concluído: %s (%d bytes).",
            destino.name,
            bytes_gravados,
        )
        return destino
