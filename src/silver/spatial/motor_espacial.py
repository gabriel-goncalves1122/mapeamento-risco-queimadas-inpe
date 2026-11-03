"""
Orquestrador de consultas espaciais em memória (`MotorEspacial`).

Delega a instanciação das 7 camadas espaciais e o template de resultado vazio ao
`SpatialLayerCatalog` (SRP / OCP), mantendo a responsabilidade única de cruzar um
ponto `(latitude, longitude)` contra as camadas de interseção e proximidade.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping

import geopandas as gpd
from shapely.geometry import Point

from src.core.config import settings
from src.core.config.constants import DISTANCE_LIMITS_KM, EPSG_GPS, EPSG_METRICO, NOT_INFORMED
from src.core.config.settings import PipelineSettings
from src.silver.spatial.layers import SpatialLayer
from src.silver.spatial.spatial_layer_catalog import SpatialLayerCatalog
from src.silver.utils.df_helpers import coordenada_valida

logger = logging.getLogger(__name__)


class MotorEspacial:
    """
    Orquestrador de consultas vetoriais R-Tree contra as dimensões Silver.

    Implementa `SpatialEngineProtocol` (DIP / ISP) expondo `analisar_todas_ameacas`
    e `intersecoes_camada`, aceitando injeção de `settings_obj` ou `camadas` prontas.
    """

    DIST_LIMITES_KM = list(DISTANCE_LIMITS_KM)
    OUTPUT_ID_KEYS = dict(SpatialLayerCatalog.OUTPUT_ID_KEYS)

    def __init__(
        self,
        settings_obj: PipelineSettings | Any | None = None,
        camadas: Mapping[str, SpatialLayer] | None = None,
    ) -> None:
        logger.info("Inicializando Motor Espacial orientado a objetos via SpatialLayerCatalog.")
        cfg = settings_obj or settings

        # Passa `layer_cls=SpatialLayer` do escopo deste módulo para preservar compatibilidade com `@patch`
        catalogo = (
            dict(camadas)
            if camadas is not None
            else SpatialLayerCatalog.build_layers(cfg, layer_cls=SpatialLayer)
        )

        self.camada_funai = catalogo["camada_funai"]
        self.camada_municipios = catalogo["camada_municipios"]
        self.camada_rodovias = catalogo["camada_rodovias"]
        self.camada_linhas = catalogo["camada_linhas"]
        self.camada_subestacoes = catalogo["camada_subestacoes"]
        self.camada_sistemas = catalogo["camada_sistemas"]
        self.camada_hospitais = catalogo["camada_hospitais"]

        self.camadas_proximidade = [
            getattr(self, key) for key in SpatialLayerCatalog.PROXIMITY_LAYER_KEYS
        ]

    def _resultado_base(self) -> dict[str, Any]:
        """Retorna a estrutura padrão para coordenadas ausentes ou inválidas."""
        return SpatialLayerCatalog.criar_resultado_vazio(self.DIST_LIMITES_KM)

    @staticmethod
    def _coordenada_valida(lat: Any, lon: Any) -> bool:
        return coordenada_valida(lat, lon)

    def intersecoes_camada(
        self,
        nome_camada: str,
        coordenadas: Iterable[tuple[float, float]],
    ) -> list[str]:
        """
        Consulta interseções de múltiplos pares `(lat, lon)` sobre uma camada poligonal,
        evitando que consumidores externos acessem atributos internos do motor (ISP).
        """
        camada = getattr(self, nome_camada, None)
        if camada is None or not hasattr(camada, "intersecao"):
            return []

        codigos: list[str] = []
        for lat, lon in coordenadas:
            resultado = camada.intersecao(Point(float(lon), float(lat)))
            codigo = resultado.get("id", NOT_INFORMED)
            if codigo != NOT_INFORMED:
                codigos.append(str(codigo))
        return codigos

    def analisar_todas_ameacas(self, latitude: Any, longitude: Any) -> dict[str, Any]:
        """
        Cruza um ponto WGS84 contra todas as camadas espaciais:
        polígonos por interseção (EPSG:4326) e infraestruturas por proximidade métrica (EPSG:5880).
        """
        res = self._resultado_base()
        if not self._coordenada_valida(latitude, longitude):
            return res

        lat = float(str(latitude).strip().replace(",", "."))
        lon = float(str(longitude).strip().replace(",", "."))

        ponto_gps = Point(lon, lat)
        ponto_metrico = (
            gpd.GeoSeries([ponto_gps], crs=f"EPSG:{EPSG_GPS}")
            .to_crs(epsg=EPSG_METRICO)
            .iloc[0]
        )

        # 1. Interseção administrativa com Municípios (EPSG:4326)
        mun = self.camada_municipios.intersecao(ponto_gps)
        res["codigo_ibge_espacial"] = mun["id"]
        res["foco_em_municipio_mapeado"] = mun["flag"]
        res.update(mun["attrs"])

        # 2. Interseção e proximidade híbrida com Terras Indígenas FUNAI
        ti_inter = self.camada_funai.intersecao(ponto_gps)
        res["codigo_ti"] = ti_inter["id"]
        res["foco_em_terra_indigena"] = ti_inter["flag"]
        if ti_inter["flag"] == 1:
            res.update(ti_inter["attrs"])

        ti_prox = self.camada_funai.proximidade(ponto_metrico)
        res["codigo_ti_proxima"] = ti_prox["terra_indigena_id_proximo"]
        res["distancia_terra_indigena_km"] = ti_prox["distancia_terra_indigena_km"]
        res["faixa_distancia_terra_indigena"] = ti_prox["faixa_distancia_terra_indigena"]
        for limite in self.DIST_LIMITES_KM:
            res[f"terra_indigena_ate_{limite}km"] = ti_prox[f"terra_indigena_ate_{limite}km"]

        if ti_inter["flag"] == 0:
            res.update(ti_prox["attrs"])

        # 3. Proximidade métrica para infraestruturas críticas (EPSG:5880)
        for camada in self.camadas_proximidade:
            prox = camada.proximidade(ponto_metrico)
            prefixo = camada.prefixo
            chave_id = getattr(camada, "output_id_key", None) or self.OUTPUT_ID_KEYS.get(prefixo)
            if chave_id in self.OUTPUT_ID_KEYS.values():
                res[chave_id] = prox[f"{prefixo}_id_proximo"]
            elif prefixo in self.OUTPUT_ID_KEYS:
                res[self.OUTPUT_ID_KEYS[prefixo]] = prox[f"{prefixo}_id_proximo"]

            res[f"distancia_{prefixo}_km"] = prox[f"distancia_{prefixo}_km"]
            res[f"faixa_distancia_{prefixo}"] = prox[f"faixa_distancia_{prefixo}"]
            res.update(prox["attrs"])

            for limite in self.DIST_LIMITES_KM:
                res[f"{prefixo}_ate_{limite}km"] = prox[f"{prefixo}_ate_{limite}km"]

        return res
