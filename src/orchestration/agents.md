# CCO DataOps - Orchestration Context (Dagster)

Bem-vindo ao Orquestrador do DataOps (Apache Dagster). O maestro do Data Warehouse.

## 🤖 Regras para a Inserção de Agentes
1. **Proibição de Scripts Órfãos**: Todo processamento em lote (ETL), inteligência artificial (inferência batch), limpeza de dados espaciais ou treinamento de rede que deva ocorrer periodicamente deve ser implementado como um `Software-Defined Asset (@asset)` no Dagster. **Não crie CRON Jobs soltos no S.O.**
2. **Definição de Assets**:
   - Assets devem estar localizados no repositório modular (como `src/orchestration/assets/`).
   - Utilize a decoração `@asset` e declare estritamente as dependências de inputs como argumentos na assinatura da função do asset (DAG pipeline). 
   - **Integração Científica**: Algoritmos de Machine Learning e Ciência de Redes (ex: clusterização de polígonos ST-DBSCAN e cálculos de Betweenness Centrality no NetworkX) DEVEM ser obrigatoriamente incluídos como `@assets` dependentes da malha principal, nunca rodados em notebooks isolados.
3. **Agendamento**: Defina `@schedule` para atualizações diárias ou noturnas (ex: processamento do ST-DBSCAN de madrugada ou atualização diária das tabelas dimensionais do IBGE).
4. **Execução de Comandos Dagster**: Para iniciar a interface UI do orquestrador localmente, o Agente de IA deve rodar:
   - ✅ Correto: `uv run dagster dev -f src/orchestration/repo.py`
   - ✅ Correto: `.venv/bin/dagster dev -f src/orchestration/repo.py`
5. **Comunicação com ETLs (Clean Architecture)**: O Dagster apenas *accciona* a engrenagem. Ao orquestrar a geração das Dimensões (camada `src/etl/`), você deve importar a classe correspondente (`BaseETL` subclass) e invocar o método herdado `.execute()` dentro do contexto do Asset Dagster. Não re-escreva lógica de Pandas dentro do Asset.

## 📝 Comentários na Orquestração
Siga a regra global de comentários em `src/agents.md`: explique dependências, ordem de materialização e motivo de isolamento por subprocesso quando isso afetar linhagem, reexecução ou diagnóstico. Evite narrar chamadas Dagster óbvias.
