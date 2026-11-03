"""
Gerenciador de auditoria e telemetria de streaming (`StreamingAuditLogger`).

Encapsula a abertura, escrita incremental (JSONL e CSV) e fechamento determinístico
dos arquivos opcionais de auditoria e progresso do produtor de eventos via protocolo
de Context Manager (`__enter__` / `__exit__`) (SRP).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import IO, Any


class StreamingAuditLogger:
    """
    Context Manager para escrita de auditoria (`debug_jsonl`) e progresso
    (`progress_jsonl`, `progress_csv`) durante o replay de eventos no Kafka.
    """

    PROGRESS_FIELDS: tuple[str, ...] = (
        "timestamp",
        "chunk",
        "raw_lidas",
        "focos_validos",
        "eventos_enviados",
        "buffer_focos",
        "erros_janela",
        "taxa_eventos_s",
        "janela_atual",
    )

    def __init__(
        self,
        debug_jsonl: str | None = None,
        progress_jsonl: str | None = None,
        progress_csv: str | None = None,
    ) -> None:
        self.debug_jsonl_path = debug_jsonl
        self.progress_jsonl_path = progress_jsonl
        self.progress_csv_path = progress_csv
        self.auditoria_fp: IO[str] | None = None
        self.progresso_jsonl_fp: IO[str] | None = None
        self.progresso_csv_fp: IO[str] | None = None
        self.progresso_csv_writer: csv.DictWriter | None = None

    @staticmethod
    def abrir_arquivo_texto(path: str | None) -> IO[str] | None:
        """Cria diretórios pais se necessário e abre arquivo texto em UTF-8."""
        if not path:
            return None
        destino = Path(path)
        destino.parent.mkdir(parents=True, exist_ok=True)
        return destino.open("w", encoding="utf-8")

    @classmethod
    def abrir_progress_csv(cls, path: str | None) -> tuple[IO[str] | None, csv.DictWriter | None]:
        """Abre CSV de telemetria e escreve o cabeçalho padronizado de throughput."""
        if not path:
            return None, None
        destino = Path(path)
        destino.parent.mkdir(parents=True, exist_ok=True)
        fp = destino.open("w", encoding="utf-8", newline="")
        writer = csv.DictWriter(fp, fieldnames=list(cls.PROGRESS_FIELDS))
        writer.writeheader()
        return fp, writer

    def __enter__(self) -> StreamingAuditLogger:
        self.auditoria_fp = self.abrir_arquivo_texto(self.debug_jsonl_path)
        self.progresso_jsonl_fp = self.abrir_arquivo_texto(self.progress_jsonl_path)
        self.progresso_csv_fp, self.progresso_csv_writer = self.abrir_progress_csv(self.progress_csv_path)
        return self

    def registrar_auditoria_payload(self, payload_dict: dict[str, Any]) -> None:
        """Persiste o payload enviado ao Kafka no log de auditoria JSONL quando ativo."""
        if self.auditoria_fp is not None:
            self.auditoria_fp.write(json.dumps(payload_dict, ensure_ascii=False, allow_nan=False) + "\n")

    def registrar_progresso(self, registro: dict[str, Any]) -> None:
        """Persiste telemetria de throughput por chunk nos canais ativos."""
        if self.progresso_jsonl_fp is not None:
            self.progresso_jsonl_fp.write(json.dumps(registro, ensure_ascii=False, allow_nan=False) + "\n")
            self.progresso_jsonl_fp.flush()
        if self.progresso_csv_writer is not None and self.progresso_csv_fp is not None:
            self.progresso_csv_writer.writerow(registro)
            self.progresso_csv_fp.flush()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        for fp in (self.auditoria_fp, self.progresso_jsonl_fp, self.progresso_csv_fp):
            if fp is not None:
                fp.close()
        return False
