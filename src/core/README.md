# Núcleo Compartilhado (`src/core/`) - CCO DataOps

O pacote `src/core/` centraliza o **coração compartilhado** da aplicação: interfaces de contratos abstratos (POO/SOLID), modelos Pydantic imutáveis de domínio analítico e gerenciamento de configurações/constantes do ecossistema.

Este módulo é deliberadamente livre de dependências das camadas de negócio superiores (Bronze, Silver, Gold ou Orchestration). Todas as camadas dependem de `src/core/`, mas `src/core/` **nunca** depende de nenhuma camada de negócio (Princípio da Inversão de Dependência - DIP).

---

## 🏗️ 1. Estrutura de Diretórios

```text
src/core/
├── README.md              # Este guia do núcleo compartilhado
├── contracts/             # Interfaces abstratas e Protocolos de comportamento (SOLID)
│   ├── contracts.py       # ExecutablePipelineStep, SpatialEngineProtocol, StreamPublisherBase, DataValidatorBase
│   └── __init__.py
├── domain/                # Modelos Pydantic v2 estritos e imutáveis das bordas do sistema
│   ├── foco_fato_payload.py    # Contrato imutável de focos orbitais unitários (FATO_FOCOS_INCENDIO)
│   ├── evento_fato_payload.py  # Contrato imutável de eventos complexos ST-DBSCAN (FATO_EVENTOS_INCENDIO)
│   ├── models.py               # Façade reexportando os payloads com compatibilidade retroativa
│   └── __init__.py
├── config/                # Governança de ambiente e constantes canônicas de projeto
│   ├── constants.py       # Diretórios absolutos (DIMENSIONS_DIR, RAW_DIR), CRS padrão e tolerâncias
│   ├── settings.py        # PipelineSettings baseada em Pydantic Settings (.env e variáveis de ambiente)
│   └── __init__.py
└── tests/                 # Testes unitários co-localizados do núcleo
    └── unit/
        └── test_core_contracts.py  # Validação de imutabilidade, contratos abstratos e serialização
```

---

## 📜 2. Contratos Abstratos e Protocolos (`src/core/contracts/`)

As abstrações contidas em [`contracts.py`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/contracts/contracts.py) definem as fronteiras de software do ecossistema:

### 2.1 `ExecutablePipelineStep[TResult]` (Template Method & Telemetria)
Classe base genérica abstrata para etapas operacionais de pipeline:
* **Template Method**: O método público `execute(*args, **kwargs)` centraliza cronometragem de alta precisão via `time.perf_counter()`, captura de telemetria e logging estruturado com nível de alerta.
* **Gancho Protegido**: Subclasses implementam estritamente o método abstrato `_run(*args, **kwargs) -> TResult`.
* **Polimorfismo (LSP)**: Tanto extratores da Bronze, dimensões da Silver, modelos de grafos da Gold e orquestradores Dagster compartilham a mesma assinatura de execução.

```python
class ExecutablePipelineStep(ABC, Generic[TResult]):
    @property
    def step_name(self) -> str:
        return self.__class__.__name__

    def execute(self, *args: Any, **kwargs: Any) -> TResult:
        # Inicia medição determinística de latência
        t0 = time.perf_counter()
        resultado = self._run(*args, **kwargs)
        duracao_ms = (time.perf_counter() - t0) * 1000.0
        # Logging de telemetria uniforme
        return resultado

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> TResult:
        """Lógica de negócio pura implementada pela subclasse."""
```

### 2.2 `SpatialEngineProtocol` (DIP & Interface Segregation)
Protocolo estrutural decorado com `@runtime_checkable` (`typing.Protocol`):
* Expõe aos produtores da Camada Gold exclusivamente os métodos de consulta (`analisar_todas_ameacas` e `intersecoes_camada`).
* Permite injetar nos testes unitários mocks rápidos em memória sem carregar instâncias físicas pesadas de GeoDataFrames e STRtrees do disco.

