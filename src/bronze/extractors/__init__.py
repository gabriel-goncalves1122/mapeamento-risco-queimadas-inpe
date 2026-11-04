"""Extratores da Camada Bronze do ecossistema CCO DataOps."""
from src.bronze.extractors.ingestao_aneel import AneelArcGisExtractor
from src.bronze.extractors.inpe_queimadas_extractor import InpeQueimadasExtractor

__all__ = [
    "AneelArcGisExtractor",
    "InpeQueimadasExtractor",
]
