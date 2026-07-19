# Modelagem Dimensional: Paradigma Snowflake

A normalização do esquema de banco de dados analítico adotado afasta-se de um modelo desnormalizado (*Wide Table* ou *Star Schema* puro) em favor de um **Esquema Floco de Neve (Snowflake)** estrito. O projeto do banco de dados prioriza a mitigação da redundância informacional e a otimização computacional no transporte de dados pela rede (Kafka).

## 1. Restrição Dimensional da Tabela Fato
A Tabela Fato principal (`FATO_FOCOS_INCENDIO`) é projetada para encapsular exclusivamente dados estocásticos e métricas contínuas. Na prática, a validação via classe `Pydantic` no `ProcessadorFocos` opera como uma barreira arquitetural.

A heurística barra veementemente atributos textuais descritivos (como o 'Nome do Prefeito', 'Classe da Rodovia' ou 'Descritivo do Hospital'). Ao reter apenas Identificadores (Foreign Keys - `fk`), o sistema colhe benefícios latentes de compressão e impede gargalos de transmissão I/O nos tópicos de mensageria, dado que as strings não congestionam os pacotes iterativos.

Sua taxonomia engloba três subconjuntos vetoriais:
- **Chave de Partição Temporal**: Parâmetro `__time` mandatório no Druid para fragmentação eficiente de segmentos.
- **Chaves Estrangeiras (Foreign Keys)**: Inteiros ou strings estritas de baixa cardinalidade (e.g., `fk_municipio`, `fk_subestacao`) que apontam para as tabelas-dimensão otimizadas previamente ingeridas.
- **Métricas Quantitativas**: Vetores numéricos e contínuos derivados no instante de *stream* (e.g., físicas do sensor espacial, e índices matemáticos dependentes do distanciamento euclidiano).

## 2. Resolução de Dimensões via Lookups no Apache Druid
A arquitetura baseada no Apache Druid tira proveito do recurso nativo de **Lookup Arrays** ou **Join Nodes**. A Fato transaciona apenas IDs estritos. No ápice da requisição analítica pelo Apache Superset, o nó Router do Druid comanda um *Join* vetorial (Broadcast/Lookup) contra a dimensão latente em memória RAM.

Nessa recomposição estática, atributos textuais extensos e o delineamento cartográfico original (`path_json`) fluem na apresentação interativa ao usuário com uma penalidade computacional marginal.

Esse contrato lógico de separação garante que a altíssima densidade informacional de *streams* permaneça ágil na rede e, sobretudo, tipada e regrada (Contrato Pydantic), conferindo escalabilidade contínua às análises interativas.
