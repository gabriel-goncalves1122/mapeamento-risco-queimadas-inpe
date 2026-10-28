TEMPLATE LaTeX - IX SIMPÓSIO DE INICIAÇÃO CIENTÍFICA DA UNIFEI
================================================================

Arquivo principal:
  template_resumo_expandido_ix_simposio_ic.tex

Figuras:
  figuras/assinatura_unifei.png
      Assinatura institucional da UNIFEI fornecida junto ao pedido.
  figuras/assinatura_unifei_original.png
      Cópia do arquivo original fornecido.
  figuras/LOGO_PRPI.svg
      Arquivo vetorial local de contingência para a PRPI.
  figuras/LOGO_PRPI.pdf
      Conversão para PDF usada pelo pdfLaTeX.
  figuras/figura_exemplo.png
      Imagem de exemplo extraída do template DOCX original.

COMPILAÇÃO
-----------
Recomendação: pdfLaTeX, por ser amplamente disponível e exigir poucas
ferramentas externas.

No terminal, dentro desta pasta:

  pdflatex template_resumo_expandido_ix_simposio_ic.tex
  pdflatex template_resumo_expandido_ix_simposio_ic.tex

A segunda execução atualiza referências de figuras, tabelas e equações.

FONTES
------
O template usa newtxtext/newtxmath, que reproduzem uma família tipográfica
muito próxima da Times e funcionam diretamente com pdfLaTeX. Isso evita a
dependência de uma instalação local da fonte proprietária Times New Roman e
melhora a portabilidade entre Windows, Linux, Overleaf e instalações TeX Live.

ESTRUTURA E REGRAS INCORPORADAS
-------------------------------
- A4, fonte 12 pt e texto justificado;
- margens laterais de 3 cm;
- espaçamento 1,5 no corpo e simples no resumo;
- título em caixa alta, negrito, centralizado e espaçamento simples;
- resumo com até 100 palavras;
- 3 a 5 palavras-chave;
- corpo do trabalho com limite de 1.000 palavras, excluídas as referências;
- citações longas com recuo de 4 cm, fonte 11 e espaçamento simples;
- instruções e exemplos para figuras, tabelas e equações;
- legendas de figuras e tabelas em 10 pt;
- referências conforme orientação do modelo para ABNT NBR 6023;
- agradecimentos com indicação de UNIFEI e órgão financiador, quando aplicável.
