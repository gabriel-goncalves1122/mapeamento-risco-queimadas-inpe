"""
Camada espacial indexada em memória (`SpatialLayer`).

Foca exclusivamente nas consultas vetoriais sobre o índice R-Tree (`intersecao`
em WGS84 e `proximidade` em EPSG:5880), delegando o carregamento/reprojeção de
arquivos ao `SpatialLayerLoader` e a discretização de distâncias ao
`DistanceClassifier` (SRP / DIP).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import geopandas as gpd
from shapely.geometry import Point

from src.core.config.constants import DISTANCE_LIMITS_KM, NOT_INFORMED
from src.silver.spatial.distance_classifier import DistanceClassifier
from src.silver.spatial.spatial_layer_loader import SpatialLayerLoader
from src.silver.spatial.spatial_layer_spec import SpatialLayerSpec


class SpatialLayer:
    """
    Executa consultas espaciais `intersects` e `nearest` sobre `GeoDataFrame`s indexados.

    Aceita `loader`, `classifier` ou `gdf_gps`/`gdf_metrico` pré-construídos via
    construtor para permitir testes unitários rápidos em memória sem I/O de disco (DIP).
    """

    DIST_LIMITES_KM = list(DISTANCE_LIMITS_KM)

    def __init__(
        self,
        path: str | Path,
        nome: str,
        col_id: str,
        prefixo: str,
        atributos_map: Mapping[str, str],
        projetar_metrico: bool = False,
        tipo_geometria: str = "point",
        output_id_key: str | None = None,
        loader: SpatialLayerLoader | None = None,
        classifier: DistanceClassifier | None = None,
        gdf_gps: gpd.GeoDataFrame | None = None,
        gdf_metrico: gpd.GeoDataFrame | None = None,
    ) -> None:
        self.nome = nome
        self.col_id = col_id
        self.prefixo = prefixo
        self.atributos_map = dict(atributos_map)
        self.projetar_metrico = projetar_metrico
        self.tipo_geometria = tipo_geometria
        self.output_id_key = output_id_key or f"{prefixo}_id_proximo"

        self._loader = loader or SpatialLayerLoader()
        self._classifier = classifier or DistanceClassifier(self.DIST_LIMITES_KM)

        if gdf_gps is not None:
            self.gdf_gps = gdf_gps
            self.gdf_metrico = gdf_metrico
        else:
            self.gdf_gps, self.gdf_metrico = self._loader.carregar(
                path=path,
                nome=nome,
                tipo_geometria=tipo_geometria,
                projetar_metrico=projetar_metrico,
            )

    @classmethod
    def from_spec(
        cls,
        spec: SpatialLayerSpec,
        loader: SpatialLayerLoader | None = None,
        classifier: DistanceClassifier | None = None,
    ) -> SpatialLayer:
        """Factory Method que instancia a camada a partir de um `SpatialLayerSpec`."""
        return cls(
            path=spec.path,
            nome=spec.nome,
            col_id=spec.col_id,
            prefixo=spec.prefixo,
            atributos_map=spec.atributos_map,
            projetar_metrico=spec.projetar_metrico,
            tipo_geometria=spec.tipo_geometria,
            output_id_key=spec.output_id_key,
            loader=loader,
            classifier=classifier,
        )

    def _carregar(self, path: str | Path) -> None:
        """Recarrega os `GeoDataFrame`s da camada delegando ao `SpatialLayerLoader`."""
        self.gdf_gps, self.gdf_metrico = self._loader.carregar(
            path=path,
            nome=self.nome,
            tipo_geometria=self.tipo_geometria,
            projetar_metrico=self.projetar_metrico,
        )

    def _path_json_para_geom(self, valor: Any) -> Any:
        return self._loader.path_json_para_geom(valor, tipo_geometria=self.tipo_geometria, nome=self.nome)

    # Aliases estáticos delegados para preservar retrocompatibilidade de chamadas internas
    _wkt_para_geom = staticmethod(SpatialLayerLoader.wkt_para_geom)
    _normalizar_coord = staticmethod(SpatialLayerLoader.normalizar_coord)
    _normalizar_id = staticmethod(DistanceClassifier.normalizar_id)
    _normalizar_texto = staticmethod(DistanceClassifier.normalizar_texto)
    _normalizar_float = staticmethod(DistanceClassifier.normalizar_float)
    _faixa_distancia = staticmethod(DistanceClassifier.faixa_distancia)
    _flag_ate = staticmethod(DistanceClassifier.flag_ate)

    def intersecao(self, ponto_gps: Point) -> dict[str, Any]:
        """Consulta a R-Tree (`intersects`) para determinar se o ponto WGS84 cai no polígono."""
        vazio: dict[str, Any] = {"id": NOT_INFORMED, "flag": 0, "attrs": {}}
        if self.gdf_gps is None or self.gdf_gps.empty:
            return vazio

        try:
            idxs = self.gdf_gps.sindex.query(ponto_gps, predicate="intersects")
            if len(idxs) == 0:
                return vazio

            linha = self.gdf_gps.iloc[idxs[0]]
            return {
                "id": self._classifier.normalizar_id(linha.get(self.col_id, NOT_INFORMED)),
                "flag": 1,
                "attrs": self._classifier.extrair_atributos_intersecao(linha, self.atributos_map),
            }
        except Exception:
            return vazio

    def proximidade(self, ponto_metrico: Point) -> dict[str, Any]:
        """Localiza a feição mais próxima via `sindex.nearest` e calcula a distância em km."""
        resultado: dict[str, Any] = {
            f"{self.prefixo}_id_proximo": NOT_INFORMED,
            f"distancia_{self.prefixo}_km": None,
            f"faixa_distancia_{self.prefixo}": "SEM_DISTANCIA",
            **self._classifier.flags_por_limite(self.prefixo, None),
            "attrs": {},
        }

        gdf_alvo = self.gdf_metrico if self.projetar_metrico else self.gdf_gps
        if gdf_alvo is None or gdf_alvo.empty:
            return resultado

        try:
            idx_nearest = gdf_alvo.sindex.nearest(ponto_metrico)[1][0]
            linha_alvo = gdf_alvo.iloc[idx_nearest]

            # EPSG:5880 fornece distância euclidiana em metros; dividimos por 1000 para km
            distancia_km = round(ponto_metrico.distance(linha_alvo.geometry) / 1000.0, 3)

            resultado[f"{self.prefixo}_id_proximo"] = self._classifier.normalizar_id(
                linha_alvo.get(self.col_id, NOT_INFORMED)
            )
            resultado[f"distancia_{self.prefixo}_km"] = distancia_km
            resultado[f"faixa_distancia_{self.prefixo}"] = self._classifier.faixa_distancia(distancia_km)
            resultado.update(self._classifier.flags_por_limite(self.prefixo, distancia_km))
            resultado["attrs"] = self._classifier.extrair_atributos_proximidade(
                linha_alvo,
                self.atributos_map,
            )
            return resultado
        except Exception:
            return resultado


__all__ = ["SpatialLayer", "SpatialLayerSpec"]
