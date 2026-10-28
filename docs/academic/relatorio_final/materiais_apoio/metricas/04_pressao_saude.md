# Índice de Pressão sobre a Saúde

## 1. Conceito

O **Índice de Pressão sobre a Saúde** quantifica a ameaça que incêndios florestais e emissões de fumaça representam para a infraestrutura hospitalar e de pronto atendimento do SUS. O sistema realiza o cruzamento geoespacial das coordenadas dos eventos de incêndio com mais de 550 mil estabelecimentos cadastrados no Cadastro Nacional de Estabelecimentos de Saúde (CNES), mantido pelo DataSUS. A métrica permite identificar quais unidades hospitalares estão sob risco direto devido à proximidade das frentes de fogo ou à dispersão da pluma térmica.

## 2. Taxonomia e Classificação das Unidades de Saúde

Os dados das unidades de saúde são pré-processados na Camada Silver ([etl_dim_hospitais.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/etl_dimensions/etl_dim_hospitais.py)) com uma taxonomia baseada nas categorias oficiais do CNES.

### 2.1. Taxonomia de Unidades (CNES)

| Código | Categoria | Exemplo |
|---|---|---|
| 05, 07, 15, 20, 21, 61, 62, 73 | `HOSPITAL_URGENCIA_EMERGENCIA` | Hospital Geral, Pronto-Socorro |
| 01, 02, 71, 72 | `ATENCAO_BASICA` | UBS, Posto de Saúde |
| 39, 67, 80 | `APOIO_DIAGNOSTICO_LABORATORIAL` | Laboratório |
| 64, 68, 76, 81, 82, 84 | `REGULACAO_GESTAO` | Central de Regulação |
| 32, 40, 42 | `UNIDADE_MOVEL` | SAMU, Ambulância |
| 50, 85, 83 | `VIGILANCIA_IMUNIZACAO` | Vigilância Sanitária |
| 04, 22, 36, 77, 78, 79 | `CONSULTORIO_ESPECIALIDADE` | Consultório |
| 43 | `FARMACIA` | Farmácia |
| Contém "SAUDE INDIGENA" | `SAUDE_INDIGENA` | CASAI, Polo Base |

### 2.2. Critérios de Criticidade

Uma unidade de saúde é classificada como **Crítica** se atender a qualquer um dos seguintes critérios:
1. É um Hospital de Urgência/Emergência (ex.: Hospital Geral, Pronto-Socorro).
2. É uma Unidade Móvel (ex.: SAMU, UTI Móvel).
3. Pertence à rede de Saúde Indígena (ex.: CASAI).
4. Possui funcionamento 24 horas, independentemente de sua categoria primária.

```python
def _classificar_unidade_critica(self, categoria, funciona_24h):
    if categoria in ["HOSPITAL_URGENCIA_EMERGENCIA", "UNIDADE_MOVEL", "SAUDE_INDIGENA"]: return "SIM"
    if funciona_24h == "S": return "SIM"
    return "NAO"

def _classificar_capacidade_saude(self, categoria, funciona_24h):
    if categoria == "HOSPITAL_URGENCIA_EMERGENCIA" and funciona_24h == "S": return "ALTA_CAPACIDADE"
    if categoria == "HOSPITAL_URGENCIA_EMERGENCIA": return "MEDIA_CAPACIDADE"
    if categoria == "UNIDADE_MOVEL": return "RESPOSTA_MOVEL"
    if categoria == "SAUDE_INDIGENA": return "SAUDE_INDIGENA"
    if categoria == "ATENCAO_BASICA": return "ATENCAO_LOCAL"
    return "SUPORTE"

def _classificar_atendimento(self, categoria, funciona_24h):
    if funciona_24h == "S" and categoria == "HOSPITAL_URGENCIA_EMERGENCIA": return "CRITICO_24H"
    if categoria == "HOSPITAL_URGENCIA_EMERGENCIA": return "CRITICO"
    if categoria == "UNIDADE_MOVEL": return "MOBILIDADE_ASSISTENCIAL"
    if categoria == "SAUDE_INDIGENA": return "SAUDE_INDIGENA"
    if categoria == "ATENCAO_BASICA": return "ATENCAO_LOCAL"
    return "SUPORTE"
```

## 3. Fórmula do Índice de Pressão sobre a Saúde

