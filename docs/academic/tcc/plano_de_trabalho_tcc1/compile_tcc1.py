"""
Script procedural de compilação do Plano de Trabalho de TCC01 (UNIFEI).
Execução: uv run python docs/academic/tcc/plano_de_trabalho_tcc1/compile_tcc1.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def compile_pdf() -> bool:
    print(f"[*] Diretório de trabalho: {BASE_DIR}")

    compiler = None
    if shutil.which("pdflatex"):
        compiler = "pdflatex"
    elif shutil.which("xelatex"):
        compiler = "xelatex"
    elif shutil.which("lualatex"):
        compiler = "lualatex"
    else:
        print("[!] Erro: Nenhum compilador compatível (pdflatex, xelatex ou lualatex) foi encontrado.")
        return False

    print(f"[*] Utilizando compilador: {compiler}")

    # 1. Primeira passagem do LaTeX
    print("[1/4] Executando primeira passagem LaTeX...")
    res = subprocess.run(
        [compiler, "--interaction=nonstopmode", "main.tex"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        print(f"[!] Aviso/Erro na 1ª passagem:\n{res.stdout[-1500:]}")

    # 2. Execução do BibTeX
    print("[2/4] Executando BibTeX...")
    res_bib = subprocess.run(
        ["bibtex", "main"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res_bib.returncode != 0:
        print(f"[!] Aviso BibTeX:\n{res_bib.stdout}")

    # 3. Segunda passagem
    print("[3/4] Executando segunda passagem LaTeX...")
    subprocess.run(
        [compiler, "--interaction=nonstopmode", "main.tex"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # 4. Terceira passagem (estabilização de referências e sumário)
    print("[4/4] Executando terceira passagem LaTeX...")
    subprocess.run(
        [compiler, "--interaction=nonstopmode", "main.tex"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    pdf_path = BASE_DIR / "main.pdf"
    if pdf_path.exists():
        size_kb = pdf_path.stat().st_size / 1024
        print(f"\n[OK] main.pdf gerado com sucesso! ({size_kb:.1f} KB)")
        print(f"[OK] Caminho: {pdf_path}")
        return True
    else:
        print("\n[!] Falha: main.pdf não foi gerado.")
        return False


if __name__ == "__main__":
    success = compile_pdf()
    sys.exit(0 if success else 1)
