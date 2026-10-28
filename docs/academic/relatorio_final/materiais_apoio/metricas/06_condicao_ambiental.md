# 06. Condição Ambiental

## Conceito
Os índices de Condição Ambiental e Severidade de Queimada são métricas compostas que combinam múltiplas variáveis meteorológicas e de fogo para classificar o grau de perigo ambiental. Diferente do FRP (que mede energia instantânea), esses índices incorporam o contexto climático: dias sem chuva, precipitação acumulada e risco de fogo calculado pelo INPE.

## Classificação do Risco INPE

O risco de fogo base originado do INPE é categorizado em quatro níveis:

| Valor | Classe |
|---|---|
| $\ge$ 0.8 | `RISCO_ALTO` |
| $\ge$ 0.5 | `RISCO_MEDIO` |
| > 0 | `RISCO_BAIXO` |
| 0 ou null | `SEM_RISCO` |

```python
@staticmethod
def classe_risco_fogo(risco):
    if risco is None: return "SEM_RISCO"
    if risco >= 0.8: return "RISCO_ALTO"
    if risco >= 0.5: return "RISCO_MEDIO"
    if risco > 0: return "RISCO_BAIXO"
    return "SEM_RISCO"
```

## Índice de Condição Ambiental (ICA)

O ICA atua como um termômetro de propensão do ambiente ao alastramento de incêndios, combinando a estimativa de risco do INPE com o efeito logarítmico de dias acumulados sem chuva.

**Fórmula:**
$$ \text{ICA} = \frac{\text{risco\_fogo} \times \ln(\text{dias\_sem\_chuva} + 1)}{1 + \text{precipitação}_{mm}} $$

> [!NOTE]
> **Interpretação**: A precipitação no denominador atua como um atenuante natural — a presença de chuva reduz imediatamente o índice, mitigando o perigo ambiental acumulado.

**Limiares (Thresholds) do ICA:**

| Índice | Classe |
|---|---|
| $\ge$ 1.5 | `CONDICAO_CRITICA` |
| $\ge$ 0.8 | `CONDICAO_ALTA` |
| $\ge$ 0.3 | `CONDICAO_MEDIA` |
| < 0.3 | `CONDICAO_BAIXA` |

```python
@staticmethod
def indice_condicao_ambiental(risco, dias_sem_chuva, precipitacao):
    risco_base = risco if risco is not None else 0.0
    dias_base = dias_sem_chuva if dias_sem_chuva is not None else 0.0
    chuva_base = precipitacao if precipitacao is not None else 0.0
    return round(risco_base * math.log(dias_base + 1) / (1 + chuva_base), 6)

@staticmethod
def classe_condicao_ambiental(indice):
    if indice >= 1.5: return "CONDICAO_CRITICA"
    if indice >= 0.8: return "CONDICAO_ALTA"
    if indice >= 0.3: return "CONDICAO_MEDIA"
    return "CONDICAO_BAIXA"
```

## Índice de Queimada em Evento (IQE)

Diferentemente do ICA, o Índice de Queimada em Evento (IQE) **inclui o FRP** (Fire Radiative Power), representando a intensidade real do fogo já instaurado. 

**Fórmula:**
$$ \text{IQE} = \frac{\ln(FRP + 1) \times (1 + \text{risco}) \times (1 + \ln(\text{dias\_sem\_chuva} + 1))}{1 + \text{precipitação}_{mm}} $$

> [!IMPORTANT]
> **Interpretação**: O uso de $\ln(FRP + 1)$ suaviza picos extremos de FRP, enquanto os multiplicadores de risco e seca amplificam situações de longa estiagem. Este índice mede a *severidade efetiva* do incêndio ao combinar dados de satélite ativos (FRP) com dados meteorológicos persistentes.

**Limiares (Thresholds) do IQE:**

| Índice | Classe | Significado |
|---|---|---|
| $\ge$ 20 | `EVENTO_CRITICO` | Incêndio severo em condições de seca extrema |
| $\ge$ 10 | `EVENTO_ALTO` | Incêndio significativo com contexto desfavorável |
| $\ge$ 4 | `EVENTO_MEDIO` | Queimada ativa com potencial de piora |
| > 0 | `EVENTO_BAIXO` | Foco detectado com condições atenuantes |
| 0 | `SEM_EVENTO` | Sem atividade |

```python
@staticmethod
def indice_queimada_evento(frp, risco, dias_sem_chuva, precipitacao):
    frp_base = frp if frp is not None else 0.0
    risco_base = risco if risco is not None else 0.0
    dias_base = dias_sem_chuva if dias_sem_chuva is not None else 0.0
    chuva_base = precipitacao if precipitacao is not None else 0.0
    indice = math.log(frp_base + 1) * (1 + risco_base) * (1 + math.log(dias_base + 1)) / (1 + chuva_base)
    return round(indice, 6)

@staticmethod
def classe_queimada_evento(indice):
    if indice >= 20: return "EVENTO_CRITICO"
    if indice >= 10: return "EVENTO_ALTO"
    if indice >= 4: return "EVENTO_MEDIO"
    if indice > 0: return "EVENTO_BAIXO"
    return "SEM_EVENTO"
```

## Interpretação Operacional

O **ICA** é um termômetro ambiental prévio (avaliado sem necessariamente considerar fogo ativo no instante). O **IQE**, por sua vez, é o indicador de gravidade *real* de um incêndio em andamento. Quando observamos simultaneamente um $\text{ICA} \ge 1.5$ e um $\text{IQE} \ge 20$, deparamo-nos com o pior cenário possível: seca extrema alimentando um incêndio altamente enérgico e violento, sob condições climáticas que amplificam ativamente sua propagação pela infraestrutura local.

## Arquivos Fonte
- [calculators.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/streaming_processing/processors/calculators.py)
