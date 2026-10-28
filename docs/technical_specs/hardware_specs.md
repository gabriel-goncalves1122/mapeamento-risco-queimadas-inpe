# Especificações de Hardware (Ambiente de Validação)

Este documento descreve as especificações físicas do ambiente onde o SIRDA foi desenvolvido e validado. O objetivo é demonstrar que a arquitetura suporta altíssimas cargas analíticas sob um hardware modesto (laptop padrão), dispensando supercomputadores para a prova de conceito.

## Especificações do Sistema

| Componente | Detalhe Técnico |
| :--- | :--- |
| **Processador (CPU)** | 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz |
| **Núcleos Lógicos** | 8 vCPUs (4 Cores / 8 Threads) |
| **Memória RAM** | 7.5 GiB (Aproximadamente 8 GB) |
| **Armazenamento** | 52 GB Total (Partição Raiz) |
| **Sistema Operacional**| Ubuntu Linux (x86_64) |
| **Virtualização** | VT-x Habilitado (Docker) |

> [!NOTE]
> **Impacto na Arquitetura:** A restrição primária de hardware (apenas 7.5 GiB de RAM total) exigiu uma calibração milimétrica nos recursos do ecossistema de dados para evitar incidentes de *Out of Memory (OOM)*. Essa calibração minuciosa pode ser conferida na análise do `docker-compose.yaml` neste mesmo repositório.
