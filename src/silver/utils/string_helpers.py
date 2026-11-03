"""
Serviço de extração de metadados semiestruturados (`OnsMetadataParser`).

Processa atributos embutidos em balões HTML (`PopupInfo` de KML/GeoJSON da ANEEL/ONS)
e códigos textuais, convertendo-os em campos atômicos limpos para o Apache Druid.
"""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.core.config.constants import NOT_INFORMED, UNKNOWN_UF
from src.silver.utils.cleaners import DruidTextCleaner


class OnsMetadataParser:
    """Extrator baseado em regex para atributos técnicos e siglas de UF em bases do ONS."""

    @staticmethod
    def limpar_codigo(valor: Any) -> str:
        """Remove sufixo decimal `.0`, aspas e quebras de linha de identificadores."""
        if pd.isna(valor):
            return NOT_INFORMED

        texto = str(valor).replace('"', "").replace("\n", " ").replace("\r", " ").strip()
        if texto.endswith(".0"):
            texto = texto[:-2]
        if not texto:
            return NOT_INFORMED

        return DruidTextCleaner.limpar_texto_druid(texto)

    @staticmethod
    def extrair_popup_valor(html: Any, rotulo: str) -> str:
        """Extrai o valor associado a uma tag `<b>Rótulo:</b>` dentro do HTML do KML/ONS."""
        if pd.isna(html):
            return ""

        texto = str(html)
        padrao = rf"<b>\s*{re.escape(rotulo)}\s*:\s*<\/b>\s*(.*?)(?:<br\/>|$)"
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def extrair_uf_popup(texto: Any) -> str:
        """Extrai a sigla UF no final de descrições no formato `'NOME - UF'`."""
        if pd.isna(texto):
            return UNKNOWN_UF

        match = re.search(r"-\s*([A-Z]{2})\s*$", str(texto).upper())
        return match.group(1) if match else UNKNOWN_UF

    @staticmethod
    def extrair_uf_nome_linha(nome: Any) -> str:
        """Extrai a UF principal do sufixo de linhas de transmissão (ex: `'LT 500 KV ... MG/SP'`)."""
        if pd.isna(nome):
            return UNKNOWN_UF

        texto = str(nome).upper().strip()
        match = re.search(r"\b([A-Z]{2})(?:\/[A-Z]{2})?\s*$", texto)
        return match.group(1) if match else UNKNOWN_UF


limpar_codigo = OnsMetadataParser.limpar_codigo
extrair_popup_valor = OnsMetadataParser.extrair_popup_valor
extrair_uf_popup = OnsMetadataParser.extrair_uf_popup
extrair_uf_nome_linha = OnsMetadataParser.extrair_uf_nome_linha
