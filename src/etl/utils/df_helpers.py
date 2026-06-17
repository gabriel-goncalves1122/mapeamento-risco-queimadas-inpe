"""
=========================================================
MÓDULO: Auxiliares de DataFrame (df_helpers.py)
---------------------------------------------------------
Função Geral: Fornece tipagem segura e conversões robustas
para dados tabulares (Pandas), assegurando que o ETL não 
quebre ao encontrar nulos e garantindo a escrita CSV correta.
=========================================================
"""
import csv
import math
import re
import pandas as pd


def limpar_numero(valor, default=0.0):
    """
    Converte valores numéricos sujos (strings com vírgula, caracteres invisíveis) em floats.
    Se a conversão falhar ou resultar em NaN/Infinito, retorna um fallback (default=0.0).
    Essencial para garantir que os agregadores do Apache Druid não crashem ao ler o dado.
    """
    try:
        if pd.isna(valor):
            return default

        texto = str(valor).strip()
        texto = texto.replace(',', '.')
        texto = re.sub(r'[^0-9.\-]', '', texto)

        if texto == "":
            return default

        numero = float(texto)

        if math.isnan(numero) or math.isinf(numero):
            return default

        return numero

    except Exception:
        return default


def coordenada_valida(lat, lon):
    """
    Checa se uma coordenada faz sentido geográfico no globo terrestre.
    Elimina dados lixo (0,0 no Golfo da Guiné ou coordenadas irreais tipo lat 999).
    """
    if lat is None or lon is None:
        return False

    if not (-90 <= lat <= 90):
        return False

    if not (-180 <= lon <= 180):
        return False

    if lat == 0.0 and lon == 0.0:
        return False

    return True


def salvar_csv(df, caminho):
    df.to_csv(
        caminho,
        index=False,
        encoding='utf-8',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator='\n'
    )
