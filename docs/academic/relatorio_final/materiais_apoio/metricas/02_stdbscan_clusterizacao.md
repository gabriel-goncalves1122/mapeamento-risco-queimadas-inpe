# Clusterização de Focos (ST-DBSCAN)

## Conceito
O ST-DBSCAN (Spatio-Temporal Density-Based Spatial Clustering of Applications with Noise) é o algoritmo que transforma milhões de pontos de calor individuais (pixels de satélite) em "Eventos de Incêndio" coesos — polígonos contínuos com identidade, área, duração e métricas agregadas. Sem ele, o sistema teria apenas coordenadas avulsas sem contexto operacional.

## Parâmetros de Configuração
Os parâmetros base para o algoritmo estão definidos em [settings.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/config/settings.py) (linhas 101-105):

| Parâmetro | Valor | Significado |
|---|---|---|
| `eps_km` | $5.0$ | Raio espacial: focos até 5km de distância pertencem ao mesmo cluster |
| `eps_dias` | $2.0$ | Raio temporal: focos separados por até 2 dias pertencem ao mesmo evento |
| `min_samples` | $3$ | Mínimo de 3 focos para constituir um cluster válido |
| `max_duration_days` | $7.0$ | Janela de rolamento máxima de 7 dias para evitar crescimento infinito |
| `area_buffer_km` | $0.5$ | Buffer de 500m aplicado a hulls degenerados (pontos colineares) |

## Fórmula de Escalonamento Temporal
Como o DBSCAN padrão espera uma métrica de distância uniforme (Euclidiana), o eixo temporal precisa ser projetado em espaço quilométrico:

$$
t_{km} = t_{dias} \times \frac{eps_{km}}{\max(eps_{dias}, 0.001)}
$$

Assim, 2 dias de distância temporal equivalem a 5 km de distância "virtual", tornando a métrica isotrópica.

## Projeção Métrica
Coordenadas GPS (`EPSG:4326`, graus) são projetadas para `EPSG:5880` (Policônica Brasil, metros) antes do clustering para garantir distâncias euclidianas corretas em metros.

## Geometria do Evento
O processamento geométrico dos eventos ocorre nas seguintes etapas:
1. Os pontos métricos do cluster formam um objeto `MultiPoint`.
2. Calcula-se o `convex_hull` (menor polígono convexo que envolve todos os pontos).
3. Se o hull for degenerado (`Point` ou `LineString`, com área zero), aplica-se um buffer de 500m.
4. A geometria é reprojetada para `WGS84` para armazenamento como GeoJSON.
5. A área é calculada em km²: $\text{area\_km2} = \frac{\text{area\_metros}}{1.000.000}$.

**Código-fonte da Geometria** ([eventizador.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/gold/src/science/dbscan/eventizador.py), linhas 276-304):
```python
def _geometria_evento(self, grupo: pd.DataFrame):
    gdf_gps = gpd.GeoDataFrame(
        grupo, geometry=gpd.points_from_xy(grupo["longitude"], grupo["latitude"]),
        crs=f"EPSG:{EPSG_GPS}",
    )
    pontos_metricos = gdf_gps.to_crs(epsg=EPSG_METRICO).geometry
    multiponto = MultiPoint(list(pontos_metricos))
    geom_metric = multiponto.convex_hull
    if geom_metric.geom_type in {"Point", "LineString"} or geom_metric.area <= 0:
        geom_metric = multiponto.buffer(self.config.area_buffer_km * 1000.0)
    centroide_metric = geom_metric.centroid
    geom_gps = gpd.GeoSeries([geom_metric], crs=f"EPSG:{EPSG_METRICO}").to_crs(epsg=EPSG_GPS).iloc[0]
    centroide_gps = gpd.GeoSeries([centroide_metric], crs=f"EPSG:{EPSG_METRICO}").to_crs(epsg=EPSG_GPS).iloc[0]
    area_km2 = round(float(geom_metric.area) / 1_000_000.0, 6)
    return geom_gps, float(centroide_gps.y), float(centroide_gps.x), area_km2
```

**Código-fonte do Clustering** ([eventizador.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/gold/src/science/dbscan/eventizador.py), linhas 150-175):
```python
def _eventizar_janela(self, grupo_janela: pd.DataFrame) -> list[dict]:
    if len(grupo_janela) < self.config.min_samples:
        return []
    pontos_metricos = self._pontos_metricos(grupo_janela)
    trabalho = grupo_janela.copy()
    trabalho["x_km"] = pontos_metricos.x / 1000.0
    trabalho["y_km"] = pontos_metricos.y / 1000.0
    min_time = trabalho["datahora_dt"].min()
    trabalho["tempo_dias"] = (
        (trabalho["datahora_dt"] - min_time).dt.total_seconds() / (24 * 3600)
    )
    trabalho["tempo_escalado_km"] = trabalho["tempo_dias"] * (
        self.config.eps_km / max(self.config.eps_dias, 0.001)
    )
    matriz = trabalho[["x_km", "y_km", "tempo_escalado_km"]].to_numpy()
    labels = DBSCAN(
        eps=self.config.eps_km,
        min_samples=self.config.min_samples,
        n_jobs=1,
    ).fit_predict(matriz)
    trabalho["cluster_evento"] = labels
    eventos = []
    for cluster_id, grupo_cluster in trabalho[trabalho["cluster_evento"] != -1].groupby("cluster_evento"):
        if len(grupo_cluster) < self.config.min_samples:
            continue
        eventos.append(self._montar_payload_evento(grupo_cluster, int(cluster_id)))
    return eventos
```

## Definição de Megadesastre
Um evento de grande magnitude é classificado como "Megadesastre". Os critérios estão definidos na query de análise:

| Critério | Threshold |
|---|---|
| `total_focos` | $\geq 5.000$ |
| `area_evento_km2` | $\geq 500.0 \text{ km}^2$ |
| Janela temporal | últimos 7 dias |

**SQL do Megadesastre** (`02_megadesastres_ativos.sql`):
```sql
SELECT
  f.__time as inicio_evento,
  f.fire_event_id,
  LOOKUP(f.fk_municipio_principal, 'municipios_nome') as nome_municipio,
  f.duracao_dias,
  f.area_evento_km2,
  f.total_focos,
  f.soma_frp,
  f.indice_pressao_maxima
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.total_focos >= 5000 
  AND f.area_evento_km2 >= 500.0
ORDER BY f.total_focos DESC
LIMIT 20;
```

## Interpretação Operacional
Um evento com `total_focos` $\geq 5000$ e `area_evento_km2` $\geq 500$ é classificado como Megadesastre. Os parâmetros `eps_km=5` e `eps_dias=2` garantem que focos próximos no espaço-tempo sejam agrupados, enquanto focos isolados (ruído, `label=-1`) são descartados.

**Arquivos de Origem:**
- [settings.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/config/settings.py)
- [constants.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/config/constants.py)
- [eventizador.py](file:///home/gabriel/Documentos/UNIFEI/IC%20-%20DataOps/pipelines/gold/src/science/dbscan/eventizador.py)
