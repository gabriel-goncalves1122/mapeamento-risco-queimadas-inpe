"""
Serviço de agregação estatística para benchmarks do Apache Druid (`BenchmarkStatisticsService`).

Calcula percentis interpolados (p50, p90, p95, p99), QPS, taxa de erro, ponto de
saturação e ganho percentual de cache (`cold` vs. `warm`) (SRP).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


class BenchmarkStatisticsService:
    """Serviço puro de sumarização de latências, vazão e ganho de cache."""

    @staticmethod
    def percentile(valores: Sequence[float], percentil: float) -> float | None:
        """Calcula o percentil por interpolação linear contínua."""
        if not valores:
            return None
        ordenados = sorted(float(valor) for valor in valores)
        if len(ordenados) == 1:
            return ordenados[0]
        posicao = (len(ordenados) - 1) * (percentil / 100.0)
        baixo = int(posicao)
        alto = min(baixo + 1, len(ordenados) - 1)
        fracao = posicao - baixo
        return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * fracao

    @staticmethod
    def _media(valores: Sequence[float]) -> float | None:
        return sum(valores) / len(valores) if valores else None

    @staticmethod
    def _round_or_none(valor: float | None, casas: int = 3) -> float | None:
        return round(valor, casas) if valor is not None else None

    @classmethod
    def summarizar_registros(
        cls,
        records: Sequence[Mapping[str, Any]],
        group_fields: Sequence[str],
        max_p95_ms: float,
        max_error_rate: float,
    ) -> list[dict[str, Any]]:
        """Agrupa requisições brutas por `group_fields` e calcula métricas de cauda e saturação."""
        grupos: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
        for record in records:
            chave = tuple(record[field] for field in group_fields)
            grupos.setdefault(chave, []).append(record)

        linhas: list[dict[str, Any]] = []
        for chave, itens in sorted(grupos.items(), key=lambda item: item[0]):
            sucessos = [item for item in itens if item["status"] == "OK"]
            erros = len(itens) - len(sucessos)
            latencias = [float(item["latencia_ms"]) for item in sucessos]
            inicio = min(float(item["started_epoch"]) for item in itens)
            fim = max(float(item["ended_epoch"]) for item in itens)
            duracao_s = max(fim - inicio, 0.001)
            p95 = cls.percentile(latencias, 95)
            error_rate = (erros / len(itens)) * 100.0 if itens else 0.0

            linha: dict[str, Any] = {field: chave[indice] for indice, field in enumerate(group_fields)}
            linha.update(
                {
                    "requests_total": len(itens),
                    "requests_ok": len(sucessos),
                    "requests_erro": erros,
                    "error_rate_percent": round(error_rate, 3),
                    "duration_s": round(duracao_s, 3),
                    "qps": round(len(itens) / duracao_s, 3),
                    "lat_min_ms": cls._round_or_none(min(latencias) if latencias else None),
                    "lat_avg_ms": cls._round_or_none(cls._media(latencias)),
                    "lat_p50_ms": cls._round_or_none(cls.percentile(latencias, 50)),
                    "lat_p90_ms": cls._round_or_none(cls.percentile(latencias, 90)),
                    "lat_p95_ms": cls._round_or_none(p95),
                    "lat_p99_ms": cls._round_or_none(cls.percentile(latencias, 99)),
                    "lat_max_ms": cls._round_or_none(max(latencias) if latencias else None),
                    "linhas_retornadas_total": sum(int(item["linhas_retornadas"]) for item in sucessos),
                    "bytes_retornados_total": sum(int(item["bytes_retornados"]) for item in sucessos),
                    "saturado": bool(
                        error_rate >= max_error_rate or (p95 is not None and p95 >= max_p95_ms)
                    ),
                }
            )
            linhas.append(linha)
        return linhas

    @staticmethod
    def primeiro_ponto_saturacao(
        summary_by_concurrency: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any] | None:
        """Retorna o primeiro nível de concorrência que atingiu saturação operacional."""
        for row in sorted(summary_by_concurrency, key=lambda item: int(item["concurrency"])):
            if row.get("saturado"):
                return row
        return None

    @staticmethod
    def _percent_gain(cold: Any, warm: Any) -> float | None:
        try:
            cold_f = float(cold)
            warm_f = float(warm)
        except (TypeError, ValueError):
            return None
        if cold_f <= 0:
            return None
        return round(((cold_f - warm_f) / cold_f) * 100.0, 3)

    @classmethod
    def calcular_ganho_cache(cls, summary_by_query: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Compara execuções `cold` e `warm` de cada query para medir o ganho de cache."""
        grupos: dict[tuple[Any, ...], dict[Any, Mapping[str, Any]]] = {}
        for row in summary_by_query:
            chave = (
                row.get("profile"),
                row.get("capacity_scenario"),
                row.get("scenario"),
                row.get("query_id"),
            )
            grupos.setdefault(chave, {})[row.get("cache_mode")] = row

        ganhos: list[dict[str, Any]] = []
        for chave, por_cache in sorted(grupos.items(), key=lambda item: item[0]):
            cold = por_cache.get("cold")
            warm = por_cache.get("warm")
            if not cold or not warm:
                continue
            ganhos.append(
                {
                    "profile": chave[0],
                    "capacity_scenario": chave[1],
                    "scenario": chave[2],
                    "query_id": chave[3],
                    "requests_cold": cold.get("requests_total"),
                    "requests_warm": warm.get("requests_total"),
                    "cold_avg_ms": cold.get("lat_avg_ms"),
                    "warm_avg_ms": warm.get("lat_avg_ms"),
                    "avg_gain_percent": cls._percent_gain(cold.get("lat_avg_ms"), warm.get("lat_avg_ms")),
                    "cold_p95_ms": cold.get("lat_p95_ms"),
                    "warm_p95_ms": warm.get("lat_p95_ms"),
                    "p95_gain_percent": cls._percent_gain(cold.get("lat_p95_ms"), warm.get("lat_p95_ms")),
                    "cold_error_rate_percent": cold.get("error_rate_percent"),
                    "warm_error_rate_percent": warm.get("error_rate_percent"),
                }
            )
        return ganhos


percentile = BenchmarkStatisticsService.percentile
summarizar_registros = BenchmarkStatisticsService.summarizar_registros
primeiro_ponto_saturacao = BenchmarkStatisticsService.primeiro_ponto_saturacao
calcular_ganho_cache = BenchmarkStatisticsService.calcular_ganho_cache
