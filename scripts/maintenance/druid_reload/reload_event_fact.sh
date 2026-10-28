#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SPECS_DIR="$PROJECT_ROOT/infrastructure/druid/specs"
RESULTS_ROOT="$PROJECT_ROOT/data/results/ingestion/fato_eventos"

DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"
DRUID_COORDINATOR_URL="${DRUID_COORDINATOR_URL:-http://localhost:8081}"
DRUID_BROKER_SQL_URL="${DRUID_BROKER_SQL_URL:-http://localhost:8082/druid/../../..l}"

KAFKA_CONTAINER="${KAFKA_CONTAINER:-kafka}"
KAFKA_BOOTSTRAP_DOCKER="${KAFKA_BOOTSTRAP_DOCKER:-kafka:9092}"
KAFKA_BOOTSTRAP_HOST="${KAFKA_BROKER:-localhost:29092}"

DATASOURCE="${DATASOURCE:-fato_eventos_incendio}"
SUPERVISOR_ID="${SUPERVISOR_ID:-fato_eventos_incendio}"
TOPIC="${TOPICO_EVENTOS:-streaming_eventos_incendio}"
SPEC_PATH="$SPECS_DIR/fato_eventos_incendio.json"

RUN_PRODUCER=0
DRY_RUN=0
ASSUME_YES=0
MIN_TOTAL_FOCOS="${MIN_TOTAL_FOCOS:-3000000}"
CHUNK_SIZE_FOCOS="${CHUNK_SIZE_FOCOS:-50000}"
WAIT_TASK_MAX_ATTEMPTS="${WAIT_TASK_MAX_ATTEMPTS:-60}"
EVENTOS_MAX_DURATION_DAYS="${EVENTOS_MAX_DURATION_DAYS:-2.0}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$RESULTS_ROOT/$TIMESTAMP"

usage() {
  cat <<'EOF'
Uso:
  scripts/druid/reload_event_fact.sh [--run-producer] [--dry-run] [--yes]

Opcoes:
  --run-producer   Roda o produtor Python ate terminar o CSV bruto.
  --dry-run        Mostra acoes sem apagar topico/datasource nem enviar supervisor.
  --yes            Nao pede confirmacao interativa.

Variaveis uteis:
  MIN_TOTAL_FOCOS=3000000       Alvo minimo de SUM(total_focos) apos ingestao.
  CHUNK_SIZE_FOCOS=50000        Chunk usado pelo produtor.
  WAIT_TASK_MAX_ATTEMPTS=60      Tentativas de 5s para aguardar kill task.
  EVENTOS_MAX_DURATION_DAYS=2.0  Janela operacional para evitar DBSCAN gigante.
  TOPICO_EVENTOS=...            Topico Kafka da fato.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-producer) RUN_PRODUCER=1 ;;
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

confirmar() {
  if [[ "$DRY_RUN" -eq 1 || "$ASSUME_YES" -eq 1 ]]; then
    return
  fi
  echo "Este script apaga SOMENTE a fato $DATASOURCE e o topico Kafka $TOPIC."
  echo "As dimensoes batch permanecem intactas."
  read -r -p "Digite SIM para continuar: " confirmacao
  if [[ "$confirmacao" != "SIM" ]]; then
    echo "Operacao cancelada."
    exit 0
  fi
}

json_field() {
  local field="$1"
  python3 -c "import json,sys; print(json.load(sys.stdin).get('$field', ''))"
}

sql_query() {
  local query="$1"
  curl -fsS -X POST -H "Content-Type: application/json" \
    --data-binary "{\"query\":\"$query\"}" \
    "$DRUID_BROKER_SQL_URL"
}

task_status() {
  local task_id="$1"
  curl -fsS "$DRUID_OVERLORD_URL/druid/indexer/../../..sk/$task_id/status" |
    python3 -c "import json,sys; print(json.load(sys.stdin)['status']['status'])"
}

running_task_ids_for_datasource() {
  curl -fsS "$DRUID_OVERLORD_URL/druid/indexer/../../..nningTasks" |
    python3 -c "import json,sys; ds=sys.argv[1]; print('\n'.join(str(t.get('id')) for t in json.load(sys.stdin) if t.get('dataSource') == ds and str(t.get('type')) == 'index_kafka' and t.get('id')))" "$DATASOURCE"
}

