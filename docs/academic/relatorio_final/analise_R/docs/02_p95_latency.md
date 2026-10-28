# Análise de Explosão de Latência (P95)

## A Ideia do Gráfico
O gráfico de área preenchida **Latência P95** foca na experiência pura e nua do usuário final. O Percentil 95 (P95) elimina 5% das anomalias extremas (cortando os grandes *outliers*) e responde de forma robusta à pergunta: *Sob estresse intenso, qual é o tempo máximo que 95% dos nossos operadores ficarão esperando a tela carregar?*

## Fontes de Dados Utilizadas
- **Arquivo:** `capacity_enriched.csv`
- **Métricas Chave:** `concurrency_factor` (eixo X) e `p95_latency_ms` (eixo Y).
- **Contexto:** Essa métrica isola o tempo transcorrido no relógio físico (Wall-Clock Time) desde a emissão da requisição JSON pelo Superset até o empacotamento completo do Apache Druid Broker de volta ao cliente HTTP.

## Análise dos Resultados
A área gráfica corrobora a asfixia exposta no Throughput (QPS), mas adiciona uma camada de urgência temporal:
1. **O Colapso do Baseline:** No ambiente pobre de CPU, com apenas 4 operadores abrindo o Superset, o P95 explode ultrapassando a marca dos 20.000 ms (20 segundos). Isso é tecnicamente inviável para uso interativo. O operador acreditaria que a ferramenta travou.
2. **A Sustentação Analítica:** O cenário *Query Heavy* revela-se a verdadeira âncora do sistema. Até a marca de 8 conexões (o dobro do limite anterior), ele mantém o P95 elegantemente exprimido próximo de zero. Mesmo em cenários absurdos de 16 conexões puras demandando joins espaciais, ele contém a "explosão" abaixo dos limites catastróficos.

## Mitigação de Outliers (Anomalias de Desempenho)
**Fenômeno:** Picos catastróficos eventuais onde até o P95 supera a barreira dos 10.000ms.
**Causa Raiz:** *Context Switching* provocado por cruzamentos espaciais dinâmicos intensos. Cruzar malhas poligonais indígenas (FUNAI) com milhares de focos (INPE) sob estresse força uma disputa feroz pela mesma L1/L2 Cache do processador.
**Como Melhorar:** Deslocar esse esforço puramente matemático da camada de consumo (Druid) para a camada de ingestão. Utilizando um framework ETL (Apache Spark) para processar o join geométrico no momento em que o dado entra, a tabela já chegaria totalmente plana (Flat), removendo o uso de JOIN dinâmico no painel e estabilizando a latência.

## Conclusões (Impacto no SIRDA)
Para painéis executivos de pronta resposta a desastres, latências acima de 3 segundos quebram o engajamento visual do operador. O gráfico atesta que para o SIRDA garantir UX fluida, o *Apache Druid* necessita de provisionamento na faixa do *Query Heavy*. Esse ambiente não elimina o fenômeno da latência sob estresse (como fica claro na rampa final do gráfico roxo), mas joga o gargalo para um patamar de concorrência massivo, protegendo a equipe central.
