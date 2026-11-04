# ADR 004: Execução In-Memory Orientada a Objetos de Assets no Apache Dagster

* **Status:** Aprovado
* **Data:** 2026-11-03
* **Decisores:** Engenharia de Dados CCO-DataOps

---

## 1. Contexto

Muitos pipelines de orquestração de dados utilizam o Dagster apenas como despachante de comandos de terminal via subprocessos:
```python
@asset
def meu_asset():
    subprocess.run(["python", "script_legado.py"], check=True)
```
Essa abordagem acarreta desvantagens severas:
* **Overhead de Processo**: Cada etapa reinicia o interpretador Python, recarregando bibliotecas pesadas (GeoPandas, Shapely, PyProj, Scipy) do zero.
* **Perda de Rastreabilidade e Tipagem**: A comunicação entre etapas depende de arquivos transitórios no disco, perdendo a validação estática de tipos.
* **Opacidade de Logs**: O contexto de execução do Dagster (`AssetExecutionContext`) não captura métricas refinadas de execução interna.

---

## 2. Decisão

Integrar os **Software-Defined Assets (SDA)** do Apache Dagster diretamente com o design orientado a objetos:

1. **Herança do Contrato Canônico**:
   - Todas as etapas operacionais (Bronze, Silver e Gold) herdam de [`ExecutablePipelineStep[TResult]`](../../src/core/contracts/contracts.py).
2. **Despacho em Memória (`execute_pipeline_step`)**:
   - No repositório de assets [`src/orchestration/dagster/repo.py`](../../src/orchestration/dagster/repo.py), os assets instanciam as classes de domínio e despacham a execução via função pura:
     ```python
     def execute_pipeline_step(context: Optional[AssetExecutionContext], step: ExecutablePipelineStep) -> Any:
         if context is not None:
             context.log.info(f"Executando componente POO: {step.step_name}")
         resultado = step.execute()
         if context is not None:
             total = len(resultado) if hasattr(resultado, "__len__") and resultado is not None else "N/A"
             context.log.info(f"Componente {step.step_name} finalizado (itens: {total}).")
         return resultado
     ```
3. **Telemetria Automática**:
   - A cronometragem do *Template Method* (`execute()`) é capturada diretamente pelo Dagster para relatórios de observabilidade.

---

## 3. Consequências

### Positivas
* **Performance Superior**: Eliminação do custo de inicialização de múltiplos processos Python.
* **Testabilidade Plena**: Os assets podem ser executados isoladamente em testes unitários (`test_capacity_report_assets.py`) sem dependência de daemons ou workers externos.
* **Linhagem Clara**: O Dagster mapeia as dependências exatas entre tabelas no grafo SDA.

### Negativas / Trade-offs
* Módulos devem gerenciar o consumo de memória RAM para evitar vazamentos em execuções de longa duração no mesmo processo.
