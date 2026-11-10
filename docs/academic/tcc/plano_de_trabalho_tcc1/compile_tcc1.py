"""
Script procedural de compilação do Plano de Trabalho de TCC01 (UNIFEI).
Gera o documento nomeado como GabrielGoncalves_TCC1.pdf e limpa arquivos auxiliares (.aux, .log, .out, etc.).
Execução: uv run python docs/academic/tcc/plano_de_trabalho_tcc1/compile_tcc1.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEX_BASENAME = "main"
OUTPUT_BASENAME = "GabrielGoncalves_TCC1"


def clean_intermediate_files(directory: Path, base_filename: str):
    """Remove arquivos intermediários gerados pelo LaTeX e BibTeX."""
    extensions = [
        ".aux",
        ".log",
        ".out",
        ".bbl",
        ".blg",
        ".toc",
        ".lof",
        ".lot",
        ".fls",
        ".fdb_latexmk",
        ".synctex.gz",
    ]
    for ext in extensions:
        file_path = directory / f"{base_filename}{ext}"
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass


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
        [compiler, "-interaction=nonstopmode", f"{TEX_BASENAME}.tex"],
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
    subprocess.run(
        ["bibtex", TEX_BASENAME],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # 3. Segunda passagem
    print("[3/4] Executando segunda passagem LaTeX...")
    subprocess.run(
        [compiler, "-interaction=nonstopmode", f"{TEX_BASENAME}.tex"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # 4. Terceira passagem (estabilização de referências e citações)
    print("[4/4] Executando terceira passagem LaTeX...")
    res_final = subprocess.run(
        [compiler, "-interaction=nonstopmode", f"{TEX_BASENAME}.tex"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if res_final.returncode != 0:
        print(f"[!] Erro na compilação final:\n{res_final.stdout[-2000:]}")
        clean_intermediate_files(BASE_DIR, TEX_BASENAME)
        return False

    # Renomeia / copia para o nome padronizado solicitado
    src_pdf = BASE_DIR / f"{TEX_BASENAME}.pdf"
    target_pdf = BASE_DIR / f"{OUTPUT_BASENAME}.pdf"

    if src_pdf.exists():
        shutil.copy2(src_pdf, target_pdf)
        
        # Sincroniza também no diretório espelho de templates
        mirror_dir = BASE_DIR.parent / "exemplos_e_templates" / "templates_latex" / "ECO_plano_de_trabalho_TCC01"
        if mirror_dir.exists():
            shutil.copy2(target_pdf, mirror_dir / f"{OUTPUT_BASENAME}.pdf")
            shutil.copy2(src_pdf, mirror_dir / f"{TEX_BASENAME}.pdf")
            clean_intermediate_files(mirror_dir, TEX_BASENAME)

        # Limpeza estrita de arquivos intermediários
        print("[*] Limpando arquivos auxiliares (.aux, .log, .out, .bbl, .blg)...")
        clean_intermediate_files(BASE_DIR, TEX_BASENAME)

        size_kb = target_pdf.stat().st_size / 1024
        print(f"\n[OK] Documento gerado com sucesso: {target_pdf.name} ({size_kb:.1f} KB)")
        print(f"[OK] Caminho: {target_pdf}")
        return True
    else:
        print(f"\n[!] Falha: {src_pdf.name} não foi gerado.")
        clean_intermediate_files(BASE_DIR, TEX_BASENAME)
        return False


if __name__ == "__main__":
    success = compile_pdf()
    sys.exit(0 if success else 1)
