"""
=========================================================
MÓDULO: relatorio_builder.py
---------------------------------------------------------
Função Geral: Abstrai e executa testes analíticos ou geração de relatórios de benchmark do Druid.
=========================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess

class RelatorioBuilder:
    def __init__(self, csv_path, sufixo_remover, consulta_alvo, titulo_grafico1, titulo_grafico2, latex_template, output_pdf_nome):
        self.csv_path = csv_path
        self.sufixo_remover = sufixo_remover
        self.consulta_alvo = consulta_alvo
        self.titulo_grafico1 = titulo_grafico1
        self.titulo_grafico2 = titulo_grafico2
        self.latex_template = latex_template
        self.output_pdf_nome = output_pdf_nome
        self.output_dir = "data/results/docs"

    def gerar_relatorio(self):
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📊 Iniciando a geração do {self.output_pdf_nome}...")
        
        try:
            df = pd.read_csv(self.csv_path)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {self.csv_path}. Execute o benchmark primeiro.")
            return

        df['Nome_Limpo'] = df['Nome_Consulta'].str.replace(self.sufixo_remover, '', regex=False).str.replace('_', ' ')

        # Geração de Gráficos
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.family'] = 'serif'

        # Gráfico 1
        plt.figure(figsize=(10, 5))
        bar_width = 0.35
        index = np.arange(len(df['Nome_Limpo']))

        plt.bar(index, df['Media_Cold_ms'], bar_width, label='Cold Start (I/O Disco)', color='#4c72b0', edgecolor='black')
        plt.bar(index + bar_width, df['Media_Warm_ms'], bar_width, label='Warm Start (Cache RAM)', color='#55a868', edgecolor='black')

        plt.ylabel('Tempo de Resposta (ms)', fontsize=11)
        plt.title(self.titulo_grafico1, fontsize=12, fontweight='bold')
        plt.xticks(index + bar_width / 2, df['Nome_Limpo'], rotation=35, ha='right', fontsize=9)
        plt.legend(frameon=True, shadow=True)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/fig_desemp_{self.output_pdf_nome}.png", dpi=300)
        plt.close()

        # Gráfico 2
        if self.consulta_alvo in df['Nome_Consulta'].values:
            linha_alvo = df[df['Nome_Consulta'] == self.consulta_alvo].iloc[0]
        else:
            linha_alvo = df.iloc[1]

        cold_runs = [linha_alvo[f'Cold_{i}_ms'] for i in range(1, 8)]
        warm_runs = [linha_alvo[f'Warm_{i}_ms'] for i in range(1, 8)]

        plt.figure(figsize=(9, 4.5))
        plt.plot(range(1, 8), cold_runs, marker='D', linestyle='-', color='#4c72b0', linewidth=2, label='Cold Start')
        plt.plot(range(1, 8), warm_runs, marker='s', linestyle='--', color='#55a868', linewidth=2, label='Warm Start')

        plt.xlabel('Iteração (Rodada)', fontsize=11)
        plt.ylabel('Latência Computacional (ms)', fontsize=11)
        plt.title(self.titulo_grafico2, fontsize=12, fontweight='bold')
        plt.xticks(range(1, 8))
        plt.legend(frameon=True, shadow=True)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/fig_var_{self.output_pdf_nome}.png", dpi=300)
        plt.close()

        # Tabela LaTeX
        tabela_linhas = []
        for _, row in df.iterrows():
            nome = str(row['Nome_Limpo'])
            cold = f"{row['Media_Cold_ms']:.2f}"
            warm = f"{row['Media_Warm_ms']:.2f}"
            ganho = f"{row['Ganho_Cache_%']:.2f}"
            linhas = str(row['Linhas_Retornadas'])
            tabela_linhas.append(f"    {nome} & {cold} & {warm} & {ganho}\\% & {linhas} \\\\\n")

        conteudo_tabela = "".join(tabela_linhas)

        latex_document = self.latex_template.replace("___CONTEUDO_TABELA___", conteudo_tabela)
        
        # O replace da string de imagem para usar o nome dinâmico
        latex_document = latex_document.replace("fig_desemp_cenario", f"fig_desemp_{self.output_pdf_nome}")
        latex_document = latex_document.replace("fig_var_cenario", f"fig_var_{self.output_pdf_nome}")

        tex_path = f"{self.output_dir}/{self.output_pdf_nome}.tex"
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_document)

        print(f"⚙️ Compilando o PDF do {self.output_pdf_nome}...")
        try:
            comando = ['pdflatex', '-interaction=nonstopmode', f'{self.output_pdf_nome}.tex']
            subprocess.run(comando, cwd=self.output_dir, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(comando, cwd=self.output_dir, check=True, stdout=subprocess.DEVNULL)
            print(f"🎓 SUCESSO! Relatório pronto em: {self.output_dir}/{self.output_pdf_nome}.pdf")
        except subprocess.CalledProcessError:
            print("⚠️ Aviso: O pdflatex retornou um código de erro. O PDF pode ter sido gerado com alertas.")
            print(f"Verifique o arquivo: {self.output_dir}/{self.output_pdf_nome}.pdf")
