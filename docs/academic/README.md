# Produção Científica e Publicações Acadêmicas (`docs/academic/`)

> **Trilha Geral de Documentação**: [Portal Geral (`docs/README.md`)](../README.md) | [Capítulo 01: Introdução e Fundamentação Teórica](../architecture/01_introducao_e_proposta.md) | [Avaliação de Desempenho (`docs/performance/`)](../performance/README.md)

Este diretório reúne os relatórios técnicos, artigos científicos, resumos expandidos, pôster acadêmico e a documentação de Trabalho de Conclusão de Curso (TCC/TFG) resultantes da pesquisa desenvolvida na **Universidade Federal de Itajubá (UNIFEI)**.

---

## 1. Catálogo de Documentos Acadêmicos

| Documento / Diretório | Formato | Descrição Técnica |
| :--- | :--- | :--- |
| [**Trabalho de Conclusão de Curso — TCC / TFG (`tcc/README.md`)**](tcc/README.md) | Templates LaTeX (`xelatex`) + Markdowns Arquiteturais | Portal do TCC em Engenharia de Computação (UNIFEI): propostas de evolução com IA Agêntica, Webhooks/SitRep, modelagem anisotrópica e H3 (`tcc/propostas_evolucao/`), além dos templates oficiais compilados (`TCC01` e `TFG`). |
| [**Relatório Final de Iniciação Científica (`relatorio_final/main.tex`)**](relatorio_final/main.tex) | Monografia LaTeX / [PDF Compilado](relatorio_3_conclusao_geral.pdf) | Documento completo da pesquisa contendo referencial teórico, especificação da arquitetura Medallion/Snowflake, formulação matemática dos índices e análise estatística dos experimentos de capacidade. |
| [**Artigo Científico Padrão SBC (`SBC/artigo_final.tex`)**](SBC/artigo_final.tex) | Artigo LaTeX (Template SBC) | Artigo científico sintetizando a arquitetura de streaming e OLAP e os resultados de desempenho sob concorrência no Apache Druid. |
| [**Pôster Científico A0 (`poster/README.md`)**](poster/README.md) | Pôster TikZ/LaTeX A0 / [PDF Compilado](poster/poster_simposio.pdf) | Painel técnico em formato A0 ($90\text{ cm} \times 120\text{ cm}$) elaborado para apresentação no Simpósio de Iniciação Científica da UNIFEI. |
| [**Resumo Expandido do Simpósio (`simposio/resumo_expandido.tex`)**](simposio/resumo_expandido.tex) | Resumo LaTeX / [PDF Compilado](simposio/resumo_expandido.pdf) | Síntese executiva da metodologia, arquitetura e conclusões experimentais. |
| [**Relatório Técnico Parcial (`relatorio_tecnico/main.tex`)**](relatorio_tecnico/main.tex) | Relatório LaTeX | Registro intermediário das primeiras fases de implementação do projeto. |

---

## 2. Procedimentos de Compilação LaTeX via `uv`

```bash
# Compilar Relatório Final de Iniciação Científica
uv run python docs/academic/relatorio_final/compile_tex.py

# Compilar Pôster A0 do Simpósio
uv run python docs/academic/poster/compile_poster.py

# Compilar Resumo Expandido
uv run python docs/academic/simposio/compile_tex.py
```
