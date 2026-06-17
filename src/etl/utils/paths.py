"""
=========================================================
MÓDULO: paths.py
---------------------------------------------------------
Função Geral: Funções auxiliares e compartilhadas de parsing, matemática e formatação.
=========================================================
"""
import os
from src.config import constants

ROOT_DIR = str(constants.PROJECT_ROOT)

GEO_DIR = str(constants.GEO_DIR)
DIMENSIONS_DIR = str(constants.DIMENSIONS_DIR)

os.makedirs(DIMENSIONS_DIR, exist_ok=True)
