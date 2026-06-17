import os

latex_content = r"""\documentclass[12pt]{article}

% Correção para erro \normalsfcodes no Overleaf / TeX Live 2025
\makeatletter
\DeclareRobustCommand{\normalsfcodes}{%
  \sfcode`\.=3000
  \sfcode`\?=3000
  \sfcode`\!=3000
  \sfcode`\:=2000
  \sfcode`\;=1500
  \sfcode`\,=1250
}
\makeatother

\usepackage{sbc-template}
\usepackage{graphicx,url}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[brazil]{babel}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage[hidelinks]{hyperref}

\sloppy

\title{Uma Arquitetura DataOps Orientada a Eventos para Processamento de Dados Geoespaciais, Modelagem Topológica e Clusterização de Incêndios}

\author{Gabriel Gonçalves Sampaio\inst{1}, Barbara Pimenta Caetano\inst{1}}

\address{Instituto de Engenharia de Sistemas e Tecnologia da Informação (IESTI) \\
  Universidade Federal de Itajubá (UNIFEI)\\
  Avenida BPS, 1303 -- 37500-903 -- Itajubá -- MG -- Brasil
  \email{gabrielsampaio059@gmail.com, bpimentacaetano@unifei.edu.br}
}

\begin{document}

\maketitle

\begin{abstract}
  The growing demand for real-time geospatial data processing poses challenges related to the ingestion, storage, and continuous analysis of large volumes of information. This paper presents an event-driven DataOps architecture designed to continuously integrate the stages of collection, spatial clustering, and topological modeling of geographic data. The architecture comprises a messaging system for data stream ingestion, an in-memory spatial indexing structure, and a columnar database for analytical storage. For validation, the platform was applied to wildfire hotspot monitoring, integrating Spatio-Temporal Density-Based Spatial Clustering (ST-DBSCAN) to track dynamic fire events, and Network Science (Betweenness Centrality) to evaluate the cascade failure risk in the Brazilian National Interconnected System (SIN). The results demonstrate the capability to group over 500,000 raw hotspots into unified fire events and identify critical power substations with high processing stability, indicating that the proposed architecture is suitable for advanced continuous geospatial intelligence.
\end{abstract}

\begin{resumo}
  A crescente demanda por processamento de dados geoespaciais em tempo real impõe desafios na ingestão, armazenamento e modelagem analítica contínua. Este trabalho apresenta uma arquitetura DataOps orientada a eventos, projetada para integrar a coleta, processamento de fluxos espaciais e orquestração de algoritmos preditivos. A arquitetura engloba sistemas de mensageria, banco de dados colunar e pipelines orquestrados (Dagster). Para validação, a plataforma foi aplicada ao monitoramento de incêndios, integrando a clusterização baseada em densidade espaço-temporal (ST-DBSCAN) para transmutar focos estáticos em eventos dinâmicos poligonais, além do emprego de Ciência de Redes para calcular o risco de falha em cascata no Sistema Interligado Nacional (SIN) por meio da Centralidade de Intermediação. Os resultados demonstram a conversão de meio milhão de focos brutos em eventos rastreáveis e o mapeamento de vulnerabilidades em subestações elétricas, atestando a robustez da arquitetura para inteligência geoespacial contínua.
\end{resumo}

\section{Introdução}

O mercado atual exige que informações geoespaciais sejam coletadas, processadas e entregues com latências mínimas. Em áreas críticas como meio ambiente e segurança energética, o valor do dado depende da transição de registros estáticos para modelos relacionais preditivos. Uma coordenada térmica isolada informa apenas uma anomalia física pontual, não elucidando a real propagação de um incêndio florestal ou o impacto imediato sobre a rede elétrica.

Para que um evento geofísico tenha utilidade tática, faz-se necessária a adoção de paradigmas avançados de Ciência de Dados. O Programa Queimadas do INPE \cite{inpe_queimadas} detecta focos de calor via satélite. Quando estes vetores térmicos são submetidos a algoritmos de clusterização de densidade espaço-temporal (ST-DBSCAN), é possível rastrear o ciclo de vida contínuo de um grande incêndio. Adicionalmente, através do cruzamento destes eventos com a infraestrutura do Operador Nacional do Sistema (ONS) modelada via teoria de grafos, viabiliza-se o cálculo do risco de colapso energético em cascata.

Este artigo apresenta uma arquitetura DataOps orientada a eventos que integra o Apache Kafka para mensageria contínua \cite{apache_kafka}, o Apache Druid para persistência OLAP analítica \cite{apache_druid}, e o Dagster para a orquestração formal de pipelines. Modelos de Ciência de Redes e algoritmos de clusterização espacial foram inseridos no núcleo da arquitetura para garantir o enriquecimento profundo de dados geoespaciais voltados a respostas governamentais estratégicas.

\section{Revisão Bibliográfica}

Arquiteturas modernas de Big Data adotam o paradigma DataOps para garantir rastreabilidade, automação e orquestração determinística no ciclo de vida dos dados \cite{ereth2018dataops}. Em cenários geoespaciais, a transformação de eventos observacionais brutos em dimensões enriquecidas requer a aplicação do modelo dimensional Snowflake, minimizando a entropia e o overhead na transmissão de mensagens \cite{kimball2013}.

Do ponto de vista preditivo, a análise de eventos dinâmicos como incêndios exige extrapolar a estatística clássica. O algoritmo ST-DBSCAN estende a clusterização baseada em densidade ao incorporar penalidades no domínio temporal, viabilizando o agrupamento de pontos contíguos em espaço e tempo \cite{birant2006stdbscan}. Simultaneamente, a estabilidade de infraestruturas conectadas é amplamente estudada pela Ciência de Redes. A Centralidade de Intermediação (\textit{Betweenness Centrality}) atua como um previsor confiável de gargalos em grafos complexos, como malhas de transmissão de alta tensão \cite{freeman1977set}. 

\section{Arquitetura DataOps e Topologia de Modelagem}

A arquitetura transcende dutos ETL clássicos ao separar extração estática, clusterização científica, fluxo contínuo e orquestração. A governança do projeto foi designada ao Dagster, enquadrando todos os scripts matemáticos como \textit{Software-Defined Assets} e garantindo um grafo acíclico direcionado de dependências infalível.

No eixo temporal contínuo (Streaming), cada foco de incêndio interceptado sofre cálculos de proximidade e derivação de índices de pressão ambiental na borda produtora. Estes *payloads* hiper-reduzidos são ingeridos pelo Apache Druid via barramentos Kafka, delegando ao motor de visualização (Apache Superset) a resolução dimensional vetorial via \textit{Lookups}.

\section{Modelagem Analítica Avançada: Grafos e Clusterização}

O processamento analítico profundo foi deslocado para as instâncias de pré-persistência e \textit{batch orquestrado}, garantindo que operações geofísicas rigorosas não onerassem o banco OLAP durante execuções exploratórias.

\subsection{Ciência de Redes no SIN}
Utilizando índices espaciais em memória (K-Dimensional Trees), intersecções físicas entre Linhas de Transmissão e Subestações foram modeladas em uma Matriz de Adjacência e convertidas em um Grafo Complexo via biblioteca \textit{NetworkX}. O sistema calculou iterativamente a \textit{Betweenness Centrality} de todo o Sistema Interligado Nacional (SIN), conferindo um escore escalar a cada subestação, atestando objetivamente a gravidade de um impacto em caso de colapso por queimadas na área de servidão.

\subsection{Dinâmica de Fogo com ST-DBSCAN}
Focos satelitais brutos foram submetidos a normalização escalar, fundindo as grandezas espaciais e temporais (raio de 2km e janela de 2 dias). Através do ST-DBSCAN acoplado a rotinas da biblioteca GeoPandas (geração de envoltórias convexas - \textit{Convex Hull}), milhares de anomalias térmicas isoladas foram amalgamadas em "Eventos Dinâmicos de Incêndio", polígonos representativos da evolução real da área devastada ao longo dos dias.

\section{Resultados e Discussão}

A execução da arquitetura no domínio orquestrado evidenciou latência reduzida no stream e eficácia estrutural ímpar na ciência aplicada. 
A partir de um montante de 500.000 focos de calor brutos do INPE, o algoritmo ST-DBSCAN filtrou e converteu a amostragem em 29.518 Eventos Dinâmicos de Incêndio únicos. Alguns polígonos acompanhados perduraram por até 41 dias contínuos em combustão, demonstrando um potencial de análise governamental substancial.

Na vertente do setor elétrico, a topologia de grafos apontou com precisão cirúrgica os gargalos do país, atribuindo as maiores escores de risco em cascata a nós vitais no escoamento nacional (ex: Subestação Rio Verde Norte com escore 100.00).

O monitoramento do fluxo via contêineres confirmou que a abordagem DataOps, operando sob *hard-capping* restrito de CPU/RAM em ambiente host, mantém o Apache Kafka e o Druid estáveis mesmo em picos de detecção estival na Amazônia e Cerrado. 

\section{Conclusão}

A arquitetura delineada não só soluciona o paradigma logístico de Big Data espacial, mas o eleva ao patamar de Ciência Analítica Preditiva. 
O acoplamento do ST-DBSCAN para interpretação geométrica do fogo e do cálculo vetorial de Grafos para a matriz energética comprova que plataformas DataOps orientadas a eventos não se limitam à transferência de dados, sendo motores primordiais para Inteligência Governamental. A adoção de ferramentas como Dagster e Druid certifica a escalabilidade, prontidão e excelência técnica do modelo em contextos de restrição computacional e volumetria explosiva.

\section*{Declaração de Uso de Ferramentas de IA Generativa}

Durante a elaboração deste trabalho, Inteligências Artificiais Generativas foram utilizadas como apoio à organização textual, refinamento arquitetural de código, implementação sintática em Python (NetworkX, scikit-learn) e documentação DataOps avançada. O conteúdo científico, a tomada de decisão algorítmica e a responsabilidade metodológica permanecem estritamente sob os autores.
\clearpage


\bibliographystyle{plain}
\bibliography{referencias}

\end{document}
"""

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artigo_atualizado.tex'), 'w', encoding='utf-8') as f:
    f.write(latex_content)

print("✅ O arquivo LaTeX 'artigo_atualizado.tex' foi gerado com sucesso!")