### 2.3 `StreamPublisherBase` (Context Manager para Redes)
Classe abstrata para publicadores de mensageria:
* Implementa o protocolo *Context Manager* (`__enter__` e `__exit__`).
* Garante a execução obrigatória de `flush_and_close()` mesmo diante de exceções de rede ou interrupções abruptas do processo, impedindo perda de mensagens no buffer do Kafka.

### 2.4 `DataValidatorBase` & `ValidationReport`
Contrato para validadores de qualidade de dados (QA):
* Define o método `validate() -> ValidationReport`.
* `ValidationReport` é um dataclass imutável (`@dataclass(frozen=True)`) com estatísticas de linhas validadas, falhas encontradas e detalhamento de discrepâncias.

---

## 🔒 3. Contratos de Domínio Imutáveis (`src/core/domain/`)

Os modelos de domínio implementam rigor absoluto nas **bordas do sistema** (Streaming Kafka -> Apache Druid), aplicando os princípios da modelagem **Snowflake**:

### 3.1 Imutabilidade e Veto Estrito (`ConfigDict(frozen=True, extra="forbid")`)
Tanto [`FocoFatoPayload`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/domain/foco_fato_payload.py) quanto [`EventoFatoPayload`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/domain/evento_fato_payload.py) impõem:
* `frozen=True`: Imutabilidade total. Tentativas de alterar campos após a criação lançam `ValidationError`.
* `extra="forbid"`: Rejeição sumária de qualquer campo não mapeado no contrato.
* **Validação Numérica Rígida**: Proibição de valores `NaN`, `+Inf` ou `-Inf`, que corromperiam o parser JSON do Apache Druid.

### 3.2 Princípio Snowflake: Zero Strings Redundantes na Fato
Os payloads de streaming contêm **exclusivamente**:
1. **Chaves Temporais e Primárias**: `data_hora` (`__time`), `id_foco_orbital`, `fire_event_id`.
2. **Chaves Estrangeiras (FKs)**: `fk_municipio_ibge`, `fk_linha_transmissao`, `fk_subestacao`, `fk_terra_indigena`, `fk_hospital_cnes`, `fk_rodovia_federal`.
3. **Métricas Numéricas**: `frp`, `risco_fogo`, `precipitacao_mm`, `distancia_*_km`, `area_mancha_km2`, `indice_*`.
4. **Geometrias Serializadas Compactas**: `path_json` (coordenadas para renderização Deck.gl).

> Nomes de municípios, siglas de concessionárias, etnias de TIs e descrições hospitalares **não trafegam** pelo Kafka. São resolvidos em $O(1)$ via *Lookups* em memória RAM no Druid.

---

## ⚙️ 4. Configurações e Constantes (`src/core/config/`)

* [`constants.py`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/config/constants.py):
  * Caminhos canônicos absolutos (`PROJECT_ROOT`, `DIMENSIONS_DIR`, `RAW_DIR`, `GOLD_DIR`).
  * Sistemas de Coordenadas: `CRS_SIRGAS_2000_POLICONICA = "EPSG:5880"` e `CRS_WGS84 = "EPSG:4326"`.
  * Tolerâncias espaciais padrão (buffers em km para linhas, subestações, rodovias e terras indígenas).
* [`settings.py`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/config/settings.py):
  * `PipelineSettings`: Carregador dinâmico de variáveis de ambiente (`.env`), permitindo ajuste de hiperparâmetros de Machine Learning (`EVENTOS_EPS_KM`, `EVENTOS_EPS_DIAS`, `EVENTOS_MIN_SAMPLES`) e parâmetros de rede do Kafka sem alteração de código.

---

## 🧪 5. Execução dos Testes Co-localizados

Para testar o núcleo isoladamente:
```bash
uv run pytest src/core/tests/unit/test_core_contracts.py -v
```
São validadas imutabilidade de payloads, proibição de campos extras, medição determinística de tempo em `ExecutablePipelineStep` e conformidade com protocolos de mensageria.
