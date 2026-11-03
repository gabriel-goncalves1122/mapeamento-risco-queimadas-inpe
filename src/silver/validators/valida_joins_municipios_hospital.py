"""
Validador de integridade referencial entre Hospitais CNES e Municípios IBGE.

Implementa `DataValidatorBase` sem executar I/O ou `exit()` durante o import,
permitindo validação programática em memória na suíte de testes e no Dagster.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

from src.core.config.constants import DIMENSIONS_DIR
from src.core.contracts.contracts import DataValidatorBase, ValidationReport

ARQUIVO_HOSPITAIS = os.path.join(str(DIMENSIONS_DIR), "dim_hospitais_cnes.csv")
ARQUIVO_MUNICIPIOS = os.path.join(str(DIMENSIONS_DIR), "dim_municipios_coordenadas.csv")


class HospitalMunicipioJoinValidator(DataValidatorBase):
    """
    Audita a integridade 1:N da chave estrangeira `codigo_ibge` entre as
    dimensões processadas de Hospitais (CNES) e Municípios (IBGE).
    """

    def __init__(
        self,
        hospitais_path: str | Path = ARQUIVO_HOSPITAIS,
        municipios_path: str | Path = ARQUIVO_MUNICIPIOS,
    ) -> None:
        self.hospitais_path = str(hospitais_path)
        self.municipios_path = str(municipios_path)

    def validate(self) -> ValidationReport:
        """Executa o `pd.merge` outer e contabiliza cobertura e registros órfãos."""
        if not os.path.exists(self.hospitais_path):
            raise FileNotFoundError(f"Arquivo de hospitais não encontrado: {self.hospitais_path}")
        if not os.path.exists(self.municipios_path):
            raise FileNotFoundError(f"Arquivo de municípios não encontrado: {self.municipios_path}")

        # Força string em codigo_ibge para preservar zeros à esquerda e evitar mismatch int vs str
        df_hospitais = pd.read_csv(self.hospitais_path, dtype={"codigo_ibge": str})
        df_municipios = pd.read_csv(self.municipios_path, dtype={"codigo_ibge": str})

        total_hospitais = len(df_hospitais)
        total_municipios = len(df_municipios)

        df_validacao = pd.merge(
            df_hospitais,
            df_municipios[["codigo_ibge", "municipios_nome", "estado_sigla", "path_json"]],
            on="codigo_ibge",
            how="outer",
            indicator=True,
        )

        hospitais_com_mapa = df_validacao[df_validacao["_merge"] == "both"]
        hospitais_sem_mapa = df_validacao[df_validacao["_merge"] == "left_only"]

        matched = len(hospitais_com_mapa)
        orphans = len(hospitais_sem_mapa)
        cobertura = round((matched / total_hospitais) * 100.0, 2) if total_hospitais > 0 else 0.0

        top_cidades_df = (
            hospitais_com_mapa.groupby(["codigo_ibge", "municipios_nome", "estado_sigla"])
            .size()
            .reset_index(name="qtd_hospitais")
            .sort_values(by="qtd_hospitais", ascending=False)
            .head(5)
        )
        amostra_orfaos = (
            hospitais_sem_mapa[["codigo_cnes", "nome_hospital", "codigo_ibge"]].head(5).to_dict("records")
            if not hospitais_sem_mapa.empty
            else []
        )

        return ValidationReport(
            validator_name=self.step_name,
            is_valid=(orphans == 0 and total_hospitais > 0),
            total_records=total_hospitais,
            matched_records=matched,
            orphan_records=orphans,
            coverage_pct=cobertura,
            details={
                "total_municipios": total_municipios,
                "top_cidades": top_cidades_df.to_dict("records"),
                "amostra_orfaos": amostra_orfaos,
            },
        )

    def exibir_relatorio(self, report: ValidationReport) -> None:
        """Imprime o resumo de QA formatado para inspeção em terminal."""
        print("Iniciando Validação de Integridade (QA) - Hospitais x Municípios...\n")
        print(f"-> Base de Hospitais carregada: {report.total_records} registros.")
        print(f"-> Base de Municípios carregada: {report.details.get('total_municipios', 0)} registros.\n")
        print("================ RELATÓRIO DE JOIN ================")
        print(f"✅ Hospitais CONECTADOS com sucesso: {report.matched_records} ({report.coverage_pct:.2f}%)")
        print(f"❌ Hospitais DESCONECTADOS (Órfãos): {report.orphan_records}")
        print("===================================================\n")

        print("TOP 5 Municípios com MAIS hospitais conectados:")
        for row in report.details.get("top_cidades", []):
            print(f"- {row['municipios_nome']} ({row['estado_sigla']}): {row['qtd_hospitais']} unidades de saúde")

        print("\n---------------------------------------------------")
        orfaos = report.details.get("amostra_orfaos", [])
        if orfaos:
            print("Atenção! Abaixo estão exemplos de hospitais que não encontraram mapa:")
            print(pd.DataFrame(orfaos).to_string(index=False))
        else:
            print("Mapeamento perfeito! Nenhum hospital ficou sem polígono espacial.")


def executar() -> ValidationReport:
    """Executa a validação e imprime o relatório de QA no terminal."""
    validator = HospitalMunicipioJoinValidator()
    try:
        report = validator.execute()
    except FileNotFoundError as exc:
        print(f"ERRO: Arquivo não encontrado. Execute os scripts de pipeline primeiro.\nDetalhe: {exc}")
        sys.exit(1)
    validator.exibir_relatorio(report)
    return report


if __name__ == "__main__":
    executar()
