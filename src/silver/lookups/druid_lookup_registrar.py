"""
Serviço de registro de Lookups URI em memória no Apache Druid (`DruidLookupRegistrar`).

Constrói especificações `cachedNamespace` apontando para os CSVs dimensionais
em `src/silver/data/dimensions` via protocolo local `file://`.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

from src.core.config.constants import DIMENSIONS_DIR
from src.core.contracts.contracts import ExecutablePipelineStep

logger = logging.getLogger(__name__)

DIMS_DIR = str(DIMENSIONS_DIR)
DRUID_URL = os.environ.get("DRUID_OVERLORD_URL", "http://localhost:8081")


class DruidLookupRegistrar(ExecutablePipelineStep[bool]):
    """
    Constrói e publica os mapas de Lookup (`cachedNamespace` via `file://`) no Apache Druid.

    Usar URI local (`file:///opt/src/silver/data/dimensions/...`) evita trafegar
    JSONs gigantes pelo Coordinator e permite que consultas SQL no Superset resolvam
    nomes de municípios, hospitais, TIs e ativos elétricos em $O(1)$ sem JOIN pesado.
    """

    DEFAULT_LOOKUP_SPECS: dict[str, tuple[str, str, str]] = {
        "municipios_nome": ("dim_municipios_coordenadas.csv", "codigo_ibge", "municipios_nome"),
        "municipios_uf": ("dim_municipios_coordenadas.csv", "codigo_ibge", "estado_sigla"),
        "municipios_regiao": ("dim_municipios_coordenadas.csv", "codigo_ibge", "regiao_brasil"),
        "hospitais_nome": ("dim_hospitais_cnes.csv", "codigo_cnes", "nome_hospital"),
        "hospitais_tipo": ("dim_hospitais_cnes.csv", "codigo_cnes", "tipo_unidade"),
        "hospitais_critico": ("dim_hospitais_cnes.csv", "codigo_cnes", "tipo_unidade_critica"),
        "hospitais_24h": ("dim_hospitais_cnes.csv", "codigo_cnes", "funciona_24h"),
        "ti_nome": ("dim_terras_indigenas.csv", "codigo_ti", "nome_terra_indigena"),
        "ti_etnia": ("dim_terras_indigenas.csv", "codigo_ti", "etnia"),
        "ti_uf": ("dim_terras_indigenas.csv", "codigo_ti", "estado_sigla"),
        "ti_path_json": ("dim_terras_indigenas.csv", "codigo_ti", "path_json"),
        "linha_nome": ("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "nome_linha"),
        "linha_tensao": ("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "tensao_kv"),
        "linha_uf": ("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "estado_sigla_estimado"),
        "linha_path_json": ("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "path_json"),
        "subestacao_nome": ("dim_ons_subestacoes.csv", "id_subestacao", "nome_subestacao"),
        "subestacao_capacidade": ("dim_ons_subestacoes.csv", "id_subestacao", "capacidade_mw"),
        "subestacao_risco_cascata": ("dim_ons_subestacoes.csv", "id_subestacao", "risco_cascata"),
        "subestacao_betweenness": ("dim_ons_subestacoes.csv", "id_subestacao", "betweenness_score_norm"),
        "sistema_isolado_nome": ("dim_ons_sistemas_isolados.csv", "id_sistema_isolado", "nome_sistema_isolado"),
        "sistema_isolado_uf": ("dim_ons_sistemas_isolados.csv", "id_sistema_isolado", "estado_sigla"),
        "rodovia_codigo": ("dim_rodovias_federais.csv", "id_trecho_rodoviario", "codigo_rodovia"),
        "rodovia_criticidade": ("dim_rodovias_federais.csv", "id_trecho_rodoviario", "criticidade_rodovia"),
    }

    def __init__(
        self,
        dims_dir: str | Path = DIMS_DIR,
        druid_url: str = DRUID_URL,
        container_dims_prefix: str = "file:///opt/src/silver/data/dimensions",
        lookup_specs: Mapping[str, tuple[str, str, str]] | None = None,
        http_poster: Callable[[dict[str, Any]], tuple[bool, str | None]] | None = None,
    ) -> None:
        self.dims_dir = Path(dims_dir)
        self.druid_url = druid_url.rstrip("/")
        self.container_dims_prefix = container_dims_prefix.rstrip("/")
        self.lookup_specs = dict(lookup_specs or self.DEFAULT_LOOKUP_SPECS)
        self._http_poster = http_poster or self.post_lookups

    def get_csv_columns(self, filename: str) -> list[str]:
        """Lê apenas a primeira linha (cabeçalho) do CSV dimensional local."""
        filepath = self.dims_dir / filename
        if not filepath.exists():
            return []
        with filepath.open("r", encoding="utf-8", newline="") as fp:
            reader = csv.reader(fp)
            try:
                return next(reader)
            except StopIteration:
                return []

    def make_uri_lookup(self, filename: str, key_col: str, val_col: str) -> dict[str, Any] | None:
        """Monta a especificação `cachedNamespace` para uma relação `(keyColumn -> valueColumn)`."""
        cols = self.get_csv_columns(filename)
        if not cols:
            return None

        # O Druid recarrega automaticamente o arquivo local via hash/mtime sem lock de rede
        return {
            "version": str(int(time.time())),
            "lookupExtractorFactory": {
                "type": "cachedNamespace",
                "extractionNamespace": {
                    "type": "uri",
                    "uri": f"{self.container_dims_prefix}/{filename}",
                    "namespaceParseSpec": {
                        "format": "csv",
                        "columns": cols,
                        "skipHeaderRows": 1,
                        "keyColumn": key_col,
                        "valueColumn": val_col,
                    },
                },
                "firstCacheTimeout": 0,
            },
        }

    def build_payload(self) -> dict[str, dict[str, Any]]:
        """Constrói o dicionário `__default` com todos os lookups cujos CSVs existem."""
        default_tier: dict[str, Any] = {}
        for lookup_name, (filename, key_col, val_col) in self.lookup_specs.items():
            config = self.make_uri_lookup(filename, key_col, val_col)
            if config is not None:
                default_tier[lookup_name] = config
        return {"__default": default_tier}

    def post_lookups(self, payload_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Envia o payload JSON para o endpoint `/druid/coordinator/v1/lookups/config`."""
        url = f"{self.druid_url}/druid/coordinator/v1/lookups/config"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                _ = response.read()
                return True, None
        except Exception as exc:
            err = exc.read().decode("utf-8") if hasattr(exc, "read") else str(exc)
            return False, err

    def _run(self) -> bool:
        payload = self.build_payload()
        logger.info("Enviando configuração de %d lookups URI ao Druid...", len(payload["__default"]))
        success, err = self._http_poster(payload)

        # Caso o Coordinator nunca tenha recebido um tier de lookups antes, inicializa com `{}`
        if not success and err and "Not initialized" in err:
            logger.info("Inicializando tier de lookups no Druid Coordinator...")
            self._http_poster({})
            success, err = self._http_poster(payload)

        if not success:
            logger.error("Erro ao configurar lookups no Druid: %s", err)
            return False

        logger.info("Lookups configurados com sucesso no Druid.")
        return True
