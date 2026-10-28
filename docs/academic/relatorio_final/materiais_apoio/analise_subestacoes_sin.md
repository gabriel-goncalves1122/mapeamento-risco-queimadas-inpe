# Análise Estratégica: Subestações Críticas do SIN (Sistema Interligado Nacional)

O Sistema Interligado Nacional (SIN) brasileiro é caracterizado por distâncias continentais que conectam as grandes fontes de geração (hidrelétricas e renováveis, predominantemente nas regiões Norte, Nordeste e Centro-Oeste) aos principais centros de carga e consumo (regiões Sudeste e Sul).

Na Teoria de Redes Complexas (Complex Networks Theory) aplicada a sistemas elétricos, o **"Betweenness Centrality" (Centralidade de Intermediação)** é uma métrica que identifica nós que atuam como pontes vitais entre diferentes partes da rede. Subestações com o maior índice de Betweenness Centrality são aquelas pelas quais passa o maior número de rotas mais curtas de fluxo de energia. 

As subestações de **Rio Verde Norte**, **Assis** e **Trindade** apresentam os maiores índices de centralidade do SIN. Se uma dessas subestações for removida ou sofrer uma falha, o caminho ótimo do fluxo de energia é interrompido. A energia é então forçada a buscar caminhos alternativos mais longos, sobrecarregando linhas secundárias e provocando atuação de sistemas de proteção (como o ERAC - Esquema Regional de Alívio de Carga) ou o ilhamento/separação de subsistemas, gerando um imenso efeito cascata (blackout).

Abaixo detalhamos a abrangência e a importância de cada uma delas:

---

## 1. Subestação Rio Verde Norte (R.VERDE NORTE)
- **Localização:** Estado de Goiás (GO), Região Centro-Oeste.
- **Tensão de Operação:** Principalmente 500 kV e 230 kV.
- **Área de Abrangência e Polos Alimentados:** Interliga o sudeste de Mato Grosso (através de Ribeirãozinho e Jataí) com o estado de Goiás, e segue em direção aos grandes complexos no Sudeste (região de Ilha Solteira e Marimbondo). Mato Grosso e Goiás são vitais polos agroindustriais (agronegócio) que demandam e também exportam energia regionalmente.
- **Importância Estratégica (Hub):** Funciona como um portal obrigatório. É um dos principais corredores para o escoamento do gigantesco bloco de energia oriundo das usinas do Norte (como as das bacias do Tapajós/Teles Pires e Xingu - Belo Monte) em direção ao Sudeste.
- **O Efeito Cascata:** Possui altíssimo *Betweenness Centrality* por ser o afunilamento (gargalo) do fluxo Norte-Sudeste via Centro-Oeste. Uma queda na SE Rio Verde Norte faz com que toda a carga em trânsito tente se redistribuir por redes de menor capacidade (230 kV) ou linhas distantes, levando imediatamente ao colapso térmico de linhas paralelas e, possivelmente, à divisão do sistema na região central do país.

---

## 2. Subestação Assis (ASSIS)
- **Localização:** Assis, Estado de São Paulo (SP), Região Sudeste.
- **Tensão de Operação:** 500 kV e 440 kV (rede da ISA CTEEP / TAESA).
- **Área de Abrangência e Polos Alimentados:** Localiza-se no coração do anel de transmissão do interior paulista. Atende os complexos agrícolas (cana-de-açúcar/etanol) do oeste paulista e é um ponto de entrada para alimentar grandes polos industriais do Sudeste (regiões de Bauru, Campinas e a Grande São Paulo).
- **Importância Estratégica (Hub):** Assis é o principal coletor da energia proveniente da bacia do Rio Paraná (Itaipu, Rosana, Taquaruçu) e da Região Sul. Ela direciona essa energia massiva para a rede estrutural do estado mais industrializado do país (São Paulo).
- **O Efeito Cascata:** Seu índice de *Betweenness Centrality* é astronômico porque ela é literalmente o caminho mais curto e robusto entre o maior bloco de geração do Sul/Itaipu e o maior centro de consumo (São Paulo). A sua falha divide o anel de 440/500 kV paulista. A energia de Itaipu teria que desviar por rotas no Paraná ou através de linhas no norte do estado que já operam próximo ao limite (ex: Araraquara), garantindo o acionamento de proteções sistêmicas e desligamento em massa da carga industrial.

---

## 3. Subestação Trindade (TRINDADE)
- **Localização:** Trindade (Região Metropolitana de Goiânia), Estado de Goiás (GO), Região Centro-Oeste.
- **Tensão de Operação:** 500 kV e 230 kV.
- **Área de Abrangência e Polos Alimentados:** Alimenta diretamente o polo demográfico e industrial da Grande Goiânia. Contudo, seu papel macro abrange todo o subsistema Sul/Sudeste e Centro-Oeste, interligando linhas que vêm do Norte (como Serra da Mesa, Colinas) e direcionando-as para Rio Verde, Xavantes e Sudeste.
- **Importância Estratégica (Hub):** A SE Trindade é um dos pilares históricos da chamada "Interligação Norte-Sul". Funciona como a "cintura da ampulheta" do SIN: liga a metade superior do país (subsistemas Norte e Nordeste) à metade inferior (subsistemas Sul e Sudeste).
- **O Efeito Cascata:** A perda de Trindade corta uma das artérias mais críticas do escoamento inter-regional do Brasil. Como quase todo o intercâmbio Norte-Sul (seja importando energia das hidrelétricas do Norte no período chuvoso, ou enviando energia do Sudeste no período seco) passa ou depende do corredor onde Trindade está inserida, sua falha isolaria eletricalmente enormes porções do Brasil. Isso geraria subfrequência brusca no Sudeste/Sul (apagão por falta de geração) e sobrefrequência no Norte (desligamento de usinas por excesso de geração).

---

**Referências Consultadas**

EPE. **Plano Decenal de Expansão de Energia 2032**. Empresa de Pesquisa Energética, Ministério de Minas e Energia, Brasília, 2022. Disponível em: <https://www.epe.gov.br/pt/publicacoes-dados-sinteticos/publicacoes/plano-decenal-de-expansao-de-energia-pde>. Acesso em: 24 set. 2026.

ONS. **Mapa do Sistema Interligado Nacional (Horizonte 2026)**. Operador Nacional do Sistema Elétrico, Rio de Janeiro, 2026. Disponível em: <http://www.ons.org.br/paginas/sobre-o-sin/mapas>. Acesso em: 24 set. 2026.

ONS. **Procedimentos de Rede: Operação e Critérios de Confiabilidade do SIN**. Operador Nacional do Sistema Elétrico, Rio de Janeiro, 2026. Disponível em: <http://www.ons.org.br/paginas/conhecimento/procedimentos-de-rede>. Acesso em: 24 set. 2026.
