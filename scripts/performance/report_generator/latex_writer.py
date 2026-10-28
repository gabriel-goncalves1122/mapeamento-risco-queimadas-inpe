import pandas as pd
def latex_escape(value):
    text = "" if value is None else str(value)
    replacements = {
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
    return "".join(replacements.get(char, char) for char in text)

def format_value(value, decimals=3):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def to_latex_table(path, dataframe, columns, headers, caption=None, widths=None, font_size=r"\small", landscape=False):
    spec = "".join(widths) if widths else "l" * len(columns)
    lines = []
    if landscape:
        lines.append(r"\begin{landscape}")
    lines.append("{")
    lines.append(font_size)
    lines.append(r"\setlength{\tabcolsep}{4pt}")
    lines.append(r"\renewcommand{\arraystretch}{1.15}")
    lines.append(r"\begin{longtable}{" + spec + "}")
    if caption:
        lines.append(r"\caption{" + latex_escape(caption) + r"}\\")
    lines.append(r"\toprule")
    lines.append(" & ".join(latex_escape(header) for header in headers) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(r"\toprule")
    lines.append(" & ".join(latex_escape(header) for header in headers) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    for _, row in dataframe.iterrows():
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = format_value(value)
            values.append(latex_escape(value))
        lines.append(" & ".join(values) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    lines.append("}")
    if landscape:
        lines.append(r"\end{landscape}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def latex_preamble(title):
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
\title{{{latex_escape(title)}}}
\author{{CCO DataOps}}
\date{{30 de junho de 2026}}
\begin{{document}}
\maketitle
"""


def latex_end():
    return "\n\\end{document}\n"

def figure_block(filename, caption, label):
    return (
        rf"\begin{{figure}}[H]\centering"
        rf"\includegraphics[width=0.92\textwidth,height=0.42\textheight,keepaspectratio]{{../figures/{filename}}}"
        rf"\caption{{{latex_escape(caption)}}}\label{{fig:{label}}}\end{{figure}}"
    )

