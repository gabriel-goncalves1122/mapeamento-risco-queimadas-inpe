"""
Objeto de valor dos hiperparâmetros do agrupamento ST-DBSCAN (`EventoConfig`).

Isola a configuração espaço-temporal (raio métrico `eps_km`, raio temporal `eps_dias`,
densidade mínima `min_samples`, janela máxima e buffer geométrico) da lógica de
clusterização do `EventizadorIncendios` (SRP).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.config import settings


@dataclass(frozen=True)
class EventoConfig:
    """Hiperparâmetros imutáveis para eventização espaço-temporal ST-DBSCAN."""

    eps_km: float = 5.0
    eps_dias: float = 2.0
    min_samples: int = 3
    max_duration_days: float = 7.0
    area_buffer_km: float = 0.5

    @classmethod
    def from_settings(cls, cfg: Any = settings) -> EventoConfig:
        """Constrói `EventoConfig` lendo `PipelineSettings` ou o módulo `src.core.config.settings`."""
        return cls(
            eps_km=float(getattr(cfg, "eventos_eps_km", getattr(cfg, "EVENTOS_EPS_KM", settings.EVENTOS_EPS_KM))),
            eps_dias=float(
                getattr(cfg, "eventos_eps_dias", getattr(cfg, "EVENTOS_EPS_DIAS", settings.EVENTOS_EPS_DIAS))
            ),
            min_samples=int(
                getattr(cfg, "eventos_min_samples", getattr(cfg, "EVENTOS_MIN_SAMPLES", settings.EVENTOS_MIN_SAMPLES))
            ),
            max_duration_days=float(
                getattr(
                    cfg,
                    "eventos_max_duration_days",
                    getattr(cfg, "EVENTOS_MAX_DURATION_DAYS", settings.EVENTOS_MAX_DURATION_DAYS),
                )
            ),
            area_buffer_km=float(
                getattr(
                    cfg,
                    "eventos_area_buffer_km",
                    getattr(cfg, "EVENTOS_AREA_BUFFER_KM", settings.EVENTOS_AREA_BUFFER_KM),
                )
            ),
        )
