"""
Extrator geoespacial da Camada Bronze para malhas elétricas da ANEEL/ONS.

Encapsula a paginação na API ArcGIS REST do SIGEL/ANEEL e a persistência de
GeoJSONs brutos em EPSG:4326, permitindo injeção de sessão HTTP e diretório
de destino para testes isolados (SRP / DIP).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping

_ROOT = str(Path(__file__).resolve().parents[3])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import requests

from src.core.config.constants import ANEEL_DIR
from src.core.contracts import ExecutablePipelineStep

# Endpoint ArcGIS REST da ANEEL com placeholder {id} para alternar camadas
URL_BASE = "https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmiss%C3%A3o/MapServer/{id}/query"

# Mapeamento oficial entre o prefixo do arquivo GeoJSON e o Layer ID no MapServer
CAMADAS: dict[str, int] = {
    "linhas_transmissao": 1,
    "subestacoes": 3,
    "sistemas_isolados": 5,
}


class AneelArcGisExtractor(ExecutablePipelineStep):
    """
    Serviço de ingestão paginada de feições geográficas da ANEEL/ONS.

    Respeita o limite de paginação do ArcGIS Server (`resultRecordCount=1000`)
    e aplica pausa configurável entre requisições para evitar throttling.
    """

    def __init__(
        self,
        output_dir: str | Path = ANEEL_DIR,
        camadas: Mapping[str, int] | None = None,
        url_base: str = URL_BASE,
        page_size: int = 1000,
        rate_limit_s: float = 1.0,
        http_client: Any | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.camadas = dict(camadas) if camadas is not None else dict(CAMADAS)
        self.url_base = url_base
        self.page_size = page_size
        self.rate_limit_s = rate_limit_s
        self._http_client = http_client or requests

    def extrair_camada(self, nome_arquivo: str, layer_id: int) -> Path | None:
        """Baixa todas as páginas de uma camada ArcGIS e salva um FeatureCollection GeoJSON."""
        print(f"\n[ANEEL] Iniciando extração da camada: {nome_arquivo.upper()} (Layer {layer_id})")

        url = self.url_base.format(id=layer_id)
        todas_as_features: list[dict[str, Any]] = []
        offset = 0

        while True:
            print(f"   Baixando registros de {offset} a {offset + self.page_size}...")
            # outSR=4326 força o servidor ArcGIS a reprojetar para WGS84 na origem
            params = {
                "where": "1=1",
                "outFields": "*",
                "f": "geojson",
                "resultOffset": offset,
                "resultRecordCount": self.page_size,
                "outSR": "4326",
            }

            response = self._http_client.get(url, params=params)
            if response.status_code != 200:
                print(f"   [ERRO] Falha na conexão: {response.status_code}")
                break

            dados = response.json()
            features = dados.get("features", [])
            if not features:
                break

            todas_as_features.extend(features)
            offset += self.page_size
            if self.rate_limit_s > 0:
                time.sleep(self.rate_limit_s)

            if len(features) < self.page_size:
                break

        if not todas_as_features:
            print("   [AVISO] Nenhum dado encontrado para esta camada.")
            return None

        geojson_final = {
            "type": "FeatureCollection",
            "features": todas_as_features,
        }
        self.output_dir.mkdir(parents=True, exist_ok=True)
        caminho = self.output_dir / f"{nome_arquivo}_ons.geojson"
        with open(caminho, "w", encoding="utf-8") as fp:
            json.dump(geojson_final, fp, ensure_ascii=False)

        print(f"   [SUCESSO] {len(todas_as_features)} registros salvos em '{caminho}'.")
        return caminho

    def baixar_toda_infraestrutura() -> dict[str, Path]:
        pass

    def baixar_toda_infraestrutura(self) -> dict[str, Path]:
        """Executa a extração sequencial de todas as camadas elétricas configuradas."""
        print("Iniciando Pipeline de Ingestão Geoespacial da ANEEL/ONS...")
        arquivos_gerados: dict[str, Path] = {}
        for nome, layer_id in self.camadas.items():
            caminho = self.extrair_camada(nome, layer_id)
            if caminho is not None:
                arquivos_gerados[nome] = caminho
        print("\nExtração de infraestrutura elétrica concluída 100%!")
        return arquivos_gerados

    def _run(self, *args: Any, **kwargs: Any) -> dict[str, Path]:
        return self.baixar_toda_infraestrutura()


def extrair_camada(nome_arquivo: str, layer_id: int) -> Path | None:
    """Wrapper funcional para compatibilidade com chamadas CLI diretas."""
    return AneelArcGisExtractor().extrair_camada(nome_arquivo, layer_id)


def baixar_toda_infraestrutura() -> dict[str, Path]:
    """Ponto de entrada padrão da ingestão ANEEL/ONS."""
    return AneelArcGisExtractor().execute()


if __name__ == "__main__":
    baixar_toda_infraestrutura()
