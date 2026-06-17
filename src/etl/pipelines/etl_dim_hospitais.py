"""
=========================================================
MÓDULO: etl_dim_hospitais.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
import os
import pandas as pd
import geopandas as gpd

from src.config.constants import DIMENSIONS_DIR, RAW_DIR
from src.etl.utils.base import BaseETL
from src.utils.cleaners import limpar_texto_druid
from src.etl.utils.geo_helpers import geometry_para_path_json

# ==========================================
# 1. Configurações
# ==========================================
RAW_DIR = str(RAW_DIR)
AUX_DIR = os.path.join(RAW_DIR, 'cnes_aux')
DIMENSIONS_DIR = str(DIMENSIONS_DIR)

ARQUIVO_PRINCIPAL = 'tbEstabelecimento202603.csv'
ARQUIVO_MUNICIPIOS = 'tbMunicipio202603.csv'
ARQUIVO_TIPO_UNIDADE = 'tbTipoUnidade202603.csv'
OUTPUT_CSV = os.path.join(DIMENSIONS_DIR, 'dim_hospitais_cnes.csv')

class ETLDimHospitais(BaseETL):
    def __init__(self):
        super().__init__(
            input_path=os.path.join(AUX_DIR, ARQUIVO_PRINCIPAL),
            output_path=OUTPUT_CSV,
            expected_geom_type='Point'
        )

    def _limpar_codigo(self, valor):
        if pd.isna(valor): return "NAO INFORMADO"
        texto = str(valor).strip().replace('"', '').replace('\n', '').replace('\r', '')
        return texto if texto else "NAO INFORMADO"

    def _limpar_coord(self, valor):
        if pd.isna(valor): return None
        try: return float(str(valor).strip().replace(',', '.'))
        except ValueError: return None

    def _coordenada_valida(self, lat, lon):
        if lat is None or lon is None: return False
        if not (-90 <= lat <= 90): return False
        if not (-180 <= lon <= 180): return False
        if lat == 0.0 and lon == 0.0: return False
        return True

    def _classificar_categoria_unidade(self, codigo_tipo, tipo_unidade):
        codigo = self._limpar_codigo(codigo_tipo)
        tipo = limpar_texto_druid(tipo_unidade)
        hospitais = {"05", "07", "15", "20", "21", "61", "62", "73"}
        atencao_basica = {"01", "02", "71", "72"}
        apoio_diagnostico = {"39", "67", "80"}
        regulacao_gestao = {"64", "68", "76", "81", "82", "84"}
        unidade_movel = {"32", "40", "42"}
        vigilancia = {"50", "85", "83"}
        consultorios = {"04", "22", "36", "77", "78", "79"}
        farmacia = {"43"}
        if codigo in hospitais or "HOSPITAL" in tipo or "PRONTO" in tipo: return "HOSPITAL_URGENCIA_EMERGENCIA"
        if codigo in atencao_basica: return "ATENCAO_BASICA"
        if codigo in apoio_diagnostico: return "APOIO_DIAGNOSTICO_LABORATORIAL"
        if codigo in regulacao_gestao: return "REGULACAO_GESTAO"
        if codigo in unidade_movel: return "UNIDADE_MOVEL"
        if codigo in vigilancia: return "VIGILANCIA_IMUNIZACAO"
        if codigo in consultorios: return "CONSULTORIO_ESPECIALIDADE"
        if codigo in farmacia: return "FARMACIA"
        if "SAUDE INDIGENA" in tipo: return "SAUDE_INDIGENA"
        return "OUTROS"

    def _classificar_unidade_critica(self, categoria, funciona_24h):
        if categoria in ["HOSPITAL_URGENCIA_EMERGENCIA", "UNIDADE_MOVEL", "SAUDE_INDIGENA"]: return "SIM"
        if funciona_24h == "S": return "SIM"
        return "NAO"

    def _classificar_capacidade_saude(self, categoria, funciona_24h):
        if categoria == "HOSPITAL_URGENCIA_EMERGENCIA" and funciona_24h == "S": return "ALTA_CAPACIDADE"
        if categoria == "HOSPITAL_URGENCIA_EMERGENCIA": return "MEDIA_CAPACIDADE"
        if categoria == "UNIDADE_MOVEL": return "RESPOSTA_MOVEL"
        if categoria == "SAUDE_INDIGENA": return "SAUDE_INDIGENA"
        if categoria == "ATENCAO_BASICA": return "ATENCAO_LOCAL"
        return "SUPORTE"

    def _classificar_atendimento(self, categoria, funciona_24h):
        if funciona_24h == "S" and categoria == "HOSPITAL_URGENCIA_EMERGENCIA": return "CRITICO_24H"
        if categoria == "HOSPITAL_URGENCIA_EMERGENCIA": return "CRITICO"
        if categoria == "UNIDADE_MOVEL": return "MOBILIDADE_ASSISTENCIAL"
        if categoria == "SAUDE_INDIGENA": return "SAUDE_INDIGENA"
        if categoria == "ATENCAO_BASICA": return "ATENCAO_LOCAL"
        return "SUPORTE"

    def extract(self) -> gpd.GeoDataFrame:
        """
        Lê os CSVs brutos do CNES e converte em um GeoDataFrame para se encaixar 
        perfeitamente na arquitetura espacial do BaseETL.
        """
        try:
            df_estab = pd.read_csv(self.input_path, sep=';', dtype=str, encoding='latin-1')
            df_muni = pd.read_csv(os.path.join(AUX_DIR, ARQUIVO_MUNICIPIOS), sep=';', dtype=str, encoding='latin-1')
            df_tipo = pd.read_csv(os.path.join(AUX_DIR, ARQUIVO_TIPO_UNIDADE), sep=';', dtype=str, encoding='latin-1')
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Erro ao ler arquivos do CNES: {e}")

        colunas_estab = ['CO_CNES', 'NO_FANTASIA', 'CO_MUNICIPIO_GESTOR', 'TP_UNIDADE', 'TP_ESTAB_SEMPRE_ABERTO', 'NU_LATITUDE', 'NU_LONGITUDE']
        df = df_estab[[c for c in colunas_estab if c in df_estab.columns]].copy()

        df['CO_CNES'] = df['CO_CNES'].apply(self._limpar_codigo)
        df['CO_MUNICIPIO_GESTOR'] = df['CO_MUNICIPIO_GESTOR'].apply(self._limpar_codigo)
        df['TP_UNIDADE'] = df['TP_UNIDADE'].apply(self._limpar_codigo)
        df['latitude'] = df['NU_LATITUDE'].apply(self._limpar_coord)
        df['longitude'] = df['NU_LONGITUDE'].apply(self._limpar_coord)
        
        df['coordenada_valida'] = df.apply(lambda r: self._coordenada_valida(r['latitude'], r['longitude']), axis=1)
        df = df[df['coordenada_valida']].copy()

        df_muni['CO_MUNICIPIO'] = df_muni['CO_MUNICIPIO'].apply(self._limpar_codigo)
        df_tipo['CO_TIPO_UNIDADE'] = df_tipo['CO_TIPO_UNIDADE'].apply(self._limpar_codigo)

        df = pd.merge(df, df_muni[['CO_MUNICIPIO', 'NO_MUNICIPIO', 'CO_SIGLA_ESTADO']], left_on='CO_MUNICIPIO_GESTOR', right_on='CO_MUNICIPIO', how='left')
        df = pd.merge(df, df_tipo[['CO_TIPO_UNIDADE', 'DS_TIPO_UNIDADE']], left_on='TP_UNIDADE', right_on='CO_TIPO_UNIDADE', how='left')

        # Converte para GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
        )
        return gdf

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        gdf['nome_hospital'] = gdf['NO_FANTASIA'].fillna('NAO INFORMADO').apply(limpar_texto_druid)
        gdf['tipo_unidade'] = gdf['DS_TIPO_UNIDADE'].fillna('TIPO NAO INFORMADO').apply(limpar_texto_druid)
        gdf['municipios_nome'] = gdf['NO_MUNICIPIO'].fillna('DESCONHECIDO').apply(limpar_texto_druid)
        gdf['estado_sigla'] = gdf['CO_SIGLA_ESTADO'].fillna('NI').apply(limpar_texto_druid)
        gdf['funciona_24h'] = gdf['TP_ESTAB_SEMPRE_ABERTO'].fillna('N').apply(lambda x: "SIM" if limpar_texto_druid(x) == "S" else "NAO")

        gdf['categoria_unidade'] = gdf.apply(lambda r: self._classificar_categoria_unidade(r['TP_UNIDADE'], r['DS_TIPO_UNIDADE']), axis=1)
        gdf['classe_capacidade_saude'] = gdf.apply(lambda r: self._classificar_capacidade_saude(r['categoria_unidade'], r['funciona_24h']), axis=1)
        gdf['tipo_unidade_critica'] = gdf.apply(lambda r: self._classificar_unidade_critica(r['categoria_unidade'], r['funciona_24h']), axis=1)
        gdf['categoria_atendimento'] = gdf.apply(lambda r: self._classificar_atendimento(r['categoria_unidade'], r['funciona_24h']), axis=1)

        gdf['path_json'] = gdf.geometry.apply(geometry_para_path_json)
        gdf['codigo_ibge'] = gdf['CO_MUNICIPIO_GESTOR']
        gdf['codigo_cnes'] = gdf['CO_CNES']

        ordem_final = [
            'codigo_cnes', 'nome_hospital', 'tipo_unidade', 'categoria_unidade',
            'tipo_unidade_critica', 'categoria_atendimento', 'classe_capacidade_saude',
            'funciona_24h', 'codigo_ibge', 'municipios_nome', 'estado_sigla',
            'latitude', 'longitude', 'path_json'
        ]
        
        df_final = pd.DataFrame(gdf[ordem_final]).copy()
        return df_final.drop_duplicates(subset=['codigo_cnes'])

def executar():
    etl = ETLDimHospitais()
    etl.execute()
