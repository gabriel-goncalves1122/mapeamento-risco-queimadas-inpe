"""
Catálogo e fábrica declarativa das 7 camadas espaciais Silver (`SpatialLayerCatalog`).

Retira do `MotorEspacial` a responsabilidade de conhecer os nomes de arquivos,
colunas internas de cada CSV dimensional e o template de resultado vazio (SRP / OCP).
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from src.core.config import settings
from src.core.config.constants import DISTANCE_LIMITS_KM, NOT_INFORMED
from src.core.config.settings import PipelineSettings
from src.silver.spatial.layers import SpatialLayer
from src.silver.spatial.spatial_layer_spec import SpatialLayerSpec


class SpatialLayerCatalog:
    """
    Registry e Factory das dimensões espaciais utilizadas pelo `MotorEspacial`.

    Centraliza os `SpatialLayerSpec`s das 7 dimensões Silver (FUNAI, Municípios,
    Rodovias, Linhas ONS, Subestações, Sistemas Isolados e Hospitais CNES) e
    constrói o dicionário base de resposta para coordenadas inválidas.
    """

    PROXIMITY_LAYER_KEYS: tuple[str, ...] = (
        "camada_rodovias",
        "camada_linhas",
        "camada_subestacoes",
        "camada_sistemas",
        "camada_hospitais",
    )

    OUTPUT_ID_KEYS: dict[str, str] = {
        "rodovia": "id_trecho_rodoviario",
        "linha": "id_linha_transmissao",
        "subestacao": "id_subestacao",
        "sistema_isolado": "id_sistema_isolado",
        "hospital": "codigo_cnes_prox",
    }

    DISTANCE_PREFIXES: tuple[str, ...] = (
        "rodovia",
        "linha",
        "subestacao",
        "sistema_isolado",
        "hospital",
        "terra_indigena",
    )

    @classmethod
    def default_specs(cls, settings_obj: PipelineSettings | Any | None = None) -> dict[str, SpatialLayerSpec]:
        """Retorna as especificações declarativas das 7 camadas espaciais Silver."""
        cfg = settings_obj or settings
        return {
            "camada_funai": SpatialLayerSpec(
                path=getattr(cfg, "dim_funai", getattr(cfg, "DIM_FUNAI", settings.DIM_FUNAI)),
                nome="FUNAI",
                col_id="codigo_ti",
                prefixo="terra_indigena",
                atributos_map={
                    "terra_indigena_nome": "nome_terra_indigena",
                    "terra_indigena_prioridade": "prioridade_funai",
                    "terra_indigena_classe_area": "classe_area_ti",
                },
                projetar_metrico=True,
                tipo_geometria="polygon",
                output_id_key="codigo_ti_proxima",
            ),
            "camada_municipios": SpatialLayerSpec(
                path=getattr(
                    cfg,
                    "dim_municipios_coord",
                    getattr(cfg, "DIM_MUNICIPIOS_COORD", settings.DIM_MUNICIPIOS_COORD),
                ),
                nome="Municípios GPS",
                col_id="codigo_ibge",
                prefixo="municipio_espacial",
                atributos_map={
                    "municipio_espacial_nome": "municipios_nome",
                    "municipio_espacial_estado": "estado_sigla",
                    "municipio_espacial_regiao": "regiao_brasil",
                },
                projetar_metrico=False,
                tipo_geometria="polygon",
                output_id_key="codigo_ibge_espacial",
            ),
            "camada_rodovias": SpatialLayerSpec(
                path=getattr(cfg, "dim_rodovias", getattr(cfg, "DIM_RODOVIAS", settings.DIM_RODOVIAS)),
                nome="Rodovias Federais",
                col_id="id_trecho_rodoviario",
                prefixo="rodovia",
                atributos_map={
                    "rodovia_codigo": "codigo_rodovia",
                    "rodovia_criticidade": "criticidade_rodovia",
                    "rodovia_classe_revestimento": "classe_revestimento",
                },
                projetar_metrico=True,
                tipo_geometria="line",
                output_id_key="id_trecho_rodoviario",
            ),
            "camada_linhas": SpatialLayerSpec(
                path=getattr(cfg, "dim_linhas_ons", getattr(cfg, "DIM_LINHAS_ONS", settings.DIM_LINHAS_ONS)),
                nome="Linhas ONS",
                col_id="id_linha_transmissao",
                prefixo="linha",
                atributos_map={
                    "linha_nome": "nome_linha",
                    "linha_tensao_kv": "tensao_kv",
                    "linha_classe_tensao": "classe_tensao",
                    "linha_criticidade": "classe_criticidade_linha",
                },
                projetar_metrico=True,
                tipo_geometria="line",
                output_id_key="id_linha_transmissao",
            ),
            "camada_subestacoes": SpatialLayerSpec(
                path=getattr(cfg, "dim_subestacoes", getattr(cfg, "DIM_SUBESTACOES", settings.DIM_SUBESTACOES)),
                nome="Subestações ONS",
                col_id="id_subestacao",
                prefixo="subestacao",
                atributos_map={
                    "subestacao_nome": "nome_subestacao",
                    "subestacao_capacidade_mw": "capacidade_mw",
                    "subestacao_criticidade": "criticidade_subestacao",
                },
                projetar_metrico=True,
                tipo_geometria="point",
                output_id_key="id_subestacao",
            ),
            "camada_sistemas": SpatialLayerSpec(
                path=getattr(cfg, "dim_sistemas_iso", getattr(cfg, "DIM_SISTEMAS_ISO", settings.DIM_SISTEMAS_ISO)),
                nome="Sistemas Isolados",
                col_id="id_sistema_isolado",
                prefixo="sistema_isolado",
                atributos_map={
                    "sistema_isolado_nome": "nome_sistema_isolado",
                    "sistema_isolado_prioridade": "prioridade_sistema_isolado",
                },
                projetar_metrico=True,
                tipo_geometria="point",
                output_id_key="id_sistema_isolado",
            ),
            "camada_hospitais": SpatialLayerSpec(
                path=getattr(cfg, "dim_hospitais", getattr(cfg, "DIM_HOSPITAIS", settings.DIM_HOSPITAIS)),
                nome="Hospitais CNES",
                col_id="codigo_cnes",
                prefixo="hospital",
                atributos_map={
                    "hospital_nome": "nome_hospital",
                    "hospital_categoria": "categoria_unidade",
                    "hospital_critico": "tipo_unidade_critica",
                    "hospital_funciona_24h": "funciona_24h",
                    "hospital_capacidade_classe": "categoria_atendimento",
                },
                projetar_metrico=True,
                tipo_geometria="point",
                output_id_key="codigo_cnes_prox",
            ),
        }

    @classmethod
    def build_layers(
        cls,
        settings_obj: PipelineSettings | Any | None = None,
        layer_cls: Callable[..., SpatialLayer] = SpatialLayer,
    ) -> dict[str, SpatialLayer]:
        """
        Instancia todas as camadas do catálogo usando `layer_cls`.

        Receber `layer_cls` explícito permite que mocks em testes unitários interceptem
        a criação das camadas sem ler arquivos CSV pesados do disco.
        """
        specs = cls.default_specs(settings_obj)
        return {
            key: layer_cls(
                path=spec.path,
                nome=spec.nome,
                col_id=spec.col_id,
                prefixo=spec.prefixo,
                atributos_map=dict(spec.atributos_map),
                projetar_metrico=spec.projetar_metrico,
                tipo_geometria=spec.tipo_geometria,
            )
            for key, spec in specs.items()
        }

    @classmethod
    def criar_resultado_vazio(
        cls,
        limites_km: Sequence[int] = DISTANCE_LIMITS_KM,
    ) -> dict[str, Any]:
        """Gera o dicionário padrão retornado quando a coordenada do foco é inválida."""
        res: dict[str, Any] = {
            "codigo_ti": NOT_INFORMED,
            "foco_em_terra_indigena": 0,
            "codigo_ti_proxima": NOT_INFORMED,
            "codigo_ibge_espacial": NOT_INFORMED,
            "foco_em_municipio_mapeado": 0,
            "id_trecho_rodoviario": NOT_INFORMED,
            "id_linha_transmissao": NOT_INFORMED,
            "id_subestacao": NOT_INFORMED,
            "id_sistema_isolado": NOT_INFORMED,
            "codigo_cnes_prox": NOT_INFORMED,
            "distancia_rodovia_km": None,
            "distancia_linha_km": None,
            "distancia_subestacao_km": None,
            "distancia_sistema_isolado_km": None,
            "distancia_hospital_km": None,
            "distancia_terra_indigena_km": None,
            "faixa_distancia_rodovia": "SEM_DISTANCIA",
            "faixa_distancia_linha": "SEM_DISTANCIA",
            "faixa_distancia_subestacao": "SEM_DISTANCIA",
            "faixa_distancia_sistema_isolado": "SEM_DISTANCIA",
            "faixa_distancia_hospital": "SEM_DISTANCIA",
            "faixa_distancia_terra_indigena": "SEM_DISTANCIA",
            "rodovia_codigo": NOT_INFORMED,
            "rodovia_criticidade": NOT_INFORMED,
            "rodovia_classe_revestimento": NOT_INFORMED,
            "linha_nome": NOT_INFORMED,
            "linha_tensao_kv": None,
            "linha_classe_tensao": NOT_INFORMED,
            "linha_criticidade": NOT_INFORMED,
            "subestacao_nome": NOT_INFORMED,
            "subestacao_capacidade_mw": None,
            "subestacao_criticidade": NOT_INFORMED,
            "sistema_isolado_nome": NOT_INFORMED,
            "sistema_isolado_prioridade": NOT_INFORMED,
            "hospital_nome": NOT_INFORMED,
            "hospital_categoria": NOT_INFORMED,
            "hospital_critico": NOT_INFORMED,
            "hospital_funciona_24h": NOT_INFORMED,
            "hospital_capacidade_classe": NOT_INFORMED,
            "terra_indigena_nome": NOT_INFORMED,
            "terra_indigena_prioridade": NOT_INFORMED,
            "terra_indigena_classe_area": NOT_INFORMED,
            "municipio_espacial_nome": NOT_INFORMED,
            "municipio_espacial_estado": NOT_INFORMED,
            "municipio_espacial_regiao": NOT_INFORMED,
        }

        for prefixo in cls.DISTANCE_PREFIXES:
            for limite in limites_km:
                res[f"{prefixo}_ate_{limite}km"] = 0

        return res
