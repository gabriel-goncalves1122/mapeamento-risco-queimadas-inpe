import os
import subprocess
import shutil

def clean_intermediate_files(directory, base_filename):
    """Remove arquivos intermediários gerados pelo LaTeX."""
    extensions = [".aux", ".log", ".out", ".bbl", ".blg", ".toc", ".lof", ".lot"]
    for ext in extensions:
        file_path = os.path.join(directory, base_filename + ext)
        if os.path.exists(file_path):
            os.remove(file_path)

def compile_latex():
    # Obtém o diretório atual do script
    simposio_dir = os.path.dirname(os.path.abspath(__file__))
    tex_filename = "main.tex"
    base_filename = "main"
    
    # Verifica se pdflatex e bibtex estão instalados
    if shutil.which("pdflatex") is None:
        print("Erro: 'pdflatex' não encontrado. Certifique-se de que o LaTeX está instalado no sistema.")
        return

    if shutil.which("bibtex") is None:
        print("Aviso: 'bibtex' não encontrado. As referências não serão compiladas.")
        has_bibtex = False
    else:
        has_bibtex = True

    print(f"Compilando {tex_filename} no diretório {simposio_dir}...")
    
    # Passo 1: pdflatex
    print("Passo 1/4: pdflatex (construção inicial)")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], cwd=simposio_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if has_bibtex:
        # Passo 2: bibtex
        print("Passo 2/4: bibtex (processando bibliografia)")
        subprocess.run(["bibtex", base_filename], cwd=simposio_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        # Passo 3: pdflatex
        print("Passo 3/4: pdflatex (integrando referências)")
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], cwd=simposio_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Passo 4: pdflatex final
    print("Passo 4/4: pdflatex (resolvendo referências cruzadas finais)")
    result = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], cwd=simposio_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")

    if result.returncode != 0:
        print("Erro durante a compilação!")
        print(result.stdout)
        return
            
    # Limpa arquivos temporários do LaTeX após sucesso
    print("Limpando arquivos intermediários (.aux, .log, .bbl, .blg)...")
    clean_intermediate_files(simposio_dir, base_filename)
            
    print("Compilação concluída com sucesso! O arquivo main.pdf foi gerado e atualizado.")

if __name__ == "__main__":
    compile_latex()
