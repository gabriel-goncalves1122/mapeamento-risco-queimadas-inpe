"""
=========================================================
MÓDULO: layers.py
---------------------------------------------------------
Função Geral: Motor de processamento espacial vetorial usando R-Tree/KDTree para cálculo de distâncias.
=========================================================
"""
import pandas as pd
import geopandas as gpd
import logging
import json
import math
from shapely import wkt
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon
from config.constants import (
    DISTANCE_LIMITS_KM,
    EPSG_GPS,
    EPSG_METRICO,
    GEOMETRY_WKT_COLUMN,
    NOT_INFORMED,
    PATH_JSON_COLUMN,
)
from pipelines.silver.utils.cleaners import limpar_wkt

logger = logging.getLogger(__name__)

class SpatialLayer:
    """
    Representa uma camada espacial (dimensão geográfica).
    Gerencia seu próprio carregamento, limpeza, indexação e métodos
    de interseção (contains/intersects) e proximidade (nearest).
    """
    DIST_LIMITES_KM = list(DISTANCE_LIMITS_KM)

    def __init__(
        self,
        path,
        nome,
        col_id,
        prefixo,
        atributos_map,
        projetar_metrico=False,
        tipo_geometria="point",
    ):
        self.nome = nome
        self.col_id = col_id
        self.prefixo = prefixo
        self.atributos_map = atributos_map
        self.projetar_metrico = projetar_metrico
        self.tipo_geometria = tipo_geometria
        
        self.gdf_gps = None
        self.gdf_metrico = None

        self._carregar(path)

    def _carregar(self, path):
        try:
            df = pd.read_csv(path, dtype=str)
            if df.empty:
                logger.warning("Dimensão '%s' vazia.", self.nome)
                return

            df.columns = [str(col).strip() for col in df.columns]

            if PATH_JSON_COLUMN in df.columns:
                df['geometry'] = df[PATH_JSON_COLUMN].apply(self._path_json_para_geom)
            elif GEOMETRY_WKT_COLUMN in df.columns:
                # Compatibilidade de transição: o contrato público é path_json, mas
                # CSVs antigos ainda podem conter WKT usado apenas pelo motor Python.
                df[GEOMETRY_WKT_COLUMN] = df[GEOMETRY_WKT_COLUMN].apply(limpar_wkt)
                df['geometry'] = df[GEOMETRY_WKT_COLUMN].apply(self._wkt_para_geom)
            elif {'latitude', 'longitude'}.issubset(df.columns):
                df['latitude'] = df['latitude'].apply(self._normalizar_coord)
                df['longitude'] = df['longitude'].apply(self._normalizar_coord)
                df = df.dropna(subset=['latitude', 'longitude'])
                df = df[
                    (df['latitude'].between(-90, 90)) &
                    (df['longitude'].between(-180, 180)) &
                    ~((df['latitude'] == 0.0) & (df['longitude'] == 0.0))
                ].copy()
                df['geometry'] = gpd.points_from_xy(df['longitude'], df['latitude'])
            else:
                logger.warning(
                    "Dimensão '%s' sem %s ou latitude/longitude.",
                    self.nome,
                    GEOMETRY_WKT_COLUMN,
                )
                return

            df = df.dropna(subset=['geometry']).copy()
            if df.empty:
                logger.warning("Dimensão '%s' ficou vazia após limpeza geométrica.", self.nome)
                return

            self.gdf_gps = gpd.GeoDataFrame(df, geometry='geometry', crs=f"EPSG:{EPSG_GPS}")
            _ = self.gdf_gps.sindex

            if self.projetar_metrico:
                self.gdf_metrico = self.gdf_gps.to_crs(epsg=EPSG_METRICO)
                _ = self.gdf_metrico.sindex

            logger.info("Dimensão '%s' indexada. Total: %s registros.", self.nome, len(self.gdf_gps))
        except Exception as e:
            logger.warning("Erro ao carregar '%s': %s", self.nome, e)

    def _wkt_para_geom(self, valor):
        try:
            if pd.isna(valor):
                return None
            texto = str(valor).strip()
            if not texto or texto == NOT_INFORMED:
                return None
            geom = wkt.loads(texto)
            if geom is None or geom.is_empty:
                return None
            if not geom.is_valid:
                geom = geom.buffer(0)
            if geom is None or geom.is_empty:
                return None
            return geom
        except Exception:
            return None

    def _normalizar_coord(self, valor):
        try:
            if pd.isna(valor):
                return None
            texto = str(valor).replace(',', '.').strip()
            if not texto:
                return None
            numero = float(texto)
            if math.isnan(numero) or math.isinf(numero):
                return None
            return numero
        except Exception:
            return None

    def _coord_valida(self, valor):
        return (
            isinstance(valor, list)
            and len(valor) >= 2
            and all(isinstance(v, (int, float)) for v in valor[:2])
        )

    def _limpar_coord_path(self, valor):
        return (float(valor[0]), float(valor[1]))

    def _line_string_ou_none(self, coords):
        try:
            pontos = [self._limpar_coord_path(c) for c in coords if self._coord_valida(c)]
            if len(pontos) < 2:
                return None
            return LineString(pontos)
        except Exception:
            return None

    def _polygon_ou_none(self, coords):
        try:
            pontos = [self._limpar_coord_path(c) for c in coords if self._coord_valida(c)]
            if len(pontos) < 4:
                return None
            geom = Polygon(pontos)
            if not geom.is_valid:
                geom = geom.buffer(0)
            if geom.is_empty:
                return None
            return geom
        except Exception:
            return None

    def _path_json_para_geom(self, valor):
        """
        Reconstrói Shapely a partir do path_json persistido para Druid/Superset.
        O tipo esperado vem da camada porque Polygon e MultiLineString podem ter
        estruturas JSON parecidas quando há apenas um anel ou uma linha.
        """
        try:
            if pd.isna(valor):
                return None
            data = json.loads(str(valor))
            if not data:
                return None

            tipo = str(self.tipo_geometria).lower()

            if tipo == "point":
                if self._coord_valida(data):
                    return Point(self._limpar_coord_path(data))
                if isinstance(data, list) and data and self._coord_valida(data[0]):
                    return Point(self._limpar_coord_path(data[0]))
                return None

            if tipo == "line":
                if isinstance(data, list) and data and self._coord_valida(data[0]):
                    return self._line_string_ou_none(data)
                linhas = [self._line_string_ou_none(linha) for linha in data if isinstance(linha, list)]
                linhas = [linha for linha in linhas if linha is not None]
                if not linhas:
                    return None
                return linhas[0] if len(linhas) == 1 else MultiLineString(linhas)

            if tipo == "polygon":
                if isinstance(data, list) and data and self._coord_valida(data[0]):
                    return self._polygon_ou_none(data)
                if isinstance(data, list) and data and isinstance(data[0], list) and data[0] and self._coord_valida(data[0][0]):
                    return self._polygon_ou_none(data[0])
                poligonos = []
                for poly in data:
                    if isinstance(poly, list) and poly and isinstance(poly[0], list):
                        geom = self._polygon_ou_none(poly[0])
                        if geom is not None:
                            poligonos.append(geom)
                if not poligonos:
                    return None
                return poligonos[0] if len(poligonos) == 1 else MultiPolygon(poligonos)

            logger.warning("Tipo geométrico '%s' não reconhecido para '%s'.", self.tipo_geometria, self.nome)
            return None
        except Exception:
            return None

    def _normalizar_id(self, valor):
        if pd.isna(valor):
            return NOT_INFORMED
        texto = str(valor).strip()
        texto = texto.replace('"', '').replace('\n', ' ').replace('\r', ' ').strip()
        return texto if texto else NOT_INFORMED

    def _normalizar_texto(self, valor):
        if pd.isna(valor):
            return NOT_INFORMED
        texto = str(valor).strip()
        return texto if texto else NOT_INFORMED

    def _normalizar_float(self, valor):
        try:
            if pd.isna(valor):
                return None
            texto = str(valor).replace(',', '.').strip()
            return float(texto) if texto else None
        except Exception:
            return None

    def _faixa_distancia(self, distancia_km):
        if distancia_km is None or distancia_km < 0:
            return "SEM_DISTANCIA"
        if distancia_km <= 1: return "ATE_1KM"
        if distancia_km <= 3: return "ATE_3KM"
        if distancia_km <= 7: return "ATE_7KM"
        if distancia_km <= 15: return "ATE_15KM"
        if distancia_km <= 50: return "ATE_50KM"
        return "ACIMA_50KM"

    def _flag_ate(self, distancia_km, limite_km):
        if distancia_km is None or distancia_km < 0:
            return 0
        return 1 if distancia_km <= limite_km else 0

    def intersecao(self, ponto_gps: Point):
        """Verifica se o ponto cruza o polígono."""
        vazio = {'id': NOT_INFORMED, 'flag': 0, 'attrs': {}}
        if self.gdf_gps is None or self.gdf_gps.empty:
            return vazio

        try:
            idxs = self.gdf_gps.sindex.query(ponto_gps, predicate="intersects")
            if len(idxs) == 0:
                return vazio

            linha = self.gdf_gps.iloc[idxs[0]]
            attrs = {}
            for nome_saida, nome_coluna in self.atributos_map.items():
                attrs[nome_saida] = self._normalizar_texto(linha.get(nome_coluna, NOT_INFORMED))

            return {
                'id': self._normalizar_id(linha.get(self.col_id, NOT_INFORMED)),
                'flag': 1,
                'attrs': attrs
            }
        except Exception:
            return vazio

    def proximidade(self, ponto_metrico: Point):
        """Encontra ativo mais próximo usando sistema métrico ou geográfico."""
        resultado = {
            f'{self.prefixo}_id_proximo': NOT_INFORMED,
            f'distancia_{self.prefixo}_km': None,
            f'faixa_distancia_{self.prefixo}': "SEM_DISTANCIA",
            'attrs': {}
        }
        for limite in self.DIST_LIMITES_KM:
            resultado[f'{self.prefixo}_ate_{limite}km'] = 0

        gdf_alvo = self.gdf_metrico if self.projetar_metrico else self.gdf_gps
        if gdf_alvo is None or gdf_alvo.empty:
            return resultado

        try:
            idx_nearest = gdf_alvo.sindex.nearest(ponto_metrico)[1][0]
            linha_alvo = gdf_alvo.iloc[idx_nearest]

            distancia_km = round(ponto_metrico.distance(linha_alvo.geometry) / 1000.0, 3)

            resultado[f'{self.prefixo}_id_proximo'] = self._normalizar_id(linha_alvo.get(self.col_id, NOT_INFORMED))
            resultado[f'distancia_{self.prefixo}_km'] = distancia_km
            resultado[f'faixa_distancia_{self.prefixo}'] = self._faixa_distancia(distancia_km)
            
            for limite in self.DIST_LIMITES_KM:
                resultado[f'{self.prefixo}_ate_{limite}km'] = self._flag_ate(distancia_km, limite)

            attrs = {}
            for nome_saida, nome_coluna in self.atributos_map.items():
                valor = linha_alvo.get(nome_coluna, NOT_INFORMED)
                if nome_saida.endswith("_kv") or nome_saida.endswith("_mw"):
                    attrs[nome_saida] = self._normalizar_float(valor)
                else:
                    attrs[nome_saida] = self._normalizar_texto(valor)

            resultado['attrs'] = attrs
            return resultado
        except Exception:
            return resultado
