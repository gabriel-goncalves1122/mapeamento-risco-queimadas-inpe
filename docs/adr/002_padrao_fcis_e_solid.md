# ADR 002: Padrão FCIS (Functional Core, Imperative/OO Shell) e Princípios SOLID

* **Status:** Aprovado
* **Data:** 2026-11-04
* **Decisores:** Engenharia de Dados CCO-DataOps

---

## 1. Contexto

Durante a evolução da base de código em direção à Orientação a Objetos (POO), identificou-se o surgimento de classes puramente utilitárias com métodos estáticos (como `FogoCalculators` e `FogoExtractor`). Essa prática, conhecida na literatura como anti-padrão *"Stop Writing Classes"* ou "Javaficação do Python", introduz complexidade acidental:
* Instanciação e aninhamento de classes artificiais para operações matemáticas elementares (cálculo de índices de ameaça, parsing de floats e sanitização de texto).
* Dificuldade de vetorização de colunas em DataFrames Polars/Pandas.
* Overhead desnecessário em testes unitários.

Por outro lado, o gerenciamento de conexões de mensageria com o Kafka, a carga de índices espaciais em memória e o ciclo de vida dos Assets no Dagster exigem gerenciamento real de estado e ciclo de vida.

---

## 2. Decisão

Adotamos formalmente a arquitetura **Functional Core, Imperative/OO Shell (FCIS)** combinada com os princípios **SOLID**:

### 2.1 Núcleo Funcional (Functional Core)
* Toda transformação, sanitização, cálculo matemático ou feature engineering é implementada como **função pura e sem estado** (`Data In -> Data Out`, `DataFrame -> DataFrame`).
* Proibição expressa de criar classes cuja única finalidade seja agrupar funções estáticas. O próprio módulo `.py` atua como namespace.
* Funções puras são testáveis em milissegundos sem necessidade de mocks de rede ou banco de dados.

### 2.2 Casca Orientada a Objetos (OO Shell)
* A Programação Orientada a Objetos e princípios SOLID são aplicados **exclusivamente** onde há gestão de ciclo de vida e estado mutável:
  1. **Conexões de Rede e Buffers**: `StreamPublisherBase` e `KafkaEventProducer` gerenciados obrigatoriamente via *Context Managers* (`__enter__` e `__exit__`) para flush determinístico.
  2. **Estruturas Pesadas em Memória**: `MotorEspacial` (cache de árvores espaciais STRtree) para consultas $O(\log N)$.
  3. **Orquestração e Telemetria**: `ExecutablePipelineStep[TResult]` (Template Method com cronometragem nativa e logging).
* **Injeção de Dependências (DIP)**: Classes de infraestrutura recebem clientes e protocolos no construtor, permitindo testes com mocks em memória.

### 2.3 Rigor nas Bordas e Imutabilidade
* Contratos Pydantic de borda (`FocoFatoPayload` e `EventoFatoPayload`) configurados com `ConfigDict(frozen=True, extra="forbid")`.

---

## 3. Consequências

### Positivas
* **Manutenibilidade Extrema**: O código de negócio torna-se modular, direto e legível.
* **Velocidade de Execução**: Vetorização sem atrito em DataFrames.
* **Cobertura de Testes**: Mais de 112 testes unitários executam em $< 30$ segundos no pytest.

### Negativas / Trade-offs
* Exige dos desenvolvedores disciplina para discernir quando utilizar funções puras (transformação de dados) e quando empregar classes (gestão de conexões e orquestração).
