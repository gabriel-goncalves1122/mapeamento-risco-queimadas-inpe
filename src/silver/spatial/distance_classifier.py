"""
Classificador de distâncias e higienizador de atributos espaciais (`DistanceClassifier`).

Concentra as regras de discretização de proximidade (faixas em km e flags binárias)
e a coerção de atributos lidos das dimensões Silver antes de compor o resultado
do `SpatialLayer` (SRP / OCP).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd

from src.core.config.constants import DISTANCE_LIMITS_KM, NOT_INFORMED


class DistanceClassifier:
    """
    Aplica as faixas operacionais de distância e normaliza atributos de feições espaciais.

    Permite parametrizar os limites de distância (`limites_km`) via construtor sem
    alterar a implementação de consulta vetorial do `SpatialLayer`.
    """

    DEFAULT_LIMITS_KM: tuple[int, ...] = tuple(DISTANCE_LIMITS_KM)

    def __init__(self, limites_km: Sequence[int] | None = None) -> None:
        self.limites_km: tuple[int, ...] = tuple(limites_km or self.DEFAULT_LIMITS_KM)

    @staticmethod
    def faixa_distancia(distancia_km: float | None) -> str:
        """Discretiza a distância métrica nas faixas analíticas de criticidade."""
        if distancia_km is None or distancia_km < 0:
            return "SEM_DISTANCIA"
        if distancia_km <= 1:
            return "ATE_1KM"
        if distancia_km <= 3:
            return "ATE_3KM"
        if distancia_km <= 7:
            return "ATE_7KM"
        if distancia_km <= 15:
            return "ATE_15KM"
        if distancia_km <= 50:
            return "ATE_50KM"
        return "ACIMA_50KM"

    @staticmethod
    def flag_ate(distancia_km: float | None, limite_km: int) -> int:
        """Retorna 1 quando a feição está dentro do raio `limite_km`, ou 0 caso contrário."""
        if distancia_km is None or distancia_km < 0:
            return 0
        return 1 if distancia_km <= limite_km else 0

    def flags_por_limite(self, prefixo: str, distancia_km: float | None) -> dict[str, int]:
        """Gera todas as flags `<prefixo>_ate_<N>km` configuradas para a camada."""
        return {
            f"{prefixo}_ate_{limite}km": self.flag_ate(distancia_km, limite)
            for limite in self.limites_km
        }

    @staticmethod
    def normalizar_id(valor: Any) -> str:
        """Remove quebras de linha e aspas em chaves de dimensões."""
        if pd.isna(valor):
            return NOT_INFORMED
        texto = str(valor).replace('"', "").replace("\n", " ").replace("\r", " ").strip()
        return texto if texto else NOT_INFORMED

    @staticmethod
    def normalizar_texto(valor: Any) -> str:
        """Garante fallback `NAO INFORMADO` para atributos textuais vazios ou nulos."""
        if pd.isna(valor):
            return NOT_INFORMED
        texto = str(valor).strip()
        return texto if texto else NOT_INFORMED

    @staticmethod
    def normalizar_float(valor: Any) -> float | None:
        """Converte grandezas elétricas (`_kv`, `_mw`) aceitando separador decimal com vírgula."""
        try:
            if pd.isna(valor):
                return None
            texto = str(valor).replace(",", ".").strip()
            return float(texto) if texto else None
        except Exception:
            return None

    @classmethod
    def extrair_atributos_intersecao(
        cls,
        linha: Mapping[str, Any] | pd.Series,
        atributos_map: Mapping[str, str],
    ) -> dict[str, str]:
        """Mapeia os atributos de uma feição poligonal interceptada."""
        return {
            nome_saida: cls.normalizar_texto(linha.get(nome_coluna, NOT_INFORMED))
            for nome_saida, nome_coluna in atributos_map.items()
        }

    @classmethod
    def extrair_atributos_proximidade(
        cls,
        linha: Mapping[str, Any] | pd.Series,
        atributos_map: Mapping[str, str],
    ) -> dict[str, Any]:
        """
        Mapeia atributos da feição mais próxima, preservando `float` para grandezas
        elétricas (`_kv`, `_mw`) utilizadas nos cálculos de ameaça da camada Gold.
        """
        attrs: dict[str, Any] = {}
        for nome_saida, nome_coluna in atributos_map.items():
            valor = linha.get(nome_coluna, NOT_INFORMED)
            if nome_saida.endswith("_kv") or nome_saida.endswith("_mw"):
                attrs[nome_saida] = cls.normalizar_float(valor)
            else:
                attrs[nome_saida] = cls.normalizar_texto(valor)
        return attrs
