#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SPECS_DIR="$PROJECT_ROOT/infrastructure/druid_specs"

DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"
DRUID_COORDINATOR_URL="${DRUID_COORDINATOR_URL:-http://localhost:8081}"
DRUID_BROKER_SQL_URL="${DRUID_BROKER_SQL_URL:-http://localhost:8082/druid/v2/sql}"

RUN_ETL=0
WITH_STREAMING=0
WITH_EVENTS=0
DRY_RUN=0
ASSUME_YES=0
KAFKA_CONTAINER="${KAFKA_CONTAINER:-kafka}"
KAFKA_BOOTSTRAP_DOCKER="${KAFKA_BOOTSTRAP_DOCKER:-kafka:9092}"
TOPICO_EVENTOS="${TOPICO_EVENTOS:-streaming_eventos_incendio}"

BATCH_SPECS=(
  "dim_municipios_coordenadas.json"
  "dim_hospitais_cnes.json"
  "dim_terras_indigenas_funai.json"
  "dim_rodovias_federais.json"
  "dim_ons_linhas_transmissao.json"
  "dim_ons_subestacoes.json"
  "dim_ons_sistemas_isolados.json"
)

BATCH_DATASOURCES=(
  "dim_municipios_coordenadas"
  "dim_hospitais_cnes"
  "dim_terras_indigenas"
  "dim_rodovias_federais"
  "dim_ons_linhas_transmissao"
  "dim_ons_subestacoes"
  "dim_ons_sistemas_isolados"
)

CLEANUP_DATASOURCES=(
  "fato_focos_incendio"
  "fato_eventos_incendio"
  "fogo_eventos_stdbscan"
  "dim_municipios_coordenadas"
  "dim_hospitais_cnes"
  "dim_terras_indigenas"
  "dim_rel_hospital_municipio"
  "dim_rel_terra_indigena_municipio"
  "dim_rel_hospital_terra_indigena"
  "dim_rodovias_federais"
  "dim_ons_linhas_transmissao"
  "dim_ons_subestacoes"
  "dim_ons_sistemas_isolados"
)

usage() {
  cat <<'EOF'
Uso:
  scripts/druid/reload_all.sh [--batch-only|--with-streaming|--with-events] [--run-etl] [--dry-run] [--yes]

Opcoes:
  --batch-only      Remove e reingere datasources batch. Padrao.
  --with-streaming  Tambem recria o supervisor Kafka legado de focos isolados.
  --with-events     Cria topico Kafka e supervisor da fato agregada de eventos.
  --run-etl         Regenera CSVs com uv antes da reingestao.
  --dry-run         Mostra as acoes sem executar.
  --yes             Nao pede confirmacao interativa.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --batch-only) WITH_STREAMING=0; WITH_EVENTS=0 ;;
    --with-streaming) WITH_STREAMING=1 ;;
    --with-events) WITH_EVENTS=1 ;;
    --run-etl) RUN_ETL=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --yes|-y) ASSUME_YES=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Opcao desconhecida: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

run() {
  echo "+ $*"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

curl_json() {
  local method="$1"
  local url="$2"
  local data="${3:-}"
  if [[ -n "$data" ]]; then
    curl -fsS -X "$method" -H "Content-Type: application/json" --data-binary "$data" "$url"
  else
    curl -fsS -X "$method" "$url"
  fi
}

json_field() {
  local field="$1"
  python3 -c "import json,sys; print(json.load(sys.stdin).get('$field', ''))"
}

task_status() {
  local task_id="$1"
  curl -fsS "$DRUID_OVERLORD_URL/druid/indexer/v1/task/$task_id/status" |
    python3 -c "import json,sys; print(json.load(sys.stdin)['status']['status'])"
}

wait_task() {
  local task_id="$1"
  echo "Aguardando task: $task_id"
  while true; do
    local status
    status="$(task_status "$task_id")"
    echo "  status=$status"
    case "$status" in
      SUCCESS) return 0 ;;
      FAILED|CANCELED) return 1 ;;
    esac
    sleep 5
  done
}

submit_task_file() {
  local spec_path="$1"
  local resposta
  resposta="$(curl -fsS -X POST -H "Content-Type: application/json" --data-binary @"$spec_path" "$DRUID_OVERLORD_URL/druid/indexer/v1/task")"
  echo "$resposta"
  echo "$resposta" | json_field task
}

submit_task_json() {
  local payload="$1"
  local resposta
  resposta="$(curl_json POST "$DRUID_OVERLORD_URL/druid/indexer/v1/task" "$payload")"
  echo "$resposta"
  echo "$resposta" | json_field task
}

confirmar() {
  if [[ "$DRY_RUN" -eq 1 || "$ASSUME_YES" -eq 1 ]]; then
    return
  fi
  echo "Este script vai remover datasources do Druid e reingestir os specs batch."
  echo "Nao remove volumes Docker nem arquivos locais."
  read -r -p "Digite SIM para continuar: " confirmacao
  if [[ "$confirmacao" != "SIM" ]]; then
    echo "Operacao cancelada."
    exit 0
  fi
}

