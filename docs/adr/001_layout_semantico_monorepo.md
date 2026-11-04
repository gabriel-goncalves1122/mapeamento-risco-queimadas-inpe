# ADR 001: Layout Semântico Desacoplado no Monorepo Python

* **Status:** Aprovado
* **Data:** 2026-11-03
* **Decisores:** Engenharia de Dados CCO-DataOps

---

## 1. Contexto

Historicamente, o repositório possuía uma estrutura fragmentada originada de protótipos procedurais:
* Códigos das etapas conviviam em `pipelines/bronze`, `pipelines/silver` e `pipelines/gold`.
* Havia redundância de subpastas (como `pipelines/silver/src/etl_dimensions/`).
* Configurações estavam soltas na raiz em `config/`.
* Módulos de infraestrutura Docker e testes estavam em `infrastructure/`.
* Scripts utilitários tinham nomes genéricos como `scripts/etapas/` e `scripts/performance/`.

Essa distribuição gerava ambiguidades de importação (`ModuleNotFoundError`), inconsistência em caminhos relativos ao executar scripts via CLI ou Dagster e dificuldade de isolamento de testes unitários.

---

## 2. Decisão

Adotamos a padronização **Semantic Root-Clean Layout** para o monorepo Python:

1. **Raiz Única de Aplicação (`src/`)**:
   - Todo código Python executável de negócio reside sob `src/`.
   - Divisão semântica por camadas Medallion: `src/core/` (contratos e configurações), `src/bronze/` (ingestão bruta), `src/silver/` (dimensões conformadas), `src/gold/` (ciência e streaming) e `src/orchestration/` (DAG de assets Dagster).
2. **Co-locação de Testes e Dados Locais**:
   - Cada camada abriga seus testes unitários em `src/<camada>/tests/` e dados locais em `src/<camada>/data/`.
3. **Isolamento de Infraestrutura e Ferramental**:
   - Serviços conteinerizados migraram para `infra/` (`infra/druid/`, `infra/superset/`).
   - Scripts de linha de comando foram reorganizados por finalidade em `scripts/run/`, `scripts/benchmarks/`, `scripts/maintenance/` e `scripts/setup/`.
4. **Convenção Explícita de Importação**:
   - Proibição de imports relativos ambíguos. Todos os módulos utilizam imports absolutos iniciados pelo pacote raiz: `from src.core...`, `from src.silver...`, `from src.gold...`.

---

## 3. Consequências

### Positivas
* **Previsibilidade e Legibilidade**: Clareza imediata sobre a responsabilidade de cada diretório.
* **Descoberta Determinística de Testes**: O `pytest` varre caminhos modulares (`testpaths = src/core/tests, src/bronze/tests, ...`) sem colisões de nomes de arquivos.
* **Compatibilidade com Astral `uv`**: Resolução uniforme de pacotes tanto em desenvolvimento local quanto em contêineres Docker.

### Negativas / Trade-offs
* Necessidade de ajustar caminhos montados em volumes do Docker Compose (`./src/silver/data` e `./src/gold/data`).