O índice correlaciona a potência térmica radiante, o risco meteorológico de ignição e a distância mínima registrada entre o cluster e o estabelecimento de saúde cadastrado no CNES mais próximo ([calculators.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/streaming_processing/processors/calculators.py)).

$$ \text{índice\_pressão}_{saúde} = \frac{FRP \times (1 + risco\_fogo\_inpe)}{\max(dist\_hospital_{km}, 0.1)} $$

Durante a clusterização espacial, as seguintes variáveis são computadas:
- `FRP` (na fórmula como `frp_base`): O valor acumulado da soma de FRP em todo o cluster de focos.
- `risco_fogo_inpe` (`risco_base`): O valor máximo de risco de fogo observado naquele cluster.
- `dist_hospital_km`: A distância euclidiana/métrica, convertida via sistema de coordenadas métricas (EPSG:5880), até a unidade CNES.

### 3.1. Thresholds do Índice

| Índice | Classe |
|---|---|
| $\ge 100$ | `CRITICO` |
| $\ge 30$ | `ALTO` |
| $\ge 10$ | `MEDIO` |
| $> 0$ | `BAIXO` |
| $0$ | `SEM_INDICE` |

## 4. Consultas e Alertas (Camada Analítica / Superset)

As queries a seguir fornecem materializações analíticas para Defesa Civil e Órgãos de Saúde operarem de forma proativa perante os eventos.

### 4.1. Alerta Hospitalar Imediato

Esta query ([01_alerta_hospitais.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/stakeholders/defesa_civil/01_alerta_hospitais.sql)) expõe os hospitais que estão em alerta na janela de tempo recente de 7 dias, elencados pelo índice de pressão térmica.

```sql
SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_municipio_principal, 'municipios_nome') as nome_municipio,
  LOOKUP(f.fk_municipio_principal, 'municipios_uf') as uf_sigla,
  f.total_focos,
  f.soma_frp,
  f.indice_pressao_saude,
  LOOKUP(f.fk_hospital, 'hospitais_nome') as nome_hospital,
  LOOKUP(f.fk_hospital, 'hospitais_tipo') as tipo_unidade,
  LOOKUP(f.fk_hospital, 'hospitais_critico') as hospital_critico,
  LOOKUP(f.fk_hospital, 'hospitais_24h') as funciona_24h
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_pressao_saude > 0
ORDER BY f.indice_pressao_saude DESC
LIMIT 50;
```

### 4.2. Top Hospitais Ameaçados e Enriquecimento Dimensional

Cruzamento detalhado das estatísticas vitais da Tabela Fato com as tipologias estruturais e logísticas da Dimensão de Hospitais ([07_saude_lookup_hospitais_top.sql](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/infrastructure/superset/queries/07_eventos_incendio/07_saude_lookup_hospitais_top.sql)).

```sql
WITH top_hospitais AS (
  SELECT
    fk_hospital AS codigo_cnes,
    COUNT(*) AS total_eventos,
    SUM(total_focos) AS focos_representados,
    MIN(distancia_hospital_km) AS menor_distancia_km,
    AVG(distancia_hospital_km) AS distancia_media_km,
    MAX(indice_pressao_saude) AS maior_pressao_saude
  FROM fato_eventos_incendio
  WHERE fk_hospital <> 'NAO INFORMADO'
  GROUP BY 1
  ORDER BY total_eventos DESC
  LIMIT 100
)
SELECT h.codigo_cnes, h.nome_hospital, h.categoria_unidade, h.tipo_unidade_critica,
  h.funciona_24h, t.total_eventos, t.focos_representados, t.menor_distancia_km, t.maior_pressao_saude
FROM dim_hospitais_cnes h INNER JOIN top_hospitais t ON h.codigo_cnes = t.codigo_cnes;
```

## 5. Interpretação Operacional e Tomada de Decisão

A combinação dessas métricas revela cenários catastróficos para o colapso do SUS regional. Quando um hospital com classificação de atendimento `CRITICO_24H` consta no topo dos rankings com um $\text{índice\_pressão}_{saúde} \ge 100$, significa que um estabelecimento de máxima urgência está ameaçado pelas labaredas. Isso dispara gatilhos emergenciais duplos: o próprio Pronto-Socorro pode necessitar de evacuação parcial ou enfrentará aumento vertiginoso de internações respiratórias pela pluma densa de fumaça que encobre o raio geográfico ao seu redor, exatamente num momento em que a estrutura física pode estar em perigo.
