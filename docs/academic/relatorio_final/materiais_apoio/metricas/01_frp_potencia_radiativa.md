# Potência Radiativa do Fogo (FRP - Fire Radiative Power)

## Conceito
FRP (Fire Radiative Power) é a potência radiativa do fogo medida em Megawatts (MW) por pixel de satélite. É a medição quantitativa instantânea da radiação térmica emitida por uma área em combustão, capturada pelos sensores dos satélites AQUA, TERRA (MODIS) e NOAA-20/SNPP (VIIRS). É a variável-mãe de todo o sistema SIRDA — todos os 6 índices de ameaça (rodovia, linha de transmissão, subestação, sistema isolado, saúde e terra indígena) são multiplicados pelo FRP. Quanto maior o FRP, maior a energia liberada pelo incêndio e, proporcionalmente, maior o perigo para qualquer infraestrutura próxima.

## Fórmula
O FRP é recebido diretamente do satélite (não é calculado pelo sistema). Porém, o sistema o utiliza como multiplicador base em todas as fórmulas de ameaça:

$$
\text{índice\_ameaça} = \frac{FRP \times (1 + risco\_fogo)}{\max(distância_{km}, 0.1)}
$$

## Thresholds de Classificação
As seguintes classes de FRP são definidas no sistema (ver arquivo `calculators.py`):

| FRP (MW) | Classe | Significado |
|---|---|---|
| $\geq 100$ | `EXTREMA` | Combustão violenta, risco de pirocúmulo |
| $\geq 50$ | `ALTA` | Incêndio de grande porte com propagação rápida |
| $\geq 10$ | `MEDIA` | Queimada ativa com potencial de expansão |
| $> 0$ | `BAIXA` | Foco detectado mas com baixa intensidade |
| $0$ ou null | `SEM_FRP` | Sem leitura disponível |

**Código-fonte** ([calculators.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/streaming_processing/processors/calculators.py), linhas 25-31):
```python
@staticmethod
def classe_frp(frp):
    if frp is None: return "SEM_FRP"
    if frp >= 100: return "EXTREMA"
    if frp >= 50: return "ALTA"
    if frp >= 10: return "MEDIA"
    if frp > 0: return "BAIXA"
    return "SEM_FRP"
```

## Agregações no Cluster ST-DBSCAN
Dentro do processo de clusterização, o FRP é agregado para cada evento de incêndio ([eventizador.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/gold/src/science/dbscan/eventizador.py), linhas 200-218):
- `soma_frp`: Energia acumulada de todo o cluster ($\sum FRP$). Serve como multiplicador principal de intensidade para todos os índices de ameaça do evento.
- `media_frp`: Intensidade térmica média por pixel.
- `max_frp`: Pico térmico dentro do cluster, usado como coluna de ordenação principal nas queries Druid (`ORDER BY max_frp DESC`).

## Como o FRP Alimenta os 6 Índices
**Código-fonte** ([calculators.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/silver/src/streaming_processing/processors/calculators.py), linhas 73-87):
```python
@staticmethod
def calcular_indices_ameaca(frp, risco, dist_rodovia, dist_linha, dist_sub, dist_sis, dist_hosp, dist_ti, tensao_kv, capac_mw):
    frp_base = frp if frp is not None else 0.0
    risco_base = risco if risco is not None else 0.0
    fator_risco = 1 + risco_base
    return {
        "indice_ameaca_rodovia": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_rodovia), 6),
        "indice_ameaca_linha": round(FogoCalculators.safe_div(frp_base * fator_risco * math.log(tensao_base + 1), dist_linha), 6),
        "indice_ameaca_subestacao": round(FogoCalculators.safe_div(frp_base * fator_risco * math.log(capacidade_base + 1), dist_sub), 6),
        "indice_ameaca_sistema_isolado": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_sis), 6),
        "indice_pressao_saude": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_hosp), 6),
        "indice_pressao_terra_indigena": round(FogoCalculators.safe_div(frp_base * fator_risco, dist_ti), 6),
    }
```

## Interpretação Operacional
Um foco com FRP $\geq 100$ MW próximo a qualquer infraestrutura crítica (hospital, subestação, terra indígena) deve acionar um alerta imediato. O FRP é a "temperatura do perigo" — é a única métrica que mede a intensidade real da combustão, e não apenas a detecção binária (fogo/não fogo).