wait_task() {
  local task_id="$1"
  echo "Aguardando task: $task_id"
  local tentativa=1
  while [[ "$tentativa" -le "$WAIT_TASK_MAX_ATTEMPTS" ]]; do
    local status
    status="$(task_status "$task_id")"
    echo "  tentativa=$tentativa/$WAIT_TASK_MAX_ATTEMPTS status=$status"
    case "$status" in
      SUCCESS) return 0 ;;
      FAILED|CANCELED) return 1 ;;
    esac
    tentativa=$((tentativa + 1))
    sleep 5
  done
  echo "Timeout aguardando task $task_id; a execucao seguira e a validacao final apontara residuos se existirem." >&2
  return 124
}

healthcheck() {
  echo "Verificando Druid e Kafka."
  run curl -fsS "$DRUID_OVERLORD_URL/status/health"
  echo "Coordinator/Overlord OK."
  if [[ "$DRY_RUN" -eq 0 ]]; then
    sql_query "SELECT 1 AS ok"
  else
    echo "+ SQL SELECT 1"
  fi
  echo "Broker SQL OK."
  run docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
    --list
  echo "Kafka OK."
  run python3 -m json.tool "$SPEC_PATH" >/dev/null
  echo "Spec da fato OK."
}

terminate_supervisor() {
  echo "Terminando supervisor, se existir: $SUPERVISOR_ID"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ curl -X POST $DRUID_OVERLORD_URL/druid/indexer/../../..pervisor/$SUPERVISOR_ID/terminate"
    return
  fi
  curl -fsS -X POST "$DRUID_OVERLORD_URL/druid/indexer/../../..pervisor/$SUPERVISOR_ID/terminate" >/dev/null 2>&1 || true
  sleep 5
}

reset_supervisor_offsets() {
  echo "Resetando metadados/offsets do supervisor, se existir: $SUPERVISOR_ID"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ curl -X POST $DRUID_OVERLORD_URL/druid/indexer/../../..pervisor/$SUPERVISOR_ID/reset"
    return
  fi

  # O Druid persiste offsets do supervisor no metadata store. Em replay limpo,
  # esse reset evita que um topico Kafka recriado em offset zero seja ignorado.
  curl -fsS -X POST "$DRUID_OVERLORD_URL/druid/indexer/../../..pervisor/$SUPERVISOR_ID/reset" >/dev/null 2>&1 || true
  sleep 5
}

shutdown_running_tasks() {
  echo "Encerrando tasks ativas da fato, se existirem."
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ list/shutdown running tasks for $DATASOURCE"
    return
  fi

  local task_ids
  task_ids="$(running_task_ids_for_datasource || true)"
  if [[ -z "$task_ids" ]]; then
    echo "Nenhuma task ativa da fato encontrada."
    return
  fi

  while IFS= read -r task_id; do
    [[ -z "$task_id" ]] && continue
    echo "Solicitando shutdown da task ativa: $task_id"
    curl -fsS -X POST "$DRUID_OVERLORD_URL/druid/indexer/../../..sk/$task_id/shutdown" >/dev/null 2>&1 || true
  done <<< "$task_ids"

  for _ in {1..30}; do
    task_ids="$(running_task_ids_for_datasource || true)"
    if [[ -z "$task_ids" ]]; then
      echo "Tasks ativas da fato encerradas."
      return
    fi
    echo "Ainda aguardando tasks ativas: $(echo "$task_ids" | tr '\n' ' ')"
    sleep 2
  done
  echo "Aviso: ainda ha task ativa da fato apos espera curta; o kill task pode demorar." >&2
}

reset_topic() {
  echo "Recriando topico Kafka: $TOPIC"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ docker exec $KAFKA_CONTAINER kafka-topics --delete --if-exists --topic $TOPIC"
    echo "+ docker exec $KAFKA_CONTAINER kafka-topics --create --if-not-exists --topic $TOPIC"
    return
  fi

  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
    --delete \
    --if-exists \
    --topic "$TOPIC" >/dev/null 2>&1 || true

  for _ in {1..30}; do
    if ! docker exec "$KAFKA_CONTAINER" kafka-topics \
      --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
      --describe \
      --topic "$TOPIC" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
    --create \
    --if-not-exists \
    --topic "$TOPIC" \
    --partitions 1 \
    --replication-factor 1
}

