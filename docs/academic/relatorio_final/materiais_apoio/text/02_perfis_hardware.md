# 2. Perfis de Hardware (Configurações Analisadas)

Este documento destrincha as configurações aplicadas aos nós do Apache Druid durante o *benchmark*. A estratégia de testes não focou na otimização do código SQL, mas sim na alocação de recursos físicos (CPU e RAM) para Broker e Historical, com o objetivo de descobrir a capacidade máxima sustentada antes da ocorrência de falhas ou degradação na latência.

## A Matriz de Configurações

Foram estabelecidos três perfis distintos de capacidade (alocados via Docker). As mudanças de perfil aplicam-se exclusivamente aos nós de consulta (Broker e Historical). Os demais serviços (Zookeeper, PostgreSQL e Coordinator) mantiveram-se inalterados para todas as rodadas.

| Cenário | CPU | GB (RAM) | Threads de Processamento | Buffers de Merge | Trade-off Analítico |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline** | 1.000 | 1.000 | 1 | 1 | Menor consumo; maior risco de saturação em *joins* concorrentes. |
| **Balanced** | 1.500 | 1.500 | 2 | 2 | Uso diário moderado; melhora QPS na concorrência 2, mas vulnerável à concorrência 4. |
| **Query Heavy** | 2.000 | 2.000 | 3 | 3 | Maior consumo de recursos do *host*; perfil necessário para estabilidade máxima na concorrência 4. |

*(Tabela importada a partir de `tables/scenario_profiles.tex`)*

## Explicação das Variáveis e Hipóteses

### 1. Limites de CPU e RAM
- O Druid utiliza CPU não só para coordenar as *threads* de processamento (*Historical*) e agregação final (*Broker*), mas também para serializar os resultados de rede via HTTP. 
- A RAM no Druid se divide entre o *heap* da JVM (usado para objetos de consulta na memória) e o *direct memory* (*off-heap*), usado para ler mapas na memória e agrupar (*Group By*) os resultados. O aumento linear de 1 GB (*Baseline*) para 2 GB (*Query Heavy*) visa impedir *Out Of Memory* (*OOM*) silenciosos durante *joins* multidimensionais.

### 2. Threads de Processamento (NumThreads)
O parâmetro de processamento principal do *Historical*.
- **Hipótese Metodológica**: Uma única *thread* (*Baseline*) força consultas simultâneas a enfileirarem (*queueing*). Conforme a concorrência aumenta de 1 para 4 requisições disparadas simultaneamente, se não houver *threads* suficientes, o enfileiramento estoura o limite de *timeout* do cliente.
- Ao escalar para 3 *threads* (*Query Heavy*), o Historical processa mais blocos em paralelo, sacrificando mais CPU do hospedeiro, mas reduzindo drasticamente as latências de cauda.

### 3. Buffers de Merge (Merge Buffers)
Recurso crucial gerenciado primariamente pelo *Broker*.
- **Hipótese Metodológica**: O *merge buffer* é um pool de memória alocado antes do início da consulta. Consultas densas (como agrupamentos sobre milhões de intersecções geográficas) travam o sistema se não houver *merge buffers* livres.
- Escalar de 1 para 3 *buffers* é a mudança chave para lidar com agregações espaciais massivas e evitar erros de `Resource Limit Exceeded` devolvidos pelo Druid.

## A Regra do Teste de Perfil
Cada perfil (Baseline, Balanced, Query Heavy) foi exposto ao **mesmo catálogo de consultas**, nos **mesmos dados**, disparando as requisições em 3 ondas de concorrência (`N=1`, `N=2`, `N=4`). O perfil vencedor não é o mais rápido no vácuo, mas sim aquele que garante 100% de confiabilidade na devolução (Taxa de Erro Zero) sem asfixiar o servidor (*host*).
