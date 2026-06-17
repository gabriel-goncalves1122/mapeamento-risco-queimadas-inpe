"""
Configuração compartilhada para relatórios de benchmark por cenário.
"""
from dataclasses import dataclass

from src.analytics.relatorio_builder import RelatorioBuilder


@dataclass(frozen=True)
class ScenarioReportConfig:
    csv_path: str
    sufixo_remover: str
    consulta_alvo: str
    titulo_grafico1: str
    titulo_grafico2: str
    output_pdf_nome: str


def gerar_relatorio_cenario(config: ScenarioReportConfig, latex_template: str) -> None:
    builder = RelatorioBuilder(
        csv_path=config.csv_path,
        sufixo_remover=config.sufixo_remover,
        consulta_alvo=config.consulta_alvo,
        titulo_grafico1=config.titulo_grafico1,
        titulo_grafico2=config.titulo_grafico2,
        latex_template=latex_template,
        output_pdf_nome=config.output_pdf_nome,
    )
    builder.gerar_relatorio()
