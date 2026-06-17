"""
=========================================================
MÓDULO: etl_dim_infraestrutura.py
---------------------------------------------------------
Função Geral: Pipeline ETL para extração, limpeza e carga de Tabelas de Dimensão espaciais para o Apache Druid.
=========================================================
"""
from src.etl.pipelines.etl_dim_rodovias_federais import processar_rodovias
from src.etl.pipelines.etl_dim_ons_linhas_transmissao import processar_linhas_ons
from src.etl.pipelines.etl_dim_ons_subestacoes import processar_subestacoes_ons
from src.etl.pipelines.etl_dim_ons_sistemas_isolados import processar_sistemas_isolados


def main():
    print("==================================================")
    print("🏗️ PROCESSANDO DIMENSÕES DE INFRAESTRUTURA")
    print("==================================================")

    processar_rodovias()
    processar_linhas_ons()
    processar_subestacoes_ons()
    processar_sistemas_isolados()

    print("\n✅ ETL de infraestrutura finalizado.")


if __name__ == '__main__':
    main()
