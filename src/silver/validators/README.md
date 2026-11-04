# Validadores de Qualidade e Integridade de Dados (`src/silver/validators/`)

Este diretório contém os componentes de **Data Quality (QA)** e integridade referencial da Camada Silver. 

Na arquitetura **Medallion**, a Camada Silver tem como compromisso fornecer dados higienizados e confiáveis para o modelo analítico Snowflake. Os validadores asseguram que as dimensões espaciais estejam estritamente conformadas antes de serem promovidas para *Lookups* no Apache Druid ou consumidas pela Camada Gold.

---

## 🏗️ 1. Componentes Disponíveis

```text
src/silver/validators/
├── README.md                              # Este guia de governança e validação
├── dimensao_integridade_validator.py      # Validador universal de completude e tipagem de dimensões
└── valida_joins_municipios_hospital.py    # Validador de integridade referencial CNES vs IBGE
```

---

## 🔍 2. Componentes em Detalhes

### 2.1 `DimensaoIntegridadeValidator` (Validação Estrutural Universal)
Implementado em [`dimensao_integridade_validator.py`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/silver/validators/dimensao_integridade_validator.py), herda do contrato base [`DataValidatorBase`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/contracts/contracts.py) e valida as seguintes invariantes em qualquer tabela dimensional:

1. **Unicidade de Chave Primária**: Rejeita duplicatas no campo `primary_key`.
2. **Não-Nulidade Crítica**: Exige 0% de valores nulos (`NaN` ou `None`) na chave primária e nas coordenadas essenciais (`latitude`, `longitude`).
3. **Consistência Geodésica**: Assegura que latitudes estejam no intervalo $[-35.0, 6.0]$ e longitudes no intervalo $[-75.0, -30.0]$ (envoltória do território brasileiro).
4. **Validade de `path_json`**: Confirma que as strings de geometria serializada sejam JSONs válidos decodificáveis.

Retorna uma instância imutável de [`ValidationReport`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/core/contracts/contracts.py):
```python
@dataclass(frozen=True)
class ValidationReport:
    validador_nome: str
    total_registros: int
    total_falhas: int
    erros: list[str]
    sucesso: bool
```

### 2.2 `ValidaJoinsMunicipiosHospital` (Integridade Referencial Cruzada)
Implementado em [`valida_joins_municipios_hospital.py`](file:///c:/Users/SEPLAN/Documents/UNIFEI/UNIVERSIDADE/mapeamento-risco-queimadas-inpe/src/silver/validators/valida_joins_municipios_hospital.py), valida o acoplamento entre os estabelecimentos de saúde do CNES/DATASUS e os 5.564 municípios oficiais do IBGE:

* **Integridade de Chave Estrangeira**: Verifica se todo `codigo_ibge` presente em `dim_hospitais_cnes.csv` existe em `dim_municipios_coordenadas.csv`.
* **Detecção de Órfãos**: Isola registros hospitalares sem município gestor ou com códigos antigos descontinuados pelo IBGE.
* **Consistência Espacial**: Confirma se a coordenada geográfica do hospital cai dentro do polígono do município atribuído (ou tolerância de borda de 5 km).

---

## 🚀 3. Execução dos Validadores via Linha de Comando (CLI)

Os validadores podem ser executados isoladamente durante o desenvolvimento:

```bash
# Validar integridade referencial Hospitais vs Municípios
uv run python src/silver/validators/valida_joins_municipios_hospital.py

# Validar integridade de todas as dimensões via pytest
uv run pytest src/silver/tests/unit/test_dimension_integrity_validator.py -v
```
