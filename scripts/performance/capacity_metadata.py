"""
Metadados compartilhados da matriz de capacidade Druid.

Este modulo e a fonte unica para nomes, recursos alocados e trade-offs dos
cenarios. Relatorios e consolidadores devem importar daqui para evitar que uma
tabela diga "Balanced" enquanto outra calcula com parametros diferentes.
"""
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SQL_DIR = PROJECT_ROOT / "scripts" / "sql" / "performance"
DEFAULT_MATRIX_ROOT = PROJECT_ROOT / "data" / "results" / "performance" / "druid_capacity"
DEFAULT_MATRIX_DIR = DEFAULT_MATRIX_ROOT / "20260630_000802"
DEFAULT_DOCS_ROOT = PROJECT_ROOT / "docs" / "performance" / "druid_capacity"


@dataclass(frozen=True)
class CapacityScenario:
    name: str
    label: str
    short_label: str
    cpu: float
    memory_gb: float
    threads: int
    merge_buffers: int
    tradeoff: str


SCENARIO_PROFILES = (
    CapacityScenario(
        name="scenario_01_baseline",
        label="Cenario 1 - Baseline",
        short_label="Baseline",
        cpu=1.0,
        memory_gb=1.0,
        threads=1,
        merge_buffers=1,
        tradeoff="Menor consumo; maior risco de saturação em joins concorrentes.",
    ),
    CapacityScenario(
        name="scenario_02_balanced",
        label="Cenario 2 - Balanced",
        short_label="Balanced",
        cpu=1.5,
        memory_gb=1.5,
        threads=2,
        merge_buffers=2,
        tradeoff="Uso diário; melhora QPS em concorrência 2, mas ainda falha em concorrência 4.",
    ),
    CapacityScenario(
        name="scenario_03_query_heavy",
        label="Cenario 3 - Query Heavy",
        short_label="Query Heavy",
        cpu=2.0,
        memory_gb=2.0,
        threads=3,
        merge_buffers=3,
        tradeoff="Maior consumo; único perfil estável na concorrência 4.",
    ),
)

SCENARIO_BY_NAME = {scenario.name: scenario for scenario in SCENARIO_PROFILES}
SCENARIO_LABELS = {scenario.name: scenario.label for scenario in SCENARIO_PROFILES}
SCENARIO_CPU = {scenario.name: scenario.cpu for scenario in SCENARIO_PROFILES}
SCENARIO_MEMORY_GB = {scenario.name: scenario.memory_gb for scenario in SCENARIO_PROFILES}


def scenario_profile_rows():
    return [
        {
            "scenario": scenario.name,
            "label": scenario.short_label,
            "cpu": scenario.cpu,
            "memory_gb": scenario.memory_gb,
            "threads": scenario.threads,
            "merge_buffers": scenario.merge_buffers,
            "tradeoff": scenario.tradeoff,
        }
        for scenario in SCENARIO_PROFILES
    ]
