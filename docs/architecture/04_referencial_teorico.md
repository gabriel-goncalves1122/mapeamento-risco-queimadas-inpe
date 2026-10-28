# Referencial Teórico (SIRDA)

Este documento centraliza a fundamentação acadêmica que alicerça as escolhas arquiteturais e algorítmicas da plataforma SIRDA (Sistema de Inteligência e Resposta a Desastres Ambientais). Os trabalhos aqui citados representam o estado da arte e não dizem respeito a manuais ou documentações de ferramentas comerciais, mas sim a paradigmas conceituais que motivam o uso das tecnologias.

---

## 1. Consciência Situacional em Sistemas Dinâmicos
A principal vocação do SIRDA é fornecer inteligência acionável para órgãos de controle ambiental e de infraestrutura. Essa meta é teoricamente embasada pelo modelo seminal de **Mica R. Endsley (1995)**. Mica Endsley é a maior autoridade global no estudo de como humanos e sistemas tomam decisões em ambientes complexos e dinâmicos (como aviação, controle de tráfego e desastres naturais).

Em seu trabalho "*Toward a theory of situation awareness in dynamic systems*", Endsley formaliza a "Consciência Situacional" (*Situation Awareness* - SA) não apenas como o ato de "saber o que está acontecendo", mas como um modelo cognitivo estruturado em três níveis hierárquicos obrigatórios:

1. **Nível 1 - Percepção (*Perception*):** A habilidade de perceber os elementos e dados brutos do ambiente (ex: "Existem 100 focos de calor neste mapa"). O SIRDA implementa este nível por meio da ingestão iterativa dos focos brutos capturados via satélite.
2. **Nível 2 - Compreensão (*Comprehension*):** A capacidade de sintetizar esses elementos para entender o significado real da situação (ex: "Esses focos de calor estão a 2 km de um hospital e dentro de um bioma em período de seca extrema, logo, são de alto risco"). Na plataforma, este nível ganha vida através das árvores espaciais (R-Tree/KDTree) que cruzam os focos térmicos com bancos de dados de infraestruturas (ONS, CNES, FUNAI) para dar significado aos pontos isolados.
3. **Nível 3 - Projeção (*Projection*):** A habilidade de projetar o estado futuro do ambiente com base no Nível 2 para tomar decisões antecipadas (ex: "O fogo vai atingir a rodovia em 2 horas, precisamos desviar a rota"). Este nível é empoderado no projeto pelos painéis interativos que consomem o banco OLAP em sub-segundos, permitindo que gestores projetem e aloquem ajuda antes que o desastre piore.

Essa taxonomia justifica o uso de ferramentas de *Streaming* e painéis interativos de resposta na casa dos milissegundos, provando que a arquitetura serve a um propósito maior de mitigar catástrofes em vez de apenas armazenar dados.

---

## 2. Paradigma DataOps na Gestão de Crises
O termo *DataOps* nasceu no mercado corporativo (inspirado no DevOps) para resolver o caos e a lentidão de projetos de *Big Data*. No entanto, foi o artigo "*DataOps: Towards a Definition*" de **Julian Ereth (2018)**, apresentado no congresso ICEIS, que trouxe a primeira definição acadêmica formal para esse conceito. Ereth define o DataOps como uma prática colaborativa de gestão de dados focada em melhorar a comunicação, integração e automação dos fluxos de dados.

O autor estipula que a metodologia se sustenta em três pilares fundamentais:
1. **Agilidade:** Reduzir o tempo de ciclo (latência) desde a geração do dado até a visualização no painel. O SIRDA atinge isso usando o Apache Druid OLAP processando mais de 3.3 milhões de registros históricos e suportando consultas simultâneas na camada de visualização.
2. **Qualidade:** Automatizar os testes e cruzamentos no pipeline para evitar que dados "sujos" cheguem ao decisor. Em vez de uma extração manual caótica, o sistema possui um fluxo automatizado que cruza biomas e redes elétricas em tempo real.
3. **Orquestração:** Usar ferramentas que garantam que os dados fluam continuamente. A plataforma utiliza orquestração assíncrona por meio do Apache Kafka e *pipelines* via Dagster, evitando os tradicionais e lentos fluxos ETL de blocos monolíticos.

A adoção do DataOps justifica arquitetonicamente por que não foi empregado um simples *script* Python rodando num banco SQL tradicional: a escala massiva de monitoramento ambiental do Brasil requer latência ultrabaixa e controle qualitativo de ponta a ponta.

---

## 3. Identificação Orgânica de Desastres via Agrupamento Espacial (DBSCAN)
Focos de calor brutos oriundos de varreduras via satélite frequentemente sofrem de falsos positivos (*noise*) ou de sobreposições em áreas muito quentes. Tratar cada registro isoladamente como uma "ameaça" prejudica a escalabilidade e o entendimento macroscópico do desastre.

O estado da arte aponta que incêndios não são matrizes perfeitas ou geometrias simétricas; são manchas orgânicas de progressão assimétrica impulsionadas por vento e umidade. Para isso, o algoritmo algorítmico ideal citado extensivamente em literaturas especializadas é o **DBSCAN** (*Density-Based Spatial Clustering of Applications with Noise*). 

Diferente do *K-means*, o DBSCAN agrupa anomalias térmicas baseando-se unicamente na densidade espacial (e temporal, em suas vertentes ST-DBSCAN), permitindo formatar "manchas contínuas de incêndio" de qualquer tamanho e formato poligonal. Ao mesmo tempo, ele exclui eficientemente focos espúrios e ruídos sensoriais como artefatos (pontos isolados de baixa densidade). É essa tese que fundamenta o uso da biblioteca `scikit-learn` pela nossa arquitetura na Camada Gold, convertendo um emaranhado de lat/long disperso em "Eventos de Incêndio" sólidos.

---

## 4. Teoria dos Grafos e Vulnerabilidade em Infraestruturas Críticas
Para avaliar a vulnerabilidade da malha elétrica, a abordagem adotada transcende os cálculos geoespaciais comuns (como a simples distância Euclidiana). A resiliência de linhas de transmissão não depende apenas do quão perto o fogo está de um poste, mas do quão vital aquele poste é para conectar todo o resto da rede nacional. 

Pesquisas contemporâneas sobre segurança de *Power Grids* empregam majoritariamente a **Teoria dos Grafos** para abstrair a rede física (estações e linhas) em nós e arestas matemáticos. Métricas de **Centralidade de Intermediação (*Betweenness Centrality*)** são usadas nesses estudos para descobrir os "elos fracos" estruturais. 
Se uma mancha de incêndio (agrupada pelo DBSCAN) se aproxima de uma subestação com altíssima *Betweenness Centrality*, a probabilidade de um blecaute em cascata (*cascading failure*) é enorme. O projeto implementa essas métricas topológicas (via `networkx`) em caráter exclusivo sobre a camada da ANEEL, embasando as decisões táticas não só pelo perigo físico do fogo, mas pela severidade estrutural da instalação sob ameaça.

---

## Referências Diretas Citadas
- ENDSLEY, Mica R. Toward a theory of situation awareness in dynamic systems. *Human Factors*, v. 37, n. 1, p. 32-64, mar. 1995.
- ERETH, Julian. DataOps: towards a definition. In: INTERNATIONAL CONFERENCE ON WIRTSCHAFTSINFORMATIK, 13., 2018. *Proceedings*. St. Gallen, 2018.
