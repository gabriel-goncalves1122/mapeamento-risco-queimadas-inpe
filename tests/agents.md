# CCO DataOps - Testing Context (Agent Guide)

Bem-vindo à suite de Engenharia de Qualidade (Q.E.). Garantir a corretude das predições de risco e do pipeline de streaming é a nossa prioridade número zero.

## 🧪 Padrão Pytest (CRÍTICO)
Agentes frequentemente esquecem de invocar os testes corretamente, gerando falsos negativos ambientais. Respeite as regras de invocação:
1. **Comandos de Execução**: Lembre-se, SEMPRE execute os testes usando o ambiente virtual da aplicação:
   - ✅ Correto: `uv run pytest tests/` ou `.venv/bin/pytest tests/`
   - ✅ Correto com verbosidade e interrupção rápida no erro: `.venv/bin/pytest -v -x`
   - ❌ Errado: `pytest tests/`
2. **Testes Unitários Rápidos**: Testes em `unit/` devem rodar em milissegundos. Isole dependências de disco e network usando o submódulo `unittest.mock` e `pytest.fixture`. NUNCA conecte o Kafka em um unit-test de Payload.
3. **Organização Arquitetural**:
   - `tests/unit/`: Lógica isolada, limpadores customizados, serializadores geográficos e calculadoras estáticas de matemática (índices).
   - `tests/integration/`: Integrações profundas com GeoPandas (operações I/O), Testes de Polimorfismo do `BaseETL` usando arquivos Parquet/CSV/GeoJSON locais (mockados).

## ⚙️ Diretrizes Operacionais para Agentes
- **Test-Driven Refactoring**: Ao modificar ou refatorar profundamente o comportamento de uma camada core (como fizemos trocando o `WKT` por `path_json` na `src.etl.utils.helpers`), execute IMEDIATAMENTE a suite de testes locais antes de considerar a refatoração concluída.
- **Edge-Cases Complexos**: Se você adicionar uma lógica matemática nova aos `calculators.py` ou expandir validações restritivas no Pydantic (`models.py`), você DEVE, de forma compulsória, desenhar e incluir um teste parametrizado correspondente testando inputs erráticos (NaN, Inf, Null, String Vazia).
- **Tratamento de Falhas**: Testes que falharem devem ser consertados logicamente no código da aplicação. **É categoricamente proibido** deletar um teste que falhou ou preenchê-lo com `pass` apenas para forçar o sucesso na esteira do console. Analise e entenda a raiz da divergência.

## 📝 Comentários em Testes
- Prefira nomes de teste descritivos: o nome deve explicar cenário, ação e expectativa.
- Use comentários apenas para cenários de dados não óbvios, como coordenada sentinela `(0, 0)`, outlier `-999`, CRS métrico ou payload Snowflake.
- Não comente asserts triviais. Se o teste precisa de muitas explicações, extraia fixtures/factories com nomes melhores.
- Para bugs de tratamento de dados, o comentário deve apontar a origem do caso real (INPE, ONS, CNES, Druid/Superset) quando conhecida.
