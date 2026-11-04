"""
Eventização espaço-temporal de focos de incêndio via ST-DBSCAN (`EventizadorIncendios`).

Agrupa focos brutos do INPE em janelas temporais fechadas, delega a construção de
polígonos métricos ao `EventGeometryBuilder` (SRP) e emite payloads validados pelo
contrato `EventoFatoPayload` para o Apache Druid/Superset.
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
from collections import Counter
from typing import Any, Iterable

import geopandas as gpd
import pandas as pd

pd.set_option("future.no_silent_downcasting", True)

from shapely.geometry import Point
from sklearn.cluster import DBSCAN

from src.core.config import settings
from src.core.config.constants import (
    BRAZIL_LAT_MAX,
    BRAZIL_LAT_MIN,
    BRAZIL_LON_MAX,
    BRAZIL_LON_MIN,
    NOT_INFORMED,
)
from src.core.contracts.contracts import ExecutablePipelineStep, SpatialEngineProtocol
from src.core.domain.evento_fato_payload import EventoFatoPayload
from src.gold.science.dbscan.event_geometry_builder import EventGeometryBuilder
from src.gold.science.dbscan.evento_config import EventoConfig
from src.silver.streaming_processing.processors.calculators import (
    calcular_indices_ameaca,
    indice_condicao_ambiental,
    indice_queimada_evento,
)
from src.silver.utils.cleaners import limpar_texto_druid, limpar_valor_numerico_nullable

logger = logging.getLogger(__name__)


class EventizadorIncendios(ExecutablePipelineStep):
    """
    Agrupa anomalias térmicas pontuais em eventos agregados (`FATO_EVENTOS_INCENDIO`).

    Depende de `SpatialEngineProtocol` (DIP / ISP) para resolver proximidade às
    infraestruturas críticas e de `EventGeometryBuilder` (SRP) para construir o
    polígono `convex_hull` em projeção policônica métrica (EPSG:5880).
    """

    COLUNAS_BRUTAS = [
        "DataHora",
        "Satelite",
        "Pais",
        "Estado",
        "Municipio",
        "Bioma",
        "DiaSemChuva",
        "Precipitacao",
        "RiscoFogo",
        "FRP",
        "Latitude",
        "Longitude",
    ]

    def __init__(
        self,
        motor_espacial: SpatialEngineProtocol | Any | None = None,
        config: EventoConfig | None = None,
        geometry_builder: EventGeometryBuilder | None = None,
    ) -> None:
        self.motor = motor_espacial
        self.config = config or EventoConfig()
        self.geometry_builder = geometry_builder or EventGeometryBuilder(
            area_buffer_km=self.config.area_buffer_km
        )

    def preparar_focos(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Higieniza coordenadas, timestamps e métricas climáticas antes da clusterização,
        descartando pontos sem FRP positivo ou fora do território brasileiro.
        """
        df = df_bruto.copy()
        for coluna in self.COLUNAS_BRUTAS:
            if coluna not in df.columns:
                df[coluna] = None

        df["datahora_dt"] = pd.to_datetime(df["DataHora"], errors="coerce")
        df["latitude"] = df["Latitude"].apply(limpar_valor_numerico_nullable)
        df["longitude"] = df["Longitude"].apply(limpar_valor_numerico_nullable)
        df["frp"] = df["FRP"].apply(limpar_valor_numerico_nullable).fillna(0.0)
        df["risco_fogo"] = df["RiscoFogo"].apply(limpar_valor_numerico_nullable).fillna(0.0)
        df["dias_sem_chuva"] = df["DiaSemChuva"].apply(limpar_valor_numerico_nullable).fillna(0.0)
        df["precipitacao_mm"] = df["Precipitacao"].apply(limpar_valor_numerico_nullable).fillna(0.0)

        mascara = (
            df["datahora_dt"].notna()
            & (df["frp"] > 0.0)
            & df["latitude"].between(BRAZIL_LAT_MIN, BRAZIL_LAT_MAX)
            & df["longitude"].between(BRAZIL_LON_MIN, BRAZIL_LON_MAX)
            & ~((df["latitude"] == 0.0) & (df["longitude"] == 0.0))
        )
        df = df.loc[mascara].copy()
        if df.empty:
            return df

        df["pais_origem"] = df["Pais"].apply(limpar_texto_druid)
        df["fk_bioma"] = df["Bioma"].apply(limpar_texto_druid)
        df["fk_satelite_sensor"] = df["Satelite"].apply(limpar_texto_druid)
        df["indice_condicao_ambiental"] = [
            indice_condicao_ambiental(risco, dias, chuva)
            for risco, dias, chuva in zip(df["risco_fogo"], df["dias_sem_chuva"], df["precipitacao_mm"])
        ]
        df["indice_queimada_evento"] = [
            indice_queimada_evento(frp, risco, dias, chuva)
            for frp, risco, dias, chuva in zip(
                df["frp"],
                df["risco_fogo"],
                df["dias_sem_chuva"],
                df["precipitacao_mm"],
            )
        ]

        segundos_janela = max(self.config.max_duration_days, 1.0) * 24 * 3600
        epoch = pd.Timestamp("1970-01-01")
        df["janela_evento"] = (
            (df["datahora_dt"] - epoch).dt.total_seconds() // segundos_janela
        ).astype("int64")
        return df.sort_values("datahora_dt")

    def eventizar_focos(self, df_focos: pd.DataFrame) -> list[dict[str, Any]]:
        """Retorna payloads de eventos para um DataFrame bruto ou já preparado."""
        if "datahora_dt" not in df_focos.columns:
            df_focos = self.preparar_focos(df_focos)
        if df_focos.empty:
            return []

        eventos: list[dict[str, Any]] = []
        for _, grupo_janela in df_focos.groupby("janela_evento", sort=True):
            eventos.extend(self._eventizar_janela(grupo_janela))
        return eventos

    def _eventizar_janela(self, grupo_janela: pd.DataFrame) -> list[dict[str, Any]]:
        if len(grupo_janela) < self.config.min_samples:
            return []

        pontos_metricos = self.geometry_builder.pontos_metricos(grupo_janela)
        trabalho = grupo_janela.copy()
        trabalho["x_km"] = pontos_metricos.x / 1000.0
        trabalho["y_km"] = pontos_metricos.y / 1000.0

        min_time = trabalho["datahora_dt"].min()
        trabalho["tempo_dias"] = (
            (trabalho["datahora_dt"] - min_time).dt.total_seconds() / (24 * 3600)
        )
        # Escala a dimensão temporal para a mesma métrica espacial de eps_km no DBSCAN 3D
        trabalho["tempo_escalado_km"] = trabalho["tempo_dias"] * (
            self.config.eps_km / max(self.config.eps_dias, 0.001)
        )

        matriz = trabalho[["x_km", "y_km", "tempo_escalado_km"]].to_numpy()
        labels = DBSCAN(
            eps=self.config.eps_km,
            min_samples=self.config.min_samples,
            n_jobs=1,
        ).fit_predict(matriz)
        trabalho["cluster_evento"] = labels

        eventos: list[dict[str, Any]] = []
        for cluster_id, grupo_cluster in trabalho[trabalho["cluster_evento"] != -1].groupby("cluster_evento"):
            if len(grupo_cluster) < self.config.min_samples:
                continue
            eventos.append(self._montar_payload_evento(grupo_cluster, int(cluster_id)))
        return eventos

    @staticmethod
    def _pontos_metricos(df: pd.DataFrame) -> gpd.GeoSeries:
        return EventGeometryBuilder.pontos_metricos(df)

    def _geometria_evento(self, grupo: pd.DataFrame) -> tuple[Any, float, float, float]:
        return self.geometry_builder.construir_geometria(grupo)

    def _montar_payload_evento(self, grupo: pd.DataFrame, cluster_id: int) -> dict[str, Any]:
        grupo = grupo.sort_values("datahora_dt")
        data_inicio = grupo["datahora_dt"].min()
        data_fim = grupo["datahora_dt"].max()
        duracao_horas = max((data_fim - data_inicio).total_seconds() / 3600.0, 0.0)

        geom_gps, centroide_lat, centroide_lon, area_km2 = self._geometria_evento(grupo)
        path_json = self.geometry_builder.serializar_path_json(geom_gps)
        analise = self._analise_espacial_evento(grupo, centroide_lat, centroide_lon)

        soma_frp = self._soma(grupo["frp"])
        max_frp = self._max(grupo["frp"])
        max_risco = self._max(grupo["risco_fogo"])

        indices = calcular_indices_ameaca(
            frp=soma_frp,
            risco=max_risco,
            dist_rodovia=analise.get("distancia_rodovia_km"),
            dist_linha=analise.get("distancia_linha_km"),
            dist_sub=analise.get("distancia_subestacao_km"),
            dist_sis=analise.get("distancia_sistema_isolado_km"),
            dist_hosp=analise.get("distancia_hospital_km"),
            dist_ti=analise.get("distancia_terra_indigena_km"),
            tensao_kv=analise.get("linha_tensao_kv"),
            capac_mw=analise.get("subestacao_capacidade_mw"),
        )
        indice_pressao_maxima = max(indices.values()) if indices else 0.0

        payload = EventoFatoPayload(
            fire_event_id=self._gerar_event_id(grupo, cluster_id, centroide_lat, centroide_lon),
            data_inicio=data_inicio.strftime("%Y-%m-%d %H:%M:%S"),
            data_fim=data_fim.strftime("%Y-%m-%d %H:%M:%S"),
            pais_origem=self._modo(grupo["pais_origem"]),
            fk_bioma=self._modo(grupo["fk_bioma"]),
            fk_satelite_sensor=self._modo(grupo["fk_satelite_sensor"]),
            fk_municipio_principal=analise["fk_municipio_principal"],
            codigos_ibge_interceptados=analise["codigos_ibge_interceptados"],
            qtd_municipios_interceptados=self._qtd_codigos_validos(analise["codigos_ibge_interceptados"]),
            fk_terra_indigena=analise["fk_terra_indigena"],
            codigos_ti_interceptadas=analise["codigos_ti_interceptadas"],
            qtd_terras_indigenas_interceptadas=self._qtd_codigos_validos(analise["codigos_ti_interceptadas"]),
            fk_terra_indigena_proxima=analise["fk_terra_indigena_proxima"],
            fk_trecho_rodoviario=analise["fk_trecho_rodoviario"],
            fk_linha_transmissao=analise["fk_linha_transmissao"],
            fk_subestacao=analise["fk_subestacao"],
            fk_sistema_isolado=analise["fk_sistema_isolado"],
            fk_hospital=analise["fk_hospital"],
            latitude_centroide=round(centroide_lat, 6),
            longitude_centroide=round(centroide_lon, 6),
            path_json=path_json,
            total_focos=int(len(grupo)),
            duracao_horas=round(duracao_horas, 6),
            duracao_dias=round(duracao_horas / 24.0, 6),
            area_evento_km2=area_km2,
            soma_frp=soma_frp,
            media_frp=self._media(grupo["frp"]),
            max_frp=max_frp,
            media_risco_fogo=self._media(grupo["risco_fogo"]),
            max_risco_fogo=max_risco,
            media_dias_sem_chuva=self._media(grupo["dias_sem_chuva"]),
            media_precipitacao_mm=self._media(grupo["precipitacao_mm"]),
            indice_condicao_ambiental_medio=self._media(grupo["indice_condicao_ambiental"]),
            indice_queimada_evento_medio=self._media(grupo["indice_queimada_evento"]),
            indice_queimada_evento_max=self._max(grupo["indice_queimada_evento"]),
            distancia_rodovia_km=analise.get("distancia_rodovia_km"),
            distancia_linha_km=analise.get("distancia_linha_km"),
            distancia_subestacao_km=analise.get("distancia_subestacao_km"),
            distancia_sistema_isolado_km=analise.get("distancia_sistema_isolado_km"),
            distancia_hospital_km=analise.get("distancia_hospital_km"),
            distancia_terra_indigena_km=analise.get("distancia_terra_indigena_km"),
            indice_ameaca_rodovia=indices["indice_ameaca_rodovia"],
            indice_ameaca_linha=indices["indice_ameaca_linha"],
            indice_ameaca_subestacao=indices["indice_ameaca_subestacao"],
            indice_ameaca_sistema_isolado=indices["indice_ameaca_sistema_isolado"],
            indice_pressao_saude=indices["indice_pressao_saude"],
            indice_pressao_terra_indigena=indices["indice_pressao_terra_indigena"],
            indice_pressao_maxima=round(indice_pressao_maxima, 6),
            param_eps_km=self.config.eps_km,
            param_eps_dias=self.config.eps_dias,
            param_min_samples=self.config.min_samples,
            param_max_duration_days=self.config.max_duration_days,
        )
        return payload.model_dump(mode="json")

    def _analise_espacial_evento(
        self,
        grupo: pd.DataFrame,
        lat: float,
        lon: float,
    ) -> dict[str, Any]:
        analise_centroide: dict[str, Any] = {}
        if self.motor is not None and hasattr(self.motor, "analisar_todas_ameacas"):
            analise_centroide = self.motor.analisar_todas_ameacas(lat, lon) or {}

        municipios = self._intersecoes_por_ponto(grupo, "camada_municipios")
        terras = self._intersecoes_por_ponto(grupo, "camada_funai")

        municipio_principal = self._mais_frequente(
            municipios,
            analise_centroide.get("codigo_ibge_espacial", NOT_INFORMED),
        )
        terra_principal = self._mais_frequente(
            terras,
            analise_centroide.get("codigo_ti", NOT_INFORMED),
        )

        return {
            "fk_municipio_principal": municipio_principal,
            "codigos_ibge_interceptados": self._lista_ou_nao_informado(municipios, municipio_principal),
            "fk_terra_indigena": terra_principal,
            "codigos_ti_interceptadas": self._lista_ou_nao_informado(terras, terra_principal),
            "fk_terra_indigena_proxima": analise_centroide.get("codigo_ti_proxima", NOT_INFORMED),
            "fk_trecho_rodoviario": analise_centroide.get("id_trecho_rodoviario", NOT_INFORMED),
            "fk_linha_transmissao": analise_centroide.get("id_linha_transmissao", NOT_INFORMED),
            "fk_subestacao": analise_centroide.get("id_subestacao", NOT_INFORMED),
            "fk_sistema_isolado": analise_centroide.get("id_sistema_isolado", NOT_INFORMED),
            "fk_hospital": analise_centroide.get("codigo_cnes_prox", NOT_INFORMED),
            "distancia_rodovia_km": analise_centroide.get("distancia_rodovia_km"),
            "distancia_linha_km": analise_centroide.get("distancia_linha_km"),
            "distancia_subestacao_km": analise_centroide.get("distancia_subestacao_km"),
            "distancia_sistema_isolado_km": analise_centroide.get("distancia_sistema_isolado_km"),
            "distancia_hospital_km": analise_centroide.get("distancia_hospital_km"),
            "distancia_terra_indigena_km": analise_centroide.get("distancia_terra_indigena_km"),
            "linha_tensao_kv": analise_centroide.get("linha_tensao_kv"),
            "subestacao_capacidade_mw": analise_centroide.get("subestacao_capacidade_mw"),
        }

    def _intersecoes_por_ponto(self, grupo: pd.DataFrame, nome_camada: str) -> list[str]:
        if self.motor is None:
            return []

        coords_df = grupo[["latitude", "longitude"]].drop_duplicates()
        pares = [(float(foco.latitude), float(foco.longitude)) for foco in coords_df.itertuples(index=False)]

        if hasattr(self.motor, "intersecoes_camada"):
            return self.motor.intersecoes_camada(nome_camada, pares)

        if not hasattr(self.motor, nome_camada):
            return []
        camada = getattr(self.motor, nome_camada)
        codigos: list[str] = []
        for lat, lon in pares:
            resultado = camada.intersecao(Point(lon, lat))
            codigo = resultado.get("id", NOT_INFORMED)
            if codigo != NOT_INFORMED:
                codigos.append(str(codigo))
        return codigos

    @staticmethod
    def _lista_ou_nao_informado(valores: Iterable[str], fallback: str) -> list[str]:
        limpos = sorted({str(valor) for valor in valores if valor and valor != NOT_INFORMED})
        if limpos:
            return limpos
        if fallback and fallback != NOT_INFORMED:
            return [str(fallback)]
        return [NOT_INFORMED]

    @staticmethod
    def _qtd_codigos_validos(valores: Iterable[str]) -> int:
        return len([valor for valor in valores if valor and valor != NOT_INFORMED])

    @staticmethod
    def _mais_frequente(valores: Iterable[str], fallback: str) -> str:
        limpos = [str(valor) for valor in valores if valor and valor != NOT_INFORMED]
        if not limpos:
            return fallback or NOT_INFORMED
        return Counter(limpos).most_common(1)[0][0]

    @staticmethod
    def _modo(serie: pd.Series) -> str:
        valores = [str(valor) for valor in serie.dropna() if str(valor).strip()]
        if not valores:
            return NOT_INFORMED
        return Counter(valores).most_common(1)[0][0]

    @staticmethod
    def _media(serie: pd.Series) -> float:
        valor = pd.to_numeric(serie, errors="coerce").dropna().mean()
        if pd.isna(valor) or math.isinf(float(valor)):
            return 0.0
        return round(float(valor), 6)

    @staticmethod
    def _soma(serie: pd.Series) -> float:
        valor = pd.to_numeric(serie, errors="coerce").fillna(0.0).sum()
        return round(float(valor), 6)

    @staticmethod
    def _max(serie: pd.Series) -> float:
        valores = pd.to_numeric(serie, errors="coerce").dropna()
        if valores.empty:
            return 0.0
        return round(float(valores.max()), 6)

    @staticmethod
    def _gerar_event_id(grupo: pd.DataFrame, cluster_id: int, lat: float, lon: float) -> str:
        inicio = grupo["datahora_dt"].min().strftime("%Y%m%d%H%M%S")
        fim = grupo["datahora_dt"].max().strftime("%Y%m%d%H%M%S")
        base = f"{inicio}|{fim}|{cluster_id}|{round(lat, 5)}|{round(lon, 5)}|{len(grupo)}"
        digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
        return f"EVT_{inicio}_{digest}"

    def _run(self, raw_focos_path: str | None = None, nrows: int = 5000) -> list[dict[str, Any]]:
        """Executa clusterização em lote de amostra quando acionado pelo Dagster ou CLI."""
        caminho = raw_focos_path or settings.RAW_FOCOS
        if not os.path.exists(caminho):
            logger.warning("Arquivo de focos não encontrado para eventização batch: %s", caminho)
            return []

        df_amostra = pd.read_csv(
            caminho,
            nrows=nrows,
            dtype=str,
            encoding=settings.CSV_ENCODING,
            usecols=lambda c: c in self.COLUNAS_BRUTAS,
        )
        return self.eventizar_focos(df_amostra)


def executar() -> list[dict[str, Any]]:
    """Ponto de entrada CLI e do asset `st_dbscan_fire_events`."""
    return EventizadorIncendios().execute()


__all__ = ["EventGeometryBuilder", "EventoConfig", "EventizadorIncendios", "executar"]


if __name__ == "__main__":
    executar()
