# Referências Acadêmicas Fundamentais do Projeto

Este documento explica as ideias e metodologias dos dois artigos científicos seminais que utilizamos para fundamentar o **Referencial Teórico** do resumo expandido do CCO-DataOps.

---

## 1. Consciência Situacional (Situational Awareness)
**Artigo:** *Toward a Theory of Situation Awareness in Dynamic Systems*
**Autora:** Mica R. Endsley (1995)

Mica Endsley é a maior autoridade global no estudo de como humanos e sistemas tomam decisões em ambientes complexos e dinâmicos (como aviação, controle de tráfego e desastres naturais). 

### Ideia Central e Metodologia
Neste artigo de 1995, Endsley formaliza a "Consciência Situacional" (SA - *Situation Awareness*) não apenas como o ato de "saber o que está acontecendo", mas como um modelo cognitivo estruturado em três níveis hierárquicos obrigatórios:

1. **Nível 1 - Percepção (Perception):** A habilidade de perceber os elementos e dados brutos do ambiente (ex: "Existem 100 focos de calor neste mapa").
2. **Nível 2 - Compreensão (Comprehension):** A capacidade de sintetizar esses elementos para entender o significado real da situação (ex: "Esses focos de calor estão a 2 km de um hospital e dentro de um bioma em período de seca extrema, logo, são de alto risco").
3. **Nível 3 - Projeção (Projection):** A habilidade de projetar o estado futuro do ambiente com base no Nível 2 para tomar decisões antecipadas (ex: "O fogo vai atingir a rodovia em 2 horas, precisamos desviar a rota").

### Conexão com o seu Trabalho
O seu projeto CCO-DataOps implementa exatamente essa teoria na prática da Defesa Civil:
- **Nível 1** é feito pela ingestão iterativa dos focos brutos de satélite.
- **Nível 2** é feito pelas árvores espaciais (R-Tree/KDTree) que cruzam os focos com infraestruturas (ONS, CNES, terras indígenas) para dar significado aos pontos isolados.
- **Nível 3** é empoderado pelos painéis interativos consumindo o banco OLAP em sub-segundos, permitindo que gestores projetem e aloquem ajuda antes que o desastre piore.

---

## 2. DataOps (Data Operations)
**Artigo:** *DataOps: Towards a Definition*
**Autor:** Julian Ereth (2018)

O termo *DataOps* nasceu no mercado (inspirado no DevOps) para resolver o caos e a lentidão dos projetos de Big Data. No entanto, foi o artigo de Julian Ereth no congresso ICEIS (2018) que trouxe a primeira definição acadêmica formal para esse conceito.

### Ideia Central e Metodologia
A metodologia do artigo consistiu em analisar a literatura emergente da indústria e sistematizá-la cientificamente. Ereth define *DataOps* como uma "prática colaborativa de gestão de dados focada em melhorar a comunicação, integração e automação dos fluxos de dados entre gestores e engenheiros". 

O autor estipula que a metodologia DataOps se sustenta em três pilares metodológicos:
1. **Agilidade:** Reduzir o tempo de ciclo (latência) desde a geração do dado até a visualização no painel.
2. **Qualidade:** Automatizar os testes e cruzamentos no pipeline para evitar que dados "sujos" cheguem ao decisor.
3. **Orquestração:** Usar ferramentas que garantam que os dados fluam continuamente e não em blocos monolíticos isolados.

### Conexão com o seu Trabalho
No seu resumo expandido, nós usamos as ideias de Ereth para justificar por que você não poderia simplesmente usar um script Python rodando em um banco SQL tradicional para salvar desastres ambientais. 
Você adota **DataOps** na veia:
- Orquestra os dados de forma assíncrona (Apache Kafka).
- Garante agilidade extrema e baixa latência (Apache Druid OLAP processando 3.3 milhões de registros e segurando 2 QPS).
- Substitui a extração manual caótica por um fluxo automatizado que cruza biomas e redes elétricas com qualidade antes do gestor ver o mapa.

---
*Estes dois artigos dão um peso acadêmico gigantesco ao seu trabalho de Ciência da Computação, provando que sua arquitetura de engenharia de dados (Ereth) serve ao nobre propósito de apoiar o combate a desastres (Endsley).*
