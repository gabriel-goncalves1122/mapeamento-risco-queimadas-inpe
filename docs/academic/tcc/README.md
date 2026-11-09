# Portal de Documentação: Trabalho de Conclusão de Curso (TCC / TFG)

Este diretório centraliza os modelos oficiais da coordenação de **Engenharia de Computação da UNIFEI**, os planos de trabalho aprovados pela orientadora **Profa. Dra. Barbara Pimenta Caetano** e o plano de evolução arquitetural do **SIRDA 2.0 (Sistema Integrado de Risco e Detecção de Queimadas)**.

---

## 1. Estrutura do Diretório

```text
docs/academic/tcc/
├── README.md                                           # Este portal de documentação
├── exemplos_e_templates/                               # Templates oficiais UNIFEI e referências
│   ├── LEIAM-ME.txt                                    # Regras de formatação (Arial, 10pt/12pt, xelatex)
│   ├── referencias_aprovadas/                          # Planos de trabalho reais aprovados
│   │   └── plano_de_trabalho_PL_revisado.pdf           # Referência real (Orientadora: Profa. Barbara)
│   ├── templates_latex/                                # Cópias descompactadas e compiladas
│   │   ├── ECO_plano_de_trabalho_TCC01/                # Template de Plano de Trabalho (TCC01)
│   │   └── ECO_Revisao_bibliografica_TFG/              # Template de Revisão Bibliográfica (TFG)
│   └── zips_originais/                                 # Arquivos .zip originais intactos
└── propostas_evolucao/                                 # Propostas técnicas de evolução para o TCC
    ├── 00_visao_geral_roadmap_tcc.md                   # Resumo executivo, roadmap e matriz FCIS
    ├── 01_webhooks_alarmes_e_relatorios_ia_sitrep.md   # Frente 1: Webhooks de Alarme e SitRep com IA
    ├── 02_agentes_ia_mcp_e_text_to_druidsql.md         # Frente 2: Agentes de IA, Servidor MCP e RAG
    ├── 03_novas_bases_dados_e_modelagem_fisica.md      # Frente 3: Vento (INMET), Combustível e Apagões
    ├── 04_novas_tecnologias_h3_e_duckdb_spatial.md     # Frente 4: Indexação Hexagonal Uber H3 e DuckDB
    ├── 05_catalogo_apis_e_novos_dados.md               # Catálogo de Dados, Especificação de APIs e Protocolos
    └── 06_evidencias_e_dados_para_revisao_bibliografica.md # Caderno de Evidências Estatísticas para o TCC/TFG
```

---

## 2. Catálogo das Propostas de Evolução para o TCC (`propostas_evolucao/`)

| Documento | Foco Técnico | Principais Tecnologias e Conceitos |
| :--- | :--- | :--- |
| [**00 — Visão Geral e Roadmap do TCC**](propostas_evolucao/00_visao_geral_roadmap_tcc.md) | Transição da IC para o TCC e encaixe nas seções do modelo UNIFEI | Arquitetura Medallion + Inteligência Ativa (*Actionable AI*), estrutura de capítulos do TCC01 e cronograma do TCC02. |
| [**01 — Webhooks de Alarme e Relatórios Executivos com IA (SitRep)**](propostas_evolucao/01_webhooks_alarmes_e_relatorios_ia_sitrep.md) | Monitoramento ativo (*push*) além dos dashboards passivos | Máquina de estados de *cooldown* (anti-spam), plotagem automática de perímetros de queimada, geração de boletins padrão **ICS-209** em PDF/Markdown via LLM e disparo multicanal (**Telegram, Slack/Discord, n8n, CAP XML Defesa Civil**). |
| [**02 — Agentes de IA, Servidor MCP e Text-to-DruidSQL**](propostas_evolucao/02_agentes_ia_mcp_e_text_to_druidsql.md) | Democratização da análise de dados complexos para operadores | **Model Context Protocol (`FastMCP`)**, ferramentas determinísticas sobre o **Apache Druid** e simulação de contingência elétrica $N-1$ no **NetworkX**, *Text-to-DruidSQL* com *Golden Queries* e **RAG Episódico** (`pgvector` / `DuckDB VSS`). |
| [**03 — Novas Bases de Dados e Modelagem Física Direcional**](propostas_evolucao/03_novas_bases_dados_e_modelagem_fisica.md) | Enriquecimento meteorológico, florestal e validação histórica real | Vetores de vento e umidade (**INMET / Open-Meteo**), inflamabilidade e recorrência de 40 anos (**MapBiomas Fogo 30m**), histórico real de **desligamentos forçados por queimadas no SIN (ONS)**, satélite **GOES-19 (10 min)** e **Buffers Elípticos Anisotrópicos**. |
| [**04 — Indexação Hexagonal Uber H3 e DuckDB Spatial**](propostas_evolucao/04_novas_tecnologias_h3_e_duckdb_spatial.md) | Otimização algorítmica geoespacial e arquitetura Lakehouse híbrida | Grade Global Discreta Hexagonal **Uber H3 (`uint64`)** para *hash joins* espaciais em $O(1)$, camada 3D no **Apache Superset (`H3HexagonLayer`)** e motor analítico embarcado **DuckDB (`spatial` + `h3` + `vss`)** sobre `GeoParquet`. |
| [**05 — Catálogo de Dados, Especificação de APIs e Protocolos**](propostas_evolucao/05_catalogo_apis_e_novos_dados.md) | Especificação formal de endpoints, contratos, payloads e esquemas de dados | Protocolos de integração com **ONS AWS S3 Open Data** (`INTERRUPCAO_CARGA`, `LINHA_TRANSMISSAO`), **Open-Meteo API** (FlatBuffers), **INMET PrevMet**, **MapBiomas GEE Coleção 11/5.1** e **NASA FIRMS** (VIIRS NOAA-20/21). |
| [**06 — Evidências Quantitativas e Dados Empíricos para o TCC**](propostas_evolucao/06_evidencias_e_dados_para_revisao_bibliografica.md) | Subsidia factual com números reais, tabelas LaTeX e análises da Bronze | Sazonalidade ONS (8.395 interrupções, 717 GW acumulados), condições extremas ERA5 (vento até 48,2 km/h, umidade $< 12\%$), 89\% de queima em pastagem/Cerrado e trade-off multissensor (VIIRS 375m vs GOES 10 min). |

---

## 3. Como Compilar os Templates LaTeX da UNIFEI

Conforme especificado pela coordenação de Engenharia de Computação no arquivo [`LEIAM-ME.txt`](exemplos_e_templates/LEIAM-ME.txt), os modelos de Plano de Trabalho (TCC01) e Revisão Bibliográfica utilizam a fonte **Arial** do sistema via pacote `fontspec` e devem ser compilados obrigatoriamente com **`xelatex`**:

```powershell
# Compilar o modelo de Plano de Trabalho (TCC01)
cd docs/academic/tcc/exemplos_e_templates/templates_latex/ECO_plano_de_trabalho_TCC01
xelatex main.tex

# Compilar o modelo de Revisão Bibliográfica (TFG)
cd ../ECO_Revisao_bibliografica_TFG
xelatex main.tex
biber main
xelatex main.tex
```
