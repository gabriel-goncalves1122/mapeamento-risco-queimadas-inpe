"""
Pacote do Motor Espacial da Camada Silver (`src.silver.spatial`).

Cada módulo deste pacote segue a regra "1 Classe Principal por Arquivo" (SRP):
- `SpatialLayerSpec`: especificação imutável da camada (`spatial_layer_spec.py`)
- `DistanceClassifier`: discretização de faixas de distância e coerção de atributos (`distance_classifier.py`)
- `SpatialLayerLoader`: leitura de CSV, reprojeção CRS e criação da R-Tree (`spatial_layer_loader.py`)
- `SpatialLayer`: consultas vetoriais `intersecao` e `proximidade` (`layers.py`)
- `SpatialLayerCatalog`: fábrica e registro das 7 dimensões Silver (`spatial_layer_catalog.py`)
- `MotorEspacial`: orquestrador de ameaças espaciais (`motor_espacial.py`)
"""
from src.silver.spatial.distance_classifier import DistanceClassifier
from src.silver.spatial.layers import SpatialLayer
from src.silver.spatial.motor_espacial import MotorEspacial
from src.silver.spatial.spatial_layer_catalog import SpatialLayerCatalog
from src.silver.spatial.spatial_layer_loader import SpatialLayerLoader
from src.silver.spatial.spatial_layer_spec import SpatialLayerSpec

__all__ = [
    "DistanceClassifier",
    "MotorEspacial",
    "SpatialLayer",
    "SpatialLayerCatalog",
    "SpatialLayerLoader",
    "SpatialLayerSpec",
]