healthcheck() {
  echo "Verificando Druid Coordinator/Overlord..."
  run curl -fsS "$DRUID_OVERLORD_URL/status/health" >/dev/null
  echo "Verificando Druid Broker SQL..."
  if [[ "$DRY_RUN" -eq 0 ]]; then
    curl -fsS -X POST -H "Content-Type: application/json" \
      --data-binary '{"query":"SELECT 1 AS ok"}' \
      "$DRUID_BROKER_SQL_URL" >/dev/null
  else
    echo "+ curl -fsS -X POST $DRUID_BROKER_SQL_URL"
  fi
}

run_etl() {
  if [[ "$RUN_ETL" -eq 1 ]]; then
    run env UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.etl.run_etl
  fi
}

validar_specs() {
  local specs=("${BATCH_SPECS[@]}")
  if [[ "$WITH_STREAMING" -eq 1 ]]; then
    specs+=("fato_focos_incendio.json")
  fi
  if [[ "$WITH_EVENTS" -eq 1 ]]; then
    specs+=("fato_eventos_incendio.json")
  fi
  for spec_name in "${specs[@]}"; do
    local spec_path="$SPECS_DIR/$spec_name"
    if [[ ! -f "$spec_path" ]]; then
      echo "Spec nao encontrado: $spec_path" >&2
      exit 1
    fi
    run python3 -m json.tool "$spec_path" >/dev/null
  done
}

terminar_supervisor() {
  local supervisor="$1"
  echo "Terminando supervisor Kafka, se existir: $supervisor"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ curl -X POST $DRUID_OVERLORD_URL/druid/indexer/v1/supervisor/$supervisor/terminate"
    return
  fi
  curl -fsS -X POST "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor/$supervisor/terminate" >/dev/null 2>&1 || true
}

remover_datasource() {
  local datasource="$1"
  echo "Removendo datasource: $datasource"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ curl -X DELETE $DRUID_COORDINATOR_URL/druid/coordinator/v1/datasources/$datasource"
    echo "+ submit kill task for $datasource"
    return
  fi

  curl -fsS -X DELETE "$DRUID_COORDINATOR_URL/druid/coordinator/v1/datasources/$datasource" >/dev/null 2>&1 || true

  local payload
  payload="{\"type\":\"kill\",\"dataSource\":\"$datasource\",\"interval\":\"1900-01-01/3000-01-01\"}"
  local task_id
  task_id="$(submit_task_json "$payload" | tail -n 1 || true)"
  if [[ -n "$task_id" ]]; then
    wait_task "$task_id" || true
  fi
}

remover_datasources() {
  terminar_supervisor "fato_focos_incendio"
  terminar_supervisor "fato_eventos_incendio"
  for datasource in "${CLEANUP_DATASOURCES[@]}"; do
    remover_datasource "$datasource"
  done
}

ingestir_batch() {
  for spec_name in "${BATCH_SPECS[@]}"; do
    local spec_path="$SPECS_DIR/$spec_name"
    echo "Enviando spec batch: $spec_name"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "+ curl -X POST --data-binary @$spec_path $DRUID_OVERLORD_URL/druid/indexer/v1/task"
      continue
    fi
    local task_id
    task_id="$(submit_task_file "$spec_path" | tail -n 1)"
    wait_task "$task_id"
  done
}

recriar_streaming() {
  if [[ "$WITH_STREAMING" -eq 0 ]]; then
    echo "Supervisor legado de focos isolados nao sera recriado. Use --with-streaming para habilitar."
    return
  fi
  local spec_path="$SPECS_DIR/fato_focos_incendio.json"
  echo "Recriando supervisor Kafka legado de focos isolados."
  run curl -fsS -X POST -H "Content-Type: application/json" --data-binary @"$spec_path" "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor"
}

criar_topico_eventos() {
  if [[ "$WITH_EVENTS" -eq 0 ]]; then
    return
  fi
  echo "Garantindo topico Kafka de eventos: $TOPICO_EVENTOS"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA_BOOTSTRAP_DOCKER --create --if-not-exists --topic $TOPICO_EVENTOS --partitions 1 --replication-factor 1"
    return
  fi
  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
    --create \
    --if-not-exists \
    --topic "$TOPICO_EVENTOS" \
    --partitions 1 \
    --replication-factor 1
}

recriar_eventos() {
  if [[ "$WITH_EVENTS" -eq 0 ]]; then
    echo "Supervisor de eventos nao sera recriado. Use --with-events para habilitar."
    return
  fi
  local spec_path="$SPECS_DIR/fato_eventos_incendio.json"
  echo "Recriando supervisor Kafka da fato agregada de eventos."
  run curl -fsS -X POST -H "Content-Type: application/json" --data-binary @"$spec_path" "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor"
}

conferir() {
  echo "Loadstatus:"
  run curl -fsS "$DRUID_COORDINATOR_URL/druid/coordinator/v1/loadstatus"
  echo
  for datasource in "${BATCH_DATASOURCES[@]}"; do
    echo "COUNT $datasource"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "+ SQL COUNT $datasource"
      continue
    fi
    curl -fsS -X POST -H "Content-Type: application/json" \
      --data-binary "{\"query\":\"SELECT COUNT(*) AS total FROM $datasource\"}" \
      "$DRUID_BROKER_SQL_URL" || true
    echo
  done
}

cd "$PROJECT_ROOT"

confirmar
healthcheck
run_etl
validar_specs
remover_datasources
ingestir_batch
criar_topico_eventos
recriar_streaming
recriar_eventos
conferir

echo "Recarga Druid concluida."
