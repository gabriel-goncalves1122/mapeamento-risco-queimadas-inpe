import os
import subprocess
import shutil

def clean_intermediate_files(directory, base_filename):
    """Remove arquivos intermediários gerados pelo LaTeX."""
    extensions = [".aux", ".log", ".out"]
    for ext in extensions:
        file_path = os.path.join(directory, base_filename + ext)
        if os.path.exists(file_path):
            os.remove(file_path)

def compile_latex():
    # Obtém o diretório atual do script (substitui o hardcode)
    simposio_dir = os.path.dirname(os.path.abspath(__file__))
    tex_filename = "template_resumo_expandido_ix_simposio_ic.tex"
    base_filename = tex_filename.replace(".tex", "")
    
    # Verifica se pdflatex está instalado
    if shutil.which("pdflatex") is None:
        print("Erro: 'pdflatex' não encontrado. Certifique-se de que o LaTeX está instalado no sistema.")
        return

    print(f"Compilando {tex_filename} no diretório {simposio_dir}...")
    
    # Executa o pdflatex duas vezes para garantir a criação das referências
    for i in range(2):
        print(f"Executando pdflatex (passo {i+1}/2)...")
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            cwd=simposio_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace"
        )
        
        if result.returncode != 0:
            print("Erro durante a compilação!")
            print(result.stdout)
            return
            
    # Limpa arquivos temporários do LaTeX após sucesso
    print("Limpando arquivos temporários do LaTeX (.aux, .log, .out)...")
    clean_intermediate_files(simposio_dir, base_filename)
            
    print("Compilação concluída com sucesso! O arquivo resumo_expandido.pdf foi gerado e atualizado.")

if __name__ == "__main__":
    compile_latex()
