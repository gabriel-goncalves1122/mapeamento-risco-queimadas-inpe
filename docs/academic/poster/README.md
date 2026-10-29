# Pôster Acadêmico - IX Simpósio de Iniciação Científica (UNIFEI)

Este diretório contém os fontes LaTeX, ilustrações e scripts para geração do pôster científico do projeto:
**"Inteligência Geoespacial em Tempo Real para Mitigação de Desastres Ambientais"**

---

## 📁 Estrutura de Diretórios

```
docs/academic/poster/
├── figures/              # Figuras ativas e banners institucionais UNIFEI
│   ├── fig_pipeline_camadas.png      # Diagrama da arquitetura de ingestão em camadas
│   ├── fig_druid_superset.png        # Arquitetura OLAP (Druid + Superset)
│   ├── fig_qps_saturation.png        # Gráfico de Throughput / QPS por concorrência
│   ├── fig_p95_latency.png           # Gráfico de Latência P95 por concorrência
│   ├── fig_dashboard_superset.png    # Painéis táticos operacionais
│   ├── fig_pressao_indigena.png      # Análise de pressão em Terras Indígenas
│   ├── fig_evolucao_energia.png      # Séries temporais de estresse no SIN
│   ├── image2.png                    # Banner institucional superior oficial UNIFEI
│   └── image3.png                    # Banner institucional inferior oficial UNIFEI
├── modelo/               # Template original de referência UNIFEI
│   ├── a0header.ps
│   ├── a0poster.cls
│   ├── modelo_poster_IX_simposio_IC_Unifei.tex
│   └── modelo_poster_IX_simposio_IC_Unifei.pdf
├── sections/             # Seções modulares do pôster
│   ├── 01_introducao.tex             # Contextualização e Consciência Situacional
│   ├── 02_metodologia.tex            # Pipeline em memória, DBSCAN e Apache Druid
│   ├── 03_resultados.tex             # Benchmarks de carga (QPS, P95) e painéis
│   ├── 04_conclusoes.tex             # Conclusões e síntese científica
│   ├── 05_agradecimentos.tex         # Agradecimentos institucionais (UNIFEI / CNPq)
│   └── 06_referencias.tex            # Referências bibliográficas (ABNT)
├── a0header.ps           # Definição PostScript do formato A0
├── a0poster.cls          # Classe LaTeX para pôster em formato A0
├── compile_poster.ps1    # Script PowerShell para compilação automatizada
├── compile_poster.py     # Script Python para compilação modular
├── main.tex              # Arquivo LaTeX principal (mestre)
├── poster_simposio.pdf   # Pôster final compilado (90 cm x 120 cm)
└── README.md             # Este guia
```

---

## 🛠️ Como Compilar o Pôster

Para gerar o arquivo `poster_simposio.pdf`, execute um dos comandos abaixo a partir da raiz do repositório ou de dentro da pasta `poster`:

### Via PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File docs/academic/poster/compile_poster.ps1
```

### Via Python:
```powershell
uv run python docs/academic/poster/compile_poster.py
```
*(ou `python docs/academic/poster/compile_poster.py` caso o compilador `pdflatex` esteja no seu PATH)*

Os scripts executam duas passagens com `pdflatex` para consolidação do layout e referências cruzadas, limpando automaticamente quaisquer arquivos intermediários (`.aux`, `.log`, `.out`, `.synctex.gz`).