kill_datasource() {
  echo "Removendo datasource da fato: $DATASOURCE"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ curl -X DELETE $DRUID_COORDINATOR_URL/druid/coordinator/../../..tasources/$DATASOURCE"
    echo "+ submit kill task for $DATASOURCE"
    return
  fi

  curl -fsS -X DELETE "$DRUID_COORDINATOR_URL/druid/coordinator/../../..tasources/$DATASOURCE" >/dev/null 2>&1 || true
  local payload="{\"type\":\"kill\",\"dataSource\":\"$DATASOURCE\",\"interval\":\"1900-01-01/3000-01-01\"}"
  local resposta
  resposta="$(curl -fsS -X POST -H "Content-Type: application/json" --data-binary "$payload" "$DRUID_OVERLORD_URL/druid/indexer/../../..sk")"
  local task_id
  task_id="$(echo "$resposta" | json_field task)"
  if [[ -n "$task_id" ]]; then
    wait_task "$task_id" || true
  fi
}

create_supervisor() {
  echo "Criando supervisor Kafka da fato: $SUPERVISOR_ID"
  run curl -fsS -X POST -H "Content-Type: application/json" \
    --data-binary @"$SPEC_PATH" \
    "$DRUID_OVERLORD_URL/druid/indexer/../../..pervisor"
  echo
}

collect_state() {
  local prefix="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return
  fi
  mkdir -p "$OUT_DIR"
  curl -fsS "$DRUID_OVERLORD_URL/druid/indexer/../../..pervisor/$SUPERVISOR_ID/status" \
    > "$OUT_DIR/${prefix}_supervisor_status.json" || true
  docker exec "$KAFKA_CONTAINER" kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list "$KAFKA_BOOTSTRAP_DOCKER" \
    --topic "$TOPIC" \
    --time -1 > "$OUT_DIR/${prefix}_kafka_offsets.txt" || true
  sql_query "SELECT COUNT(*) AS eventos, SUM(total_focos) AS focos_representados, MIN(__time) AS min_time, MAX(__time) AS max_time FROM $DATASOURCE" \
    > "$OUT_DIR/${prefix}_druid_count.json" || true
}

run_producer() {
  if [[ "$RUN_PRODUCER" -eq 0 ]]; then
    echo "Produtor nao sera executado. Use --run-producer para processar o CSV bruto completo."
    return
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ uv run python -m pipelines.gold.src.streaming.produtor_eventos --progress-jsonl ... --progress-csv ..."
    return
  fi

  mkdir -p "$OUT_DIR"
  echo "Rodando produtor completo. Evidencias: $OUT_DIR"
  env \
    UV_CACHE_DIR=/tmp/uv-cache \
    CHUNK_SIZE_FOCOS="$CHUNK_SIZE_FOCOS" \
    EVENTOS_MAX_DURATION_DAYS="$EVENTOS_MAX_DURATION_DAYS" \
    KAFKA_BROKER="$KAFKA_BOOTSTRAP_HOST" \
    TOPICO_KAFKA_EVENTOS="$TOPIC" \
    uv run python -m pipelines.gold.src.streaming.produtor_eventos \
      --progress-jsonl "$OUT_DIR/progress.jsonl" \
      --progress-csv "$OUT_DIR/progress.csv" \
      2>&1 | tee "$OUT_DIR/produtor_eventos.log"
}

validate_final() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ validar COUNT, SUM(total_focos), lag e offsets"
    return
  fi
  mkdir -p "$OUT_DIR"
  collect_state "final"

  python3 - "$MIN_TOTAL_FOCOS" "$OUT_DIR/final_druid_count.json" <<'PY'
import json
import sys

min_total = float(sys.argv[1])
with open(sys.argv[2], encoding="utf-8") as fp:
    rows = json.load(fp)
row = rows[0] if rows else {}
eventos = int(row.get("eventos") or 0)
focos = float(row.get("focos_representados") or 0)
if eventos <= 0:
    raise SystemExit("Falha: fato_eventos_incendio nao retornou eventos.")
if focos < min_total:
    raise SystemExit(f"Falha: SUM(total_focos)={focos} abaixo do minimo esperado {min_total}.")
print(f"OK: eventos={eventos}, focos_representados={int(focos)}")
PY
}

cd "$PROJECT_ROOT"

confirmar
healthcheck
mkdir -p "$OUT_DIR"
reset_supervisor_offsets
terminate_supervisor
shutdown_running_tasks
reset_topic
kill_datasource
create_supervisor
collect_state "initial"
run_producer
validate_final

echo "Reload da fato de eventos concluido. Evidencias em: $OUT_DIR"
