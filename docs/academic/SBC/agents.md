# Governança de IA: Produção Científica e Relatórios (LaTeX)

Este arquivo define as "Leis de Ouro" arquiteturais que devem ser obrigatoriamente seguidas por qualquer Agente de Inteligência Artificial operando dentro do diretório `docs/academic_paper/`.

## 0. Linguagem e Formatação de Texto
- **Linguagem Científica Direta**: Utilize uma linguagem acadêmica simples, direta e objetiva. Evite frases excessivamente rebuscadas e "voltas" que façam o texto perder o sentido.
- **Formatação de Texto**: É ESTRITAMENTE PROIBIDO o uso da sintaxe de negrito e itálico do Markdown (ex: `**texto**` ou `*texto*`) dentro dos arquivos `.tex`. O compilador não os reconhece. Utilize os comandos oficias do LaTeX `\textbf{}` e `\textit{}`.

## 1. Diretrizes de Compilação
- O comando `pdflatex` no TeX Live recente pode retornar código de saída `1` devido a avisos inofensivos (como `\normalsfcodes`).
- **NUNCA** utilize encadeamentos com `&&` (ex: `pdflatex file.tex && bibtex file`). Se o primeiro falhar com aviso, o `bibtex` não rodará.
- **Rode os comandos sequencialmente com `;` ou em execuções separadas**:
  `pdflatex -interaction=nonstopmode arquivo.tex ; bibtex arquivo ; pdflatex -interaction=nonstopmode arquivo.tex ; pdflatex -interaction=nonstopmode arquivo.tex`

## 2. Padronização de Imagens e Diagramas
- Imagens inseridas no LaTeX devem seguir uma **escala e tamanho unificados**.
- Todas as tags `\includegraphics` devem utilizar tamanho que preencha bem sem quebrar as páginas: a regra padrão é `[width=0.9\textwidth, height=0.35\textheight, keepaspectratio]`.
- **Canal Alfa**: Para evitar falhas de renderização (fundo amarelo), todas as imagens transparentes devem ter seu canal Alpha removido e substituído por um fundo branco utilizando ImageMagick (ex: `convert file.png -background white -alpha remove -alpha off output.png`).
- O formato `[htpb]` ou `[H]` deve ser usado para flutuação.

## 3. Estrutura de Documentos
- Para relatórios estendidos (que não sofrem limite restrito de 7 páginas, diferentemente de submissões clássicas de artigos acadêmicos), deve-se adotar o uso de `\newpage` ou quebras lógicas para melhor conforto visual na leitura, isolando figuras muito grandes ou seções complexas para não sobrecarregar a diagramação.

## 4. Referências
- O arquivo `.bib` deve sempre conter a entrada correspondente para todo `\cite{}` utilizado no `.tex`.
- Se as referências aparecerem como `[?]`, reexecute o `bibtex` isoladamente para debugar possíveis erros de sintaxe no arquivo BibTeX.

## 5. Comentários e Anotações
- Ao mexer em scripts, trechos LaTeX comentados ou notas auxiliares, siga a regra global de comentários em `src/agents.md`.
- Comentários devem explicar decisões metodológicas, origem de dados, limitações de benchmark e escolhas de formatação acadêmica.
- Não mantenha comentários obsoletos que contradigam o texto final do artigo.
