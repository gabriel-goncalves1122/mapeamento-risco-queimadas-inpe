import os
import subprocess

simposio_dir = os.path.dirname(os.path.abspath(__file__))

def compile_pdf(jobname, is_anonymous):
    print(f"\n[{'Anônimo' if is_anonymous else 'Identificado'}] Compilando {jobname}...")
    
    tex_cmd = r"\def\isanonymous{1} \input{resumo_expandido.tex}" if is_anonymous else r"\input{resumo_expandido.tex}"
    
    for step in range(2):
        print(f"Executando pdflatex (passo {step+1}/2) para {jobname}...")
        result = subprocess.run([
            "pdflatex", 
            "-interaction=nonstopmode", 
            f"-jobname={jobname}", 
            tex_cmd
        ], cwd=simposio_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if result.returncode != 0:
            print(f"Erro na compilação do passo {step+1}.")
            return False
            
    return True

print("Iniciando compilação do resumo expandido...")

# Compilar as duas versões
compile_pdf("resumo_expandido_identificado", False)
compile_pdf("resumo_expandido_anonimo", True)

# Limpeza de arquivos temporários
print("\nLimpando arquivos temporários do LaTeX (.aux, .log, .out)...")
for ext in [".aux", ".log", ".out"]:
    for prefix in ["resumo_expandido_identificado", "resumo_expandido_anonimo"]:
        file_path = os.path.join(simposio_dir, prefix + ext)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

print("Compilação dupla concluída com sucesso! Verifique os PDFs gerados.")

