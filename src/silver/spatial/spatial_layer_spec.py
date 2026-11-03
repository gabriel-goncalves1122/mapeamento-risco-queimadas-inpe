"""
Especificação declarativa de camada espacial (`SpatialLayerSpec`).

Isola os metadados estruturais de cada dimensão Silver (caminho, chave primária,
prefixo de métricas, mapeamento de colunas e tipo geométrico) da lógica de
indexação R-Tree e consulta espacial (SRP / OCP).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class SpatialLayerSpec:
    """Value Object imutável que descreve uma dimensão espacial a ser indexada."""

    path: str | Path
    nome: str
    col_id: str
    prefixo: str
    atributos_map: Mapping[str, str] = field(default_factory=dict)
    projetar_metrico: bool = False
    tipo_geometria: str = "point"
    output_id_key: str | None = None

    @property
    def resolved_output_id_key(self) -> str:
        """Retorna a chave de saída explícita ou o padrão `<prefixo>_id_proximo`."""
        return self.output_id_key or f"{self.prefixo}_id_proximo"
