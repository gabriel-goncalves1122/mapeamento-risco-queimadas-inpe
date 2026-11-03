"""
Modelo de Centralidade de Rede do Sistema Interligado Nacional (`SINNetworkCentralityModel`).

Constrói o grafo topológico da malha elétrica (Subestações como vértices e Linhas
de Transmissão como arestas via `cKDTree`), calcula o `betweenness_centrality` no
NetworkX e classifica o Risco de Queda em Cascata para enriquecer `dim_ons_subestacoes.csv`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_ROOT = str(Path(__file__).resolve().parents[4])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import networkx as nx
import pandas as pd
from scipy.spatial import cKDTree

from src.core.config.constants import DIMENSIONS_DIR
from src.core.contracts.contracts import ExecutablePipelineStep
from src.silver.utils.geo_helpers import PathJsonCodec


def path_json_para_linhas(valor: Any) -> Any:
    """Reconstrução de LineString/MultiLineString delegada ao `PathJsonCodec`."""
    return PathJsonCodec.path_json_para_geometry(valor, tipo_geometria="line")


class SINNetworkCentralityModel(ExecutablePipelineStep):
    """
    Analisador orientado a objetos de vulnerabilidade sistêmica da rede elétrica ONS.

    Permite injeção dos caminhos das dimensões de subestações e linhas para execução
    isolada em testes de laboratório ou reprocessamentos históricos.
    """

    def __init__(
        self,
        subestacoes_csv: str | Path | None = None,
        linhas_csv: str | Path | None = None,
        subestacoes_path: str | Path | None = None,
        linhas_path: str | Path | None = None,
    ) -> None:
        caminho_sub = subestacoes_path or subestacoes_csv
        caminho_lin = linhas_path or linhas_csv
        self.subestacoes_csv = Path(
            caminho_sub or (DIMENSIONS_DIR / "dim_ons_subestacoes.csv")
        )
        self.linhas_csv = Path(
            caminho_lin or (DIMENSIONS_DIR / "dim_ons_linhas_transmissao.csv")
        )

    def _carregar_tabelas(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        if not self.subestacoes_csv.exists() or not self.linhas_csv.exists():
            raise FileNotFoundError(
                f"Dimensões ONS não encontradas em '{self.subestacoes_csv}' ou '{self.linhas_csv}'"
            )
        df_sub = pd.read_csv(self.subestacoes_csv, dtype=str)
        df_lin = pd.read_csv(self.linhas_csv, dtype=str)
        return df_sub, df_lin

    def construir_grafo(
        self,
        df_sub: pd.DataFrame,
        df_lin: pd.DataFrame,
    ) -> tuple[nx.Graph, pd.DataFrame, pd.DataFrame]:
        """Associa vértices a arestas usando `cKDTree` e monta o grafo NetworkX."""
        sub_coords = df_sub[["latitude", "longitude"]].astype(float).values
        # Aceita id_subestacao ou cod_subestacao
        col_id_sub = "cod_subestacao" if "cod_subestacao" in df_sub.columns else "id_subestacao"
        sub_ids = df_sub[col_id_sub].tolist()
        tree = cKDTree(sub_coords)

        G = nx.Graph()
        for _, row in df_sub.iterrows():
            G.add_node(
                row[col_id_sub],
                nome=row.get("nome_subestacao", ""),
                tensao=row.get("tensao_kv", 0),
            )

        arestas_conectadas = 0
        df_lin_copia = df_lin.copy()
        extensoes: list[float] = []

        for idx, row in df_lin.iterrows():
            geom = path_json_para_linhas(row.get("path_json"))
            if geom and not geom.is_empty:
                extensoes.append(float(row.get("extensao_km", 1.0) or 1.0))
                coords = list(geom.coords) if geom.geom_type == "LineString" else list(geom.geoms[0].coords)
                p_ini = (coords[0][1], coords[0][0])
                p_fim = (coords[-1][1], coords[-1][0])

                _, idx_ini = tree.query(p_ini)
                _, idx_fim = tree.query(p_fim)

                u = sub_ids[idx_ini]
                v = sub_ids[idx_fim]

                if u != v:
                    peso = float(row.get("extensao_km", 1.0) or 1.0)
                    col_linha_id = "cod_linha" if "cod_linha" in row else "id_linha_transmissao"
                    G.add_edge(u, v, weight=peso, cod_linha=row.get(col_linha_id))
                    arestas_conectadas += 1
            else:
                extensoes.append(0.0)

        df_lin_copia["extensao_km"] = extensoes
        return G, df_sub, df_lin_copia

    def calcular_centralidade(
        self,
        G: nx.Graph,
        df_sub: pd.DataFrame,
    ) -> pd.DataFrame:
        """Calcula betweenness e classifica o risco de cascata em 4 faixas."""
        print(f"Calculando Betweenness Centrality para {G.number_of_nodes()} nós e {G.number_of_edges()} arestas...")
        betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)

        col_id_sub = "cod_subestacao" if "cod_subestacao" in df_sub.columns else "id_subestacao"
        df_res = df_sub.copy()
        df_res["betweenness_centrality"] = df_res[col_id_sub].map(betweenness).fillna(0.0)
        df_res["betweenness_score"] = df_res["betweenness_centrality"]
        df_res["grau_conectividade"] = df_res[col_id_sub].map(dict(G.degree())).fillna(0)

        # Normaliza o score para escala 0 a 100
        max_score = df_res["betweenness_centrality"].max()
        if max_score > 0:
            df_res["betweenness_score_norm"] = (df_res["betweenness_centrality"] / max_score) * 100.0
        else:
            df_res["betweenness_score_norm"] = 0.0

        # Regra de classificação de risco sistêmico de queda em cascata
        def classificar_risco(score: float) -> str:
            if score >= 80:
                return "EXTREMO"
            if score >= 50:
                return "ALTO"
            if score >= 20:
                return "MEDIO"
            if score > 0:
                return "BAIXO"
            return "ISOLADO"

        df_res["risco_cascata"] = df_res["betweenness_score_norm"].apply(classificar_risco)
        return df_res

    def salvar_resultados(self, df_sub_enriquecido: pd.DataFrame) -> Path:
        """Sobrescreve `dim_ons_subestacoes.csv` com as métricas de grafos calculadas."""
        df_sub_enriquecido.to_csv(self.subestacoes_csv, index=False)
        print(f"Métricas topológicas salvas com sucesso em '{self.subestacoes_csv}'.")
        return self.subestacoes_csv

    def _run(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        print("\n--- [CIÊNCIA DE REDES] Iniciando Modelagem Topológica do SIN ---")
        df_sub, df_lin = self._carregar_tabelas()
        G, df_sub, _ = self.construir_grafo(df_sub, df_lin)
        df_resultado = self.calcular_centralidade(G, df_sub)
        self.salvar_resultados(df_resultado)
        return df_resultado


def construir_grafo_sin() -> pd.DataFrame:
    """Wrapper funcional para execução direta."""
    return SINNetworkCentralityModel().execute()


if __name__ == "__main__":
    construir_grafo_sin()
