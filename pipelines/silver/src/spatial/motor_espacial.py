"""
=========================================================
MÓDULO: motor_espacial.py
---------------------------------------------------------
Função Geral: Motor de processamento espacial vetorial usando R-Tree/KDTree para cálculo de distâncias.
=========================================================
"""
import pandas as pd
import geopandas as gpd
import logging

from shapely.geometry import Point

from config import settings
from config.constants import DISTANCE_LIMITS_KM, EPSG_GPS, EPSG_METRICO, NOT_INFORMED
from pipelines.silver.src.spatial.layers import SpatialLayer

logger = logging.getLogger(__name__)


class MotorEspacial:
    """
    Motor espacial do pipeline refatorado.

    Utiliza o padrão SpatialLayer para isolar a responsabilidade de
    carregamento, limpeza e consultas geográficas (intersects e nearest).
    """
    
    DIST_LIMITES_KM = list(DISTANCE_LIMITS_KM)

    def __init__(self):
        logger.info("Inicializando Motor Espacial remodelado e baseado em Layers.")

        self.camada_funai = SpatialLayer(
            path=settings.DIM_FUNAI,
            nome="FUNAI",
            col_id="codigo_ti",
            prefixo="terra_indigena",
            atributos_map={
                'terra_indigena_nome': 'nome_terra_indigena',
                'terra_indigena_prioridade': 'prioridade_funai',
                'terra_indigena_classe_area': 'classe_area_ti',
            },
            projetar_metrico=True,
            tipo_geometria="polygon",
        )

        self.camada_municipios = SpatialLayer(
            path=settings.DIM_MUNICIPIOS_COORD,
            nome="Municípios GPS",
            col_id="codigo_ibge",
            prefixo="municipio_espacial",
            atributos_map={
                'municipio_espacial_nome': 'municipios_nome',
                'municipio_espacial_estado': 'estado_sigla',
                'municipio_espacial_regiao': 'regiao_brasil',
            },
            projetar_metrico=False,
            tipo_geometria="polygon",
        )

        self.camada_rodovias = SpatialLayer(
            path=settings.DIM_RODOVIAS,
            nome="Rodovias Federais",
            col_id="id_trecho_rodoviario",
            prefixo="rodovia",
            atributos_map={
                'rodovia_codigo': 'codigo_rodovia',
                'rodovia_criticidade': 'criticidade_rodovia',
                'rodovia_classe_revestimento': 'classe_revestimento',
            },
            projetar_metrico=True,
            tipo_geometria="line",
        )

        self.camada_linhas = SpatialLayer(
            path=settings.DIM_LINHAS_ONS,
            nome="Linhas ONS",
            col_id="id_linha_transmissao",
            prefixo="linha",
            atributos_map={
                'linha_nome': 'nome_linha',
                'linha_tensao_kv': 'tensao_kv',
                'linha_classe_tensao': 'classe_tensao',
                'linha_criticidade': 'classe_criticidade_linha',
            },
            projetar_metrico=True,
            tipo_geometria="line",
        )

        self.camada_subestacoes = SpatialLayer(
            path=settings.DIM_SUBESTACOES,
            nome="Subestações ONS",
            col_id="id_subestacao",
            prefixo="subestacao",
            atributos_map={
                'subestacao_nome': 'nome_subestacao',
                'subestacao_capacidade_mw': 'capacidade_mw',
                'subestacao_criticidade': 'criticidade_subestacao',
            },
            projetar_metrico=True,
            tipo_geometria="point",
        )

        self.camada_sistemas = SpatialLayer(
            path=settings.DIM_SISTEMAS_ISO,
            nome="Sistemas Isolados",
            col_id="id_sistema_isolado",
            prefixo="sistema_isolado",
            atributos_map={
                'sistema_isolado_nome': 'nome_sistema_isolado',
                'sistema_isolado_prioridade': 'prioridade_sistema_isolado',
            },
            projetar_metrico=True,
            tipo_geometria="point",
        )

        self.camada_hospitais = SpatialLayer(
            path=settings.DIM_HOSPITAIS,
            nome="Hospitais CNES",
            col_id="codigo_cnes",
            prefixo="hospital",
            atributos_map={
                'hospital_nome': 'nome_hospital',
                'hospital_categoria': 'categoria_unidade',
                'hospital_critico': 'tipo_unidade_critica',
                'hospital_funciona_24h': 'funciona_24h',
                'hospital_capacidade_classe': 'categoria_atendimento',
            },
            projetar_metrico=True,
            tipo_geometria="point",
        )

        self.camadas_proximidade = [
            self.camada_rodovias, self.camada_linhas, self.camada_subestacoes,
            self.camada_sistemas, self.camada_hospitais
        ]

    def _resultado_base(self):
        """Estrutura padrão retornada quando a coordenada é inválida."""
        res = {
            'codigo_ti': NOT_INFORMED,
            'foco_em_terra_indigena': 0,
            'codigo_ti_proxima': NOT_INFORMED,
            'codigo_ibge_espacial': NOT_INFORMED,
            'foco_em_municipio_mapeado': 0,
            'id_trecho_rodoviario': NOT_INFORMED,
            'id_linha_transmissao': NOT_INFORMED,
            'id_subestacao': NOT_INFORMED,
            'id_sistema_isolado': NOT_INFORMED,
            'codigo_cnes_prox': NOT_INFORMED,

            'distancia_rodovia_km': None,
            'distancia_linha_km': None,
            'distancia_subestacao_km': None,
            'distancia_sistema_isolado_km': None,
            'distancia_hospital_km': None,
            'distancia_terra_indigena_km': None,

            'faixa_distancia_rodovia': "SEM_DISTANCIA",
            'faixa_distancia_linha': "SEM_DISTANCIA",
            'faixa_distancia_subestacao': "SEM_DISTANCIA",
            'faixa_distancia_sistema_isolado': "SEM_DISTANCIA",
            'faixa_distancia_hospital': "SEM_DISTANCIA",
            'faixa_distancia_terra_indigena': "SEM_DISTANCIA",

            'rodovia_codigo': NOT_INFORMED,
            'rodovia_criticidade': NOT_INFORMED,
            'rodovia_classe_revestimento': NOT_INFORMED,

            'linha_nome': NOT_INFORMED,
            'linha_tensao_kv': None,
            'linha_classe_tensao': NOT_INFORMED,
            'linha_criticidade': NOT_INFORMED,

            'subestacao_nome': NOT_INFORMED,
            'subestacao_capacidade_mw': None,
            'subestacao_criticidade': NOT_INFORMED,

            'sistema_isolado_nome': NOT_INFORMED,
            'sistema_isolado_prioridade': NOT_INFORMED,

            'hospital_nome': NOT_INFORMED,
            'hospital_categoria': NOT_INFORMED,
            'hospital_critico': NOT_INFORMED,
            'hospital_funciona_24h': NOT_INFORMED,
            'hospital_capacidade_classe': NOT_INFORMED,

            'terra_indigena_nome': NOT_INFORMED,
            'terra_indigena_prioridade': NOT_INFORMED,
            'terra_indigena_classe_area': NOT_INFORMED,

            'municipio_espacial_nome': NOT_INFORMED,
            'municipio_espacial_estado': NOT_INFORMED,
            'municipio_espacial_regiao': NOT_INFORMED,
        }

        prefixos = ['rodovia', 'linha', 'subestacao', 'sistema_isolado', 'hospital', 'terra_indigena']
        for prefixo in prefixos:
            for limite in self.DIST_LIMITES_KM:
                res[f'{prefixo}_ate_{limite}km'] = 0

        return res

    def _coordenada_valida(self, lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            if not (-90 <= lat <= 90): return False
            if not (-180 <= lon <= 180): return False
            if lat == 0.0 and lon == 0.0: return False
            return True
        except Exception:
            return False

    def analisar_todas_ameacas(self, latitude, longitude):
        """
        Processa o cruzamento de um ponto de foco de incêndio contra todas as camadas espaciais.
        
        Como funciona:
        1. Cria um objeto Point(lon, lat) EPSG:4326 a partir do payload bruto.
        2. Para polígonos (Terras Indígenas, Municípios), usa operação de 'Interseção' (intersects).
           Descobre se o ponto está 'dentro' da área.
        3. Para linhas/pontos (Infraestrutura ONS, Rodovias, Hospitais), projeta o ponto
           para uma grade plana Métrica (ex: EPSG:5880) e roda operação 'Nearest' (cKDTree/R-Tree)
           para descobrir a distância real em Kilômetros até o ativo mais próximo.
        4. Avalia riscos críticos com base em limites predefinidos (ex: fogo a menos de 1km de subestação).
        """
        res = self._resultado_base()

        if not self._coordenada_valida(latitude, longitude):
            return res

        lat = float(latitude)
        lon = float(longitude)

        ponto_gps = Point(lon, lat)
        ponto_metrico = (
            gpd.GeoSeries([ponto_gps], crs=f"EPSG:{EPSG_GPS}")
            .to_crs(epsg=EPSG_METRICO)
            .iloc[0]
        )

        # 1. Município espacial
        mun = self.camada_municipios.intersecao(ponto_gps)
        res['codigo_ibge_espacial'] = mun['id']
        res['foco_em_municipio_mapeado'] = mun['flag']
        res.update(mun['attrs'])

        # 2. Terra Indígena (Interseção e Proximidade)
        ti_inter = self.camada_funai.intersecao(ponto_gps)
        res['codigo_ti'] = ti_inter['id']
        res['foco_em_terra_indigena'] = ti_inter['flag']
        if ti_inter['flag'] == 1:
            res.update(ti_inter['attrs'])

        ti_prox = self.camada_funai.proximidade(ponto_metrico)
        res['codigo_ti_proxima'] = ti_prox['terra_indigena_id_proximo']
        res['distancia_terra_indigena_km'] = ti_prox['distancia_terra_indigena_km']
        res['faixa_distancia_terra_indigena'] = ti_prox['faixa_distancia_terra_indigena']
        for limite in self.DIST_LIMITES_KM:
            res[f'terra_indigena_ate_{limite}km'] = ti_prox[f'terra_indigena_ate_{limite}km']
        
        # Se não interseciona, os atributos da TI mais próxima são exibidos
        if ti_inter['flag'] == 0:
            res.update(ti_prox['attrs'])

        # 3. Infraestruturas e Ativos (Apenas Proximidade)
        for camada in self.camadas_proximidade:
            prox = camada.proximidade(ponto_metrico)
            
            # Map IDs specifically to output keys
            if camada.prefixo == 'rodovia':
                res['id_trecho_rodoviario'] = prox['rodovia_id_proximo']
            elif camada.prefixo == 'linha':
                res['id_linha_transmissao'] = prox['linha_id_proximo']
            elif camada.prefixo == 'subestacao':
                res['id_subestacao'] = prox['subestacao_id_proximo']
            elif camada.prefixo == 'sistema_isolado':
                res['id_sistema_isolado'] = prox['sistema_isolado_id_proximo']
            elif camada.prefixo == 'hospital':
                res['codigo_cnes_prox'] = prox['hospital_id_proximo']

            res[f'distancia_{camada.prefixo}_km'] = prox[f'distancia_{camada.prefixo}_km']
            res[f'faixa_distancia_{camada.prefixo}'] = prox[f'faixa_distancia_{camada.prefixo}']
            res.update(prox['attrs'])
            
            for limite in self.DIST_LIMITES_KM:
                res[f'{camada.prefixo}_ate_{limite}km'] = prox[f'{camada.prefixo}_ate_{limite}km']

        return res
