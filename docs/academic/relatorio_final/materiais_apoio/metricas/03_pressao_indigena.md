# Índice de Pressão sobre Terras Indígenas

## 1. Conceito

O **Índice de Pressão sobre Terras Indígenas** quantifica a ameaça térmica que os incêndios florestais exercem sobre os territórios demarcados pela FUNAI. O sistema cruza, em tempo real, as coordenadas dos focos e eventos de incêndio com os polígonos (GeoJSON) das mais de 650 Terras Indígenas cadastradas. O índice gerado combina a intensidade do fogo, medida pelo *Fire Radiative Power* (FRP), com a proximidade geográfica em relação aos limites do território.

## 2. Classificação da Dimensão Terra Indígena

As Terras Indígenas são categorizadas no momento da ingestão (Camada Silver) por área, estágio de regularização e prioridade de monitoramento para a FUNAI. A lógica de classificação encontra-se em [etl_dim_terras_indigenas.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/etl_dimensions/etl_dim_terras_indigenas.py).

### 2.1. Classificação por Área

| Área (hectares) | Classe |
|---|---|
| $\ge 1.000.000$ | `MUITO_GRANDE` |
| $\ge 100.000$ | `GRANDE` |
| $\ge 10.000$ | `MEDIA` |
| $> 0$ | `PEQUENA` |
| $0$ ou nulo | `NAO_INFORMADA` |

### 2.2. Classificação por Estágio de Regularização

| Estágio | Classe |
|---|---|
| Regularizada | `REGULARIZADA` |
| Declarada | `DECLARADA` |
| Delimitada | `DELIMITADA` |
| Em Estudo/Identificada | `EM_ESTUDO_IDENTIFICACAO` |

### 2.3. Classificação de Prioridade FUNAI

| Critério | Classe |
|---|---|
| Faixa de fronteira E $\ge 100.000$ ha | `ALTA_PRIORIDADE` |
| Não regularizada | `ALTA_PRIORIDADE` |
| $\ge 100.000$ ha | `MEDIA_PRIORIDADE` |
| Caso contrário | `MONITORAMENTO` |

### 2.4. Código de Classificação (ETL)

```python
def _classificar_area_ti(self, area_hectares):
    if area_hectares >= 1000000: return "MUITO_GRANDE"
    if area_hectares >= 100000: return "GRANDE"
    if area_hectares >= 10000: return "MEDIA"
    if area_hectares > 0: return "PEQUENA"
    return "NAO_INFORMADA"

def _classificar_regularizacao(self, estagio):
    texto = limpar_texto_druid(estagio)
    if "REGULARIZADA" in texto: return "REGULARIZADA"
    if "DECLARADA" in texto: return "DECLARADA"
    if "DELIMITADA" in texto: return "DELIMITADA"
    if "IDENTIFICADA" in texto or "EM ESTUDO" in texto: return "EM_ESTUDO_IDENTIFICACAO"
    return texto if texto != "NAO INFORMADO" else "NAO_INFORMADO"

def _classificar_prioridade_funai(self, estagio_regularizacao, em_faixa_fronteira, area_hectares):
    if em_faixa_fronteira == "SIM" and area_hectares >= 100000: return "ALTA_PRIORIDADE"
    if estagio_regularizacao != "REGULARIZADA": return "ALTA_PRIORIDADE"
    if area_hectares >= 100000: return "MEDIA_PRIORIDADE"
    return "MONITORAMENTO"
```

## 3. Fórmula do Índice de Pressão Territorial

O índice consolida a intensidade térmica (FRP), o risco meteorológico de fogo (calculado pelo INPE) e a distância do evento até o limite da Terra Indígena mais próxima. O cálculo é realizado em [calculators.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/streaming_processing/processors/calculators.py).

$$ \text{índice\_pressão}_{TI} = \frac{FRP \times (1 + risco\_fogo\_inpe)}{\max(dist\_terra\_indígena_{km}, 0.1)} $$

### 3.1. Thresholds de Pressão

| Índice | Classe | Significado |
|---|---|---|
| $\ge 300$ | `PRESSAO_CRITICA` | Incêndio massivo colado ou dentro da TI |
| $\ge 100$ | `PRESSAO_ALTA` | Frente de fogo avançando perigosamente |
| $\ge 30$ | `PRESSAO_MEDIA` | Focos detectados no entorno |
| $> 0$ | `PRESSAO_BAIXA` | Atividade térmica distante |
| $0$ | `SEM_PRESSAO` | Sem ameaça detectada |

```python
@staticmethod
def classe_pressao_territorial(indice):
    if indice >= 300: return "PRESSAO_CRITICA"
    if indice >= 100: return "PRESSAO_ALTA"
    if indice >= 30: return "PRESSAO_MEDIA"
    if indice > 0: return "PRESSAO_BAIXA"
    return "SEM_PRESSAO"
```

## 4. Classificação Operacional Espacial (Dentro vs. Entorno)

A modelagem de dados no Superset ([ds_eventos_indigenas.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/virtual_datasets/ds_eventos_indigenas.sql)) distingue se a ameaça encontra-se dentro do polígono ou apenas na vizinhança, exercendo pressão de borda:

- **DENTRO**: O cluster de focos intersecta fisicamente o polígono da Terra Indígena (`fk_terra_indigena != 'NAO INFORMADO'`).
- **ENTORNO**: Focos fora do perímetro, mas dentro do raio de pressão ativa (`indice_pressao_terra_indigena > 0`).

