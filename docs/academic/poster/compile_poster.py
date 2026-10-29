"""Script de compilação modular do pôster acadêmico em LaTeX.

Executa o pdflatex a partir de main.tex gerando poster_simposio.pdf
e limpa os arquivos auxiliares intermediários.
"""

from pathlib import Path
import subprocess
import sys


def compile_poster() -> None:
    poster_dir = Path(__file__).resolve().parent
    tex_file = poster_dir / "main.tex"
    pdf_file = poster_dir / "poster_simposio.pdf"

    if not tex_file.exists():
        print(f"Erro: Arquivo {tex_file} não encontrado.")
        sys.exit(1)

    print("=" * 60)
    print("Compilando Pôster Acadêmico Modular: main.tex -> poster_simposio.pdf")
    print(f"Diretório: {poster_dir}")
    print("=" * 60)

    for step in (1, 2):
        print(f"\n[Passo {step}/2] Executando pdflatex...")
        res = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-jobname=poster_simposio",
                "main.tex",
            ],
            cwd=str(poster_dir),
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(f"Erro na compilação do passo {step}!")
            print(res.stdout[-1500:])
            sys.exit(res.returncode)

    # Limpeza de arquivos auxiliares
    for ext in (".aux", ".out", ".synctex.gz", ".log"):
        for f in poster_dir.glob(f"*{ext}"):
            try:
                f.unlink()
            except OSError:
                pass

    if pdf_file.exists():
        size_mb = pdf_file.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("Pôster modular compilado com sucesso!")
        print(f"Arquivo: {pdf_file}")
        print(f"Tamanho: {size_mb:.2f} MB")
        print("=" * 60)
    else:
        print("Erro: PDF não gerado.")
        sys.exit(1)


if __name__ == "__main__":
    compile_poster()
