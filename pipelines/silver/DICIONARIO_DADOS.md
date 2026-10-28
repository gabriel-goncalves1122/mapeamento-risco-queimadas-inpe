# Dicionário de Dados - Camada Silver (Dimensões Conformadas)

A Camada Silver (Prata) é responsável por receber os dados geográficos e tabulares brutos (Bronze), resolver inconsistências espaciais, tratar nulos, criar geometrias cruzadas e finalmente gerar as **Tabelas de Dimensão** (.csv).

Estes CSVs serão carregados nos nós locais do Apache Druid via mecanismos de *Lookup* para realizar *JOINs* em tempo de execução sem penalizar a performance com queries distribuídas.

## Princípios de Design (Silver)
1. **Nulos Resolvidos:** Nenhum valor nulo (NaN) de domínio sobrevive. Eles são preenchidos com "N/A" ou "Desconhecido".
2. **Geometria Padronizada:** Shapes complexos ou com falhas são traduzidos ou descartados, extraindo-se centroides padronizados ou formatando Multipolígonos.
3. **Chaves (FKs):** As chaves são sempre numéricas ou códigos governamentais absolutos (ex: Código IBGE) para garantir indexação perfeita nas tabelas Fato.

---

## 1. Dimensão Municípios (`dim_municipios.csv`)
Oriundo do IBGE (Malha Territorial). Cruzamento vital para mapas coropléticos.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_municipio` | Int | Código IBGE absoluto (7 dígitos) do município. **(Primary Key)** |
| `nome_municipio` | String | Nome por extenso, normalizado (sem acentos/caps agressivo). |
| `estado` | String | UF / Estado da federação em sigla (Ex: MG). |
| `regiao` | String | Região geográfica (Norte, Sul, Sudeste...). |
| `area_km2` | Float | Área territorial do município calculada pela projeção da geometria. |
| `geometry` | WKT | Polígono do limite geográfico em Well-Known Text (apenas para exibição no Superset). |

---

## 2. Dimensão Linhas de Transmissão (`dim_linhas_transmissao.csv`)
Oriundo da ANEEL/ONS. Base do modelo de Grafos.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_linha` | Int | Identificador serial interno. **(Primary Key)** |
| `nome_linha` | String | Nome descritivo da linha e tensão. |
| `tensao_kv` | Float | Tensão elétrica (ex: 500.0, 230.0). Limpo de alfanuméricos. |
| `comprimento_km` | Float | Extensão geográfica real da linha de transmissão. |

---

## 3. Dimensão Subestações ONS (`dim_subestacoes.csv`)
Conectores da malha elétrica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_subestacao` | Int | Serial interno gerado no ETL. **(Primary Key)** |
| `nome` | String | Nome da subestação ONS. |
| `tipo` | String | Classificação (ex: Elevadora, Abaixadora). |
| `lat`, `lon` | Float | Coordenadas do ponto físico. |

---

## 4. Dimensão Terras Indígenas (`dim_terras_indigenas.csv`)
Oriundo da FUNAI.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_terra` | Int | Código da reserva/TI. **(Primary Key)** |
| `nome_terra` | String | Denominação oficial da aldeia/terra. |
| `fase` | String | Fase do processo de demarcação (Homologada, Declarada, etc). |

---

## 5. Dimensão Hospitais (`dim_hospitais.csv`)
Oriundo do DataSUS (CNES). Usado para calcular evacuação.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_cnes` | Int | Código absoluto (7 dígitos numéricos) do Hospital no sistema CNES. **(Primary Key)** |
| `nome_fantasia` | String | Nome fantasia normalizado. |
| `tipo_gestao` | String | Municipal, Estadual ou Dupla. |
| `lat`, `lon` | Float | Ponto central de atendimento. |
