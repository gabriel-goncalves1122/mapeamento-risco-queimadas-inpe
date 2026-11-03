"""
Renderizador de documentos e tabelas LaTeX (`LatexReportWriter`).

Encapsula o escape de caracteres reservados do TeX, a formatação numérica e a
geração de blocos `longtable` e `figure` para os relatórios científicos de
capacidade do Apache Druid (SRP).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pandas as pd


class LatexReportWriter:
    """Serviço de geração de fragmentos e tabelas LaTeX (`booktabs` / `longtable`)."""

    LATEX_REPLACEMENTS: dict[str, str] = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    @classmethod
    def latex_escape(cls, value: Any) -> str:
        """Escapa caracteres especiais do LaTeX preservando texto legível."""
        text = "" if value is None else str(value)
        return "".join(cls.LATEX_REPLACEMENTS.get(char, char) for char in text)

    @staticmethod
    def format_value(value: Any, decimals: int = 3) -> str:
        """Formata floats com precisão fixa descartando `None` e `NaN`."""
        if value is None or pd.isna(value):
            return ""
        if isinstance(value, str):
            return value
        try:
            return f"{float(value):.{decimals}f}"
        except (TypeError, ValueError):
            return str(value)

    @classmethod
    def to_latex_table(
        cls,
        path: Path,
        dataframe: pd.DataFrame,
        columns: Sequence[str],
        headers: Sequence[str],
        caption: str | None = None,
        widths: Sequence[str] | None = None,
        font_size: str = r"\small",
        landscape: bool = False,
    ) -> Path:
        """Exporta um DataFrame para um arquivo `.tex` usando ambiente `longtable`."""
        spec = "".join(widths) if widths else "l" * len(columns)
        lines: list[str] = []
        if landscape:
            lines.append(r"\begin{landscape}")
        lines.append("{")
        lines.append(font_size)
        lines.append(r"\setlength{\tabcolsep}{4pt}")
        lines.append(r"\renewcommand{\arraystretch}{1.15}")
        lines.append(r"\begin{longtable}{" + spec + "}")
        if caption:
            lines.append(r"\caption{" + cls.latex_escape(caption) + r"}\\")
        lines.append(r"\toprule")
        lines.append(" & ".join(cls.latex_escape(header) for header in headers) + r" \\")
        lines.append(r"\midrule")
        lines.append(r"\endfirsthead")
        lines.append(r"\toprule")
        lines.append(" & ".join(cls.latex_escape(header) for header in headers) + r" \\")
        lines.append(r"\midrule")
        lines.append(r"\endhead")
        for _, row in dataframe.iterrows():
            values = []
            for col in columns:
                value = row.get(col, "")
                if isinstance(value, float):
                    value = cls.format_value(value)
                values.append(cls.latex_escape(value))
            lines.append(" & ".join(values) + r" \\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{longtable}")
        lines.append("}")
        if landscape:
            lines.append(r"\end{landscape}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    @classmethod
    def latex_preamble(cls, title: str) -> str:
        """Retorna o preâmbulo padrão ABNT/A4 com suporte a `longtable` e `listings`."""
        return rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[brazil]{{babel}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{float}}
\usepackage{{xcolor}}
\usepackage{{listings}}
\usepackage{{pdflscape}}
\usepackage{{placeins}}
\usepackage[hidelinks]{{hyperref}}
\geometry{{margin=2.1cm}}
\setlength{{\parskip}}{{0.5em}}
\setlength{{\parindent}}{{0pt}}
\lstset{{
  basicstyle=\ttfamily\footnotesize,
  breaklines=true,
  columns=fullflexible,
  frame=single,
  showstringspaces=false,
  keywordstyle=\color{{blue}},
  commentstyle=\color{{gray}}
}}
\title{{{cls.latex_escape(title)}}}
\author{{CCO DataOps}}
\date{{30 de junho de 2026}}
\begin{{document}}
\maketitle
"""

    @staticmethod
    def latex_end() -> str:
        return "\n\\end{document}\n"

    @classmethod
    def figure_block(cls, filename: str, caption: str, label: str) -> str:
        return (
            rf"\begin{{figure}}[H]\centering"
            rf"\includegraphics[width=0.92\textwidth,height=0.42\textheight,keepaspectratio]{{../figures/{filename}}}"
            rf"\caption{{{cls.latex_escape(caption)}}}\label{{fig:{label}}}\end{{figure}}"
        )


latex_escape = LatexReportWriter.latex_escape
format_value = LatexReportWriter.format_value
to_latex_table = LatexReportWriter.to_latex_table
latex_preamble = LatexReportWriter.latex_preamble
latex_end = LatexReportWriter.latex_end
figure_block = LatexReportWriter.figure_block
