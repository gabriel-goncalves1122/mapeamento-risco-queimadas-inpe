"""
Orquestrador orientado a objetos das dimensões espaciais (`DimensionETLOrchestrator`).

Substitui o disparo acoplado de subprocessos por composição polimórfica sobre
contratos `ExecutablePipelineStep` e `DataValidatorBase` (OCP / DIP).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

_ROOT = str(Path(__file__).resolve().parents[3])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core.contracts.contracts import DataValidatorBase, ExecutablePipelineStep, ValidationReport
from src.bronze.extractors.ingestao_aneel import AneelArcGisExtractor
from src.silver.etl.etl_dim_hospitais import ETLDimHospitais
from src.silver.etl.etl_dim_municipios import ETLDimMunicipios
from src.silver.etl.etl_dim_ons_linhas_transmissao import ETLDimLinhasTransmissao
from src.silver.etl.etl_dim_ons_sistemas_isolados import ETLDimSistemasIsolados
from src.silver.etl.etl_dim_ons_subestacoes import ETLDimSubestacoes
from src.silver.etl.etl_dim_rodovias_federais import ETLDimRodoviasFederais
from src.silver.etl.etl_dim_terras_indigenas import ETLDimTerrasIndigenas
from src.silver.validators.dimensao_integridade_validator import DimensionIntegrityValidator
from src.silver.validators.valida_joins_municipios_hospital import HospitalMunicipioJoinValidator

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRONZE_SRC = PROJECT_ROOT / "src" / "bronze" / "extractors"
VALIDATORS_DIR = CURRENT_DIR.parent / "validators"

# Mantido para retrocompatibilidade com scripts externos que inspecionam a ordem batch
SCRIPTS_PIPELINE = [
    ("etl_dim_municipios.py", CURRENT_DIR / "etl_dim_municipios.py"),
    ("etl_dim_hospitais.py", CURRENT_DIR / "etl_dim_hospitais.py"),
    ("etl_dim_terras_indigenas.py", CURRENT_DIR / "etl_dim_terras_indigenas.py"),
    ("etl_dim_rodovias_federais.py", CURRENT_DIR / "etl_dim_rodovias_federais.py"),
    ("ingestao_aneel.py", BRONZE_SRC / "ingestao_aneel.py"),
    ("etl_dim_ons_linhas_transmissao.py", CURRENT_DIR / "etl_dim_ons_linhas_transmissao.py"),
    ("etl_dim_ons_subestacoes.py", CURRENT_DIR / "etl_dim_ons_subestacoes.py"),
    ("etl_dim_ons_sistemas_isolados.py", CURRENT_DIR / "etl_dim_ons_sistemas_isolados.py"),
]

SCRIPTS_VALIDACAO = [
    ("valida_joins_municipios_hospital.py", VALIDATORS_DIR / "valida_joins_municipios_hospital.py"),
]


class DimensionETLOrchestrator(ExecutablePipelineStep):
    """
    Controlador de execução das dimensões da camada Silver.

    Executa sequencialmente cada classe de dimensão em memória, cronometrando
    a latência individual e consolidando os relatórios de qualidade dos validadores.
    """

    def __init__(
        self,
        steps: Sequence[ExecutablePipelineStep] | None = None,
        validators: Sequence[DataValidatorBase] | None = None,
    ) -> None:
        self.steps = list(steps) if steps is not None else [
            ETLDimMunicipios(),
            ETLDimHospitais(),
            ETLDimTerrasIndigenas(),
            ETLDimRodoviasFederais(),
            AneelArcGisExtractor(),
            ETLDimLinhasTransmissao(),
            ETLDimSubestacoes(),
            ETLDimSistemasIsolados(),
        ]
        self.validators = list(validators) if validators is not None else [
            HospitalMunicipioJoinValidator(),
            DimensionIntegrityValidator(),
        ]

    def _executar_etapa(self, step: ExecutablePipelineStep) -> Any:
        print(f"\n--- [POO] Executando componente: {step.step_name} ---")
        return step.execute()

    def _executar_validador(self, validator: DataValidatorBase) -> ValidationReport:
        print(f"\n--- [QA] Executando validador: {validator.step_name} ---")
        relatorio = validator.execute()
        status_icone = "PASSOU" if relatorio.is_valid else "FALHOU"
        print(
            f"   [{status_icone}] Cobertura: {relatorio.coverage_pct:.1f}% "
            f"({relatorio.matched_records}/{relatorio.total_records} registros)"
        )
        return relatorio

    def _run(self, *args: Any, **kwargs: Any) -> list[ValidationReport]:
        print("\nINICIANDO ORQUESTRACAO DO DATA LAKEHOUSE (ETL BATCH)")
        print(f"Diretório base: {CURRENT_DIR}")
        inicio_total = time.perf_counter()

        resultados_etapas: dict[str, Any] = {}
        for step in self.steps:
            resultados_etapas[step.step_name] = self._executar_etapa(step)

        print("\nINICIANDO AUDITORIA E TESTES DE CONTRATO (QA)")
        relatorios_validacao: list[ValidationReport] = []
        for val in self.validators:
            relatorios_validacao.append(self._executar_validador(val))

        tempo_total_s = time.perf_counter() - inicio_total
        print(f"\nETL e Auditoria concluídos com sucesso em {tempo_total_s:.2f} segundos!")

        return relatorios_validacao


def rodar_script(nome_script: str, caminho_completo: Path) -> None:
    """Fallback procedural para compatibilidade retroativa."""
    print(f"\n--- Executando: {nome_script} ---")
    if not caminho_completo.exists():
        print(f"Erro: Arquivo não encontrado: {caminho_completo}")
        sys.exit(1)

    resultado = subprocess.run([sys.executable, str(caminho_completo)], capture_output=False)
    if resultado.returncode != 0:
        print(f"\n[ERRO CRÍTICO] Falha ao executar {nome_script}.")
        sys.exit(resultado.returncode)


def orquestrar_etl() -> list[ValidationReport]:
    """Ponto de entrada canônico da camada Silver."""
    return DimensionETLOrchestrator().execute()


if __name__ == "__main__":
    orquestrar_etl()