```sql
CASE
  WHEN fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO'
  THEN 'DENTRO'
  ELSE 'ENTORNO'
END AS tipo_ameaca
```

## 5. Análise de Risco Operacional

O ranking abaixo consolida os dados dos últimos 7 dias para monitoramento pelas ONGs e pela própria FUNAI ([03_ranking_tis_ameacadas.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/stakeholders/ongs_indigenas/03_ranking_tis_ameacadas.sql)):

```sql
SELECT
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_nome') as nome_terra_indigena,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_etnia') as etnia,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_uf') as uf_sigla,
  COUNT(f.fire_event_id) as total_eventos,
  SUM(f.total_focos) as total_focos_entorno,
  SUM(f.indice_pressao_terra_indigena) as pressao_acumulada
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.fk_terra_indigena_proxima IS NOT NULL
  AND f.fk_terra_indigena_proxima != 'NAO_INFORMADO'
GROUP BY 1, 2, 3
ORDER BY pressao_acumulada DESC
LIMIT 50;
```

### 5.1. Interpretação Operacional
O ranking ordena as Terras Indígenas pela métrica `pressao_acumulada`, que consiste no somatório dos índices de todos os eventos registrados no período. Um território com classe `PRESSAO_CRITICA` associado ao tipo de ameaça `DENTRO` configura estado de **emergência imediata**, o que indica que as frentes de fogo romperam as fronteiras do território. Um caso notável avaliado em testes operacionais, como o da Aldeia Canoanã (Ilha do Bananal), demonstra de forma trágica e pragmática essa exata classificação.


## 6. Estudo de Caso Territorial: Terra Indígena Parque do Araguaia e Aldeia Canoanã

A **Terra Indígena (TI) Parque do Araguaia** é um dos territórios socioambientais mais singulares e importantes do Brasil, figurando de maneira recorrente nas faixas mais severas de pressão calculadas pela nossa plataforma analítica.

### 6.1. Dimensão Territorial e Geografia
* **Extensão e Localização:** Cobre aproximadamente 1,35 milhão de hectares, ocupando cerca de 3/4 da porção centro-sul da **Ilha do Bananal** (a maior ilha fluvial do mundo), situada inteiramente no estado do Tocantins.
* **Bacia Hidrográfica e Municípios:** Estende-se pela bacia hidrográfica do Rio Araguaia e abrange áreas de três municípios tocantinenses:
  * **Formoso do Araguaia** (município onde se situa a Aldeia Canoanã);
  * **Lagoa da Confusão**;
  * **Pium**.
* **Bioma e Dupla Afetação:** O bioma é 100% Cerrado, porém posicionado em transição direta com a Floresta Amazônica, o que lhe confere alta biodiversidade. A região é marcada por ciclos de grandes inundações sazonais, mantendo uma relação íntima de subsistência e preservação com os rios através da pesca artesanal. Existem trechos sob regime de **dupla afetação**, nos quais os limites de preservação ambiental do Parque Nacional e os direitos territoriais indígenas se sobrepõem e são geridos conjuntamente por órgãos ambientais (ICMBio) e comunidades locais.

### 6.2. Histórico e Evolução da Demarcação
1. **Origem (1959):** O território integrava originalmente o Parque Nacional do Araguaia, criado em 1959, que englobava toda a extensão da Ilha do Bananal.
2. **A Divisão (1971):** Para equacionar conflitos de uso da terra e assegurar os direitos dos povos originários, o governo federal reduziu o Parque Nacional a apenas 1/4 da ilha (na porção norte). Os outros 3/4 (centro-sul) tornaram-se o Parque Indígena do Araguaia sob tutela da FUNAI.
3. **Homologação Definitiva (1998):** Em 14 de abril de 1998, a área foi oficialmente homologada por decreto presidencial, passando a se chamar formalmente Terra Indígena Parque do Araguaia.

### 6.3. População e Diversidade Étnica
Segundo dados oficiais do Censo do IBGE, a TI abriga aproximadamente 4.503 indígenas distribuídos por diversas aldeias. O território é compartilhado por quatro povos principais:
* **Javaé (Iny):** Grupo majoritário na região do Rio Javaés. A Aldeia Canoanã é uma de suas comunidades mais antigas e estruturadas.
* **Karajá (Iny):** Historicamente ligados aos Javaé, habitando predominantemente as margens do canal principal do Rio Araguaia.
* **Avá-Canoeiro:** Povo em situação histórica de extrema vulnerabilidade. Em 1976, após contatos traumáticos com frentes de expansão, sobreviventes foram transferidos pela FUNAI para a Aldeia Canoanã, onde residem até a atualidade.
* **Apyãwa (Tapirapé):** Povo com presença e trânsito histórico registrado na região.

### 6.4. Conexão com os Resultados do Modelo Analítico
Durante a simulação e análise operacional dos dados de 2025/2026, a TI Parque do Araguaia despontou no 3º lugar do ranking nacional de pressão acumulada. Essa vulnerabilidade matemática decorre da expansão das fronteiras agropecuárias a partir de Formoso do Araguaia, cujas áreas de queima exercem intensa pressão de borda sobre a calha fluvial do Rio Javaés. A posterior ocorrência de incêndio devastador na Aldeia Canoanã em setembro de 2026 corrobora a capacidade do sistema em apontar antecipadamente territórios com vulnerabilidade crítica acumulada.
