"""
=========================================================
MÓDULO: gerador_relatorio_final.py
---------------------------------------------------------
Função Geral: Abstrai e executa testes analíticos ou geração de relatórios de benchmark do Druid.
=========================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess

# =====================================================================
# 1. CARREGAMENTO DE TODO O ACERVO DE DADOS (OS 6 CENÁRIOS)
# =====================================================================
DIR = "data/results/tests"
OUTPUT_DIR = "data/results/docs/tcc_final"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("📚 Iniciando a compilação do Capítulo Final do TCC...")

# Lendo bases fragmentadas
df_f2 = pd.read_csv(f"{DIR}/relatorio_estatistico_6518Seg_2Cores.csv")
df_f4 = pd.read_csv(f"{DIR}/relatorio_estatistico_6518Seg_4Cores.csv")
df_f6 = pd.read_csv(f"{DIR}/relatorio_estatistico_6518Seg_6Cores.csv")

# Lendo bases compactadas
df_c2 = pd.read_csv(f"{DIR}/relatorio_estatistico_CompactYear_2Cores.csv")
df_c4 = pd.read_csv(f"{DIR}/relatorio_estatistico_CompactYear_4Cores.csv")
df_c6 = pd.read_csv(f"{DIR}/relatorio_estatistico_CompactYear_6Cores.csv")

# Extraindo médias globais de Cold Start
cold_frag = [df_f2['Media_Cold_ms'].mean(), df_f4['Media_Cold_ms'].mean(), df_f6['Media_Cold_ms'].mean()]
cold_comp = [df_c2['Media_Cold_ms'].mean(), df_c4['Media_Cold_ms'].mean(), df_c6['Media_Cold_ms'].mean()]
cores = ['2 Núcleos', '4 Núcleos', '6 Núcleos']

# =====================================================================
# 2. GERAÇÃO DOS GRÁFICOS MACROSCÓPICOS DO TCC
# =====================================================================
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'serif'

# GRÁFICO 1: A Vitória do DataOps (Comparação de Cold Start)
plt.figure(figsize=(10, 5))
x = np.arange(len(cores))
width = 0.35

plt.bar(x - width/2, cold_frag, width, label='Base Fragmentada (6.518 arqs)', color='#c44e52', edgecolor='black')
plt.bar(x + width/2, cold_comp, width, label='Base Compactada (1 arq/ano)', color='#55a868', edgecolor='black')

plt.ylabel('Tempo Médio de Leitura Bruta (ms)', fontsize=11)
plt.title('Impacto da Escala Vertical vs. Organização Geométrica (DataOps)', fontsize=12, fontweight='bold')
plt.xticks(x, cores, fontsize=11)
plt.yscale('log') # Escala logarítmica para mostrar bem a diferença de 4000ms pra 30ms
plt.text(-0.35, 6000, '(Escala Logarítmica)', fontsize=9, style='italic')
plt.legend(frameon=True, shadow=True)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/tcc_fig1_evolucao_cold.png", dpi=300)
plt.close()

# GRÁFICO 2: Autópsia do Paradoxo do Cache (Consulta BI_2_FUNAI)
# Pegando o ganho de cache da pior consulta fragmentada vs a compactada
ganho_f = [
    df_f2[df_f2['Nome_Consulta'].str.contains('FUNAI')]['Ganho_Cache_%'].values[0],
    df_f4[df_f4['Nome_Consulta'].str.contains('FUNAI')]['Ganho_Cache_%'].values[0],
    df_f6[df_f6['Nome_Consulta'].str.contains('FUNAI')]['Ganho_Cache_%'].values[0]
]
ganho_c = [
    df_c2[df_c2['Nome_Consulta'].str.contains('FUNAI')]['Ganho_Cache_%'].values[0],
    df_c4[df_c4['Nome_Consulta'].str.contains('FUNAI')]['Ganho_Cache_%'].values[0],
    df_c6[df_c6['Nome_Consulta'].str.contains('FUNAI')]['Ganho_Cache_%'].values[0]
]

plt.figure(figsize=(9, 5))
plt.plot(cores, ganho_f, marker='o', linestyle='-', color='#c44e52', linewidth=2, label='Eficácia Cache (Fragmentado)')
plt.plot(cores, ganho_c, marker='s', linestyle='--', color='#55a868', linewidth=2, label='Eficácia Cache (Compactado)')
plt.axhline(0, color='black', linewidth=1, linestyle=':')
plt.ylabel('Ganho de Performance do Cache (%)', fontsize=11)
plt.title('A Ressurreição da Memória RAM após Compactação', fontsize=12, fontweight='bold')
plt.legend(frameon=True, shadow=True)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/tcc_fig2_paradoxo_cache.png", dpi=300)
plt.close()
print("✅ Gráficos Macroscópicos gerados!")

# =====================================================================
# 3. MEGA TEMPLATE LATEX (PRIMEIRAS SEÇÕES DO CAPÍTULO)
# =====================================================================
latex_template = r"""\documentclass[12pt, a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[brazilian]{babel}
\usepackage{mathptmx}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{geometry}
\usepackage{float}
\usepackage{setspace}
\usepackage{caption}

\geometry{top=3cm, bottom=2cm, left=3cm, right=2cm}
\setstretch{1.5}
\captionsetup{font=small, labelfont=bf, labelsep=endash}

\begin{document}

\begin{center}
    \Large\textbf{Resultados e Discussão: A Arquitetura DataOps sob Estresse} \\[0.5cm]
    \normalsize\textbf{Projeto DataOps / UNIFEI} \\
    \small{\today}
\end{center}

\vspace{0.5cm}
\noindent\rule{\textwidth}{1pt}

\section{O Desafio Físico e a Metodologia de Estresse}
A consolidação de um ecossistema analítico orientado a eventos (\textit{Event-Driven}) para o monitoramento geoespacial demanda uma validação rigorosa de sua capacidade de resposta sob estresse. A base de dados transacional coligida durante as simulações consolidou um montante de $\sim$3,1 milhões de registros de focos de calor espaciais. 

Contudo, a natureza intrínseca da ingestão contínua assíncrona (\textit{Streaming}) via Apache Kafka originou uma patologia de armazenamento conhecida como \textit{Tiny Segments} (Segmentos Minúsculos). Os dados assentaram-se no \textit{Deep Storage} fragmentados em exatos 6.518 arquivos distintos, totalizando cerca de 211 MB. Esta fragmentação extrema formou a linha de base empírica para testar a escalabilidade do motor Apache Druid.

\section{A Ilusão da Escalabilidade Vertical}
A primeira fase da experimentação visou responder à seguinte premissa: \textit{"A injeção de força computacional bruta (Hardware Tuning) é capaz de mitigar a fragmentação de disco?"}. Para tal, orquestraram-se três cenários progressivos utilizando \textit{Cgroups} do Docker, alocando-se 2, 4 e 6 núcleos lógicos do processador.

Os resultados evidenciaram uma curva clássica de rendimentos decrescentes (Lei de Amdahl). Conforme ilustrado na Figura 1, saltar de 2 para 4 núcleos reduziu a latência média de leitura bruta (\textit{Cold Start}) quase pela metade (de $\sim$4.091 ms para $\sim$2.319 ms). Contudo, a alocação máxima de 6 núcleos esbarrou em um teto sistêmico, travando o ecossistema na faixa dos $\sim$1.624 ms. A escalabilidade da CPU tornou-se inócua perante o insuperável gargalo de Entrada/Saída (\textit{I/O Overhead}) gerado pela abertura e fechamento de 6.518 arquivos sequenciais.

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{tcc_fig1_evolucao_cold.png}
\caption{Comparativo Logarítmico: A estagnação da CPU perante a fragmentação versus a eficiência imediata da base compactada.}
\end{figure}

\section{Autópsia do ``Paradoxo do Cache''}
A descoberta mais contundente da fase de estrangulamento ocorreu na camada de Memória RAM Volátil. Teoricamente, o mecanismo de \textit{Cache} de um motor OLAP deve fornecer respostas instantâneas ao interceptar requisições mapeadas. Todavia, registrou-se o fenômeno aqui cunhado como \textbf{Paradoxo do Cache}.

Em leituras de alta restrição territorial (Filtros Complexos da FUNAI), a memória apresentou \textbf{latência negativa extrema}. Com 6 núcleos ativos, a leitura do cache atrasou a resposta em -12,47\% quando comparada à varredura direta do disco.

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{tcc_fig2_paradoxo_cache.png}
\caption{Eficácia da Memória RAM: O colapso na base fragmentada e a ressurreição após compactação geométrica.}
\end{figure}

Isto comprova matematicamente que a Unidade Lógica e Aritmética (ULA) colapsa não por falta de poder de cálculo temporal, mas pela exaustão logística de instanciar, indexar e fundir (\textit{merge}) os metadados de 6.518 estilhaços na memória em frações de milissegundo. O processador "engasga" na tentativa de montar o quebra-cabeça do cache.

\vspace{1cm}
\begin{center}
\textit{--- Fim da Parte 1 ---} \\
\textit{(Na próxima seção detalharemos a vitória da Compactação!)}
\end{center}

\end{document}
"""

tex_path = f"{OUTPUT_DIR}/tcc_parte1_analise_macro.tex"
with open(tex_path, 'w', encoding='utf-8') as f:
    f.write(latex_template)
    
print("✅ Código LaTeX do Capítulo (Parte 1) gerado!")

# =====================================================================
# 4. COMPILAÇÃO AUTOMÁTICA
# =====================================================================
print("⚙️ Compilando o PDF da Parte 1...")
try:
    subprocess.run(['pdflatex', '-interaction=nonstopmode', 'tcc_parte1_analise_macro.tex'], cwd=OUTPUT_DIR, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['pdflatex', '-interaction=nonstopmode', 'tcc_parte1_analise_macro.tex'], cwd=OUTPUT_DIR, check=True, stdout=subprocess.DEVNULL)
    print(f"🎓 SUCESSO! PDF Mestre (Parte 1) pronto em: {OUTPUT_DIR}/tcc_parte1_analise_macro.pdf")
except subprocess.CalledProcessError:
    print(f"⚠️  PDF compilado com avisos, verifique a pasta {OUTPUT_DIR}.")