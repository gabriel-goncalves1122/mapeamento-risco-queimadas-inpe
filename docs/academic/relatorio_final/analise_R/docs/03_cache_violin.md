# Análise de Mitigação de Latência via Broker Cache (Violin Plot)

## A Ideia do Gráfico
Em painéis analíticos modernos, é padrão que múltiplos operadores fiquem "olhando" para as mesmas métricas. O Apache Druid embute um mecanismo chamado *Broker Query Cache*, feito exatamente para interceptar comandos idênticos e devolvê-los da RAM antes de acionar a varredura bruta de segmentos no disco. O objetivo deste **Violin Plot** é evidenciar a redução matemática do tempo de processamento proporcionada por esse cache.

## Fontes de Dados Utilizadas
- **Arquivos:** `raw_requests_cold.csv` e `raw_requests_warm.csv`
- **Métricas Chave:** `latencia_ms` em nível atômico (query a query), segmentado pela flag de configuração (Cold vs Warm).
- **Contexto:** Os dados provêm apenas da bateria `scenario_02_balanced`, isolando os tempos brutos em uma infraestrutura que se manteve estável e sem *Timeouts HTTP 500* que pudessem mascarar a pureza matemática.

## Análise dos Resultados
A representação em Escala Log10 revela densidades gritantes (a largura ou "barriga" do violino) na distribuição das respostas:
1. **Cold Start (Varredura no Disco/Segmentos):** O violino azul, que representa o sistema com cache desabilitado, mostra o processamento físico bruto. A densidade alarga-se perigosamente acima da faixa de $10^3$ (1.000ms a 10.000ms). Os longos cálculos espaciais ditam o ritmo dessa distribuição bimodal.
2. **Warm Start (Acerto de Memória):** O violino amarelo é brutalmente *achatado* para as camadas inferiores do eixo Y. Ao reaproveitar resultados, a maior densidade de resposta (a barriga gorda do violino) assenta-se abaixo dos $10^2$ (menos de 100 milissegundos). A caixa interna (Boxplot) confirma que 50% de todas as queries são resolvidas em frações minúsculas de segundo.

## Mitigação de Outliers (Anomalias de Desempenho)
**Fenômeno:** Presença de *Outliers* flutuando na parte superior extrema do violino amarelo (Consultas *Warm* que não foram rápidas).
**Causa Raiz:** *Cache Eviction* (Despejo). Com dezenas de filtros rodando ao mesmo tempo, o espaço reservado para Cache na memória RAM (Heap) estoura. O Druid precisa deletar (despejar) o cache salvo da *Query A* para guardar a da *Query B*. Se o operador olhar a tela A novamente, o Broker processa a frio no disco.
**Como Melhorar:** Aumentar expressivamente a propriedade `druid.cache.sizeInBytes` ou delegar o serviço de cacheamento para uma infraestrutura externa dedicada e elástica como *Memcached* ou *Redis*, livrando a Heap do Java desse dever primário.

## Conclusões (Impacto no SIRDA)
Para a usabilidade do SIRDA, fica comprovado estatisticamente que a adoção do *Query Cache* não é meramente um "bônus" de desempenho, mas um componente vital de arquitetura. É ele quem "salva" a CPU de calcular Joins Geográficos repetitivos. Um painel CCO sem Cache operaria o tempo todo na faixa azul (lento e sobrecarregado); com o Cache ativado, após a carga inicial matinal, o restante da operação flui quase em tempo real (na barriga amarela).
