#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE_DIR="$PROJECT_ROOT/infrastructure/druid_profiles"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
OUT_ROOT="$PROJECT_ROOT/data/results/performance/druid_capacity/$RUN_ID"
BENCH_PROFILE="${BENCH_PROFILE:-baseline}"
BROKER_SQL_URL="${DRUID_BROKER_SQL_URL:-http://localhost:8082/druid/v2/sql}"
COORDINATOR_URL="${DRUID_COORDINATOR_URL:-http://localhost:8081}"
FINAL_PROFILE="$PROFILE_DIR/scenario_02_balanced.env"

SCENARIOS=(
  "scenario_01_baseline"
  "scenario_02_balanced"
  "scenario_03_query_heavy"
)

cd "$PROJECT_ROOT"

compose_profile() {
  local profile_file="$1"
  docker compose --env-file "$profile_file" "$@"
}

wait_broker() {
  echo "Aguardando Broker SQL..."
  for _ in $(seq 1 90); do
    if curl -fsS -X POST -H "Content-Type: application/json" \
      --data-binary '{"query":"SELECT 1 AS ok"}' \
      "$BROKER_SQL_URL" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Broker SQL nao respondeu a tempo." >&2
  return 1
}

wait_loadstatus() {
  echo "Aguardando loadstatus=100..."
  for _ in $(seq 1 120); do
    if curl -fsS "$COORDINATOR_URL/druid/coordinator/v1/loadstatus" |
      python3 -c 'import json,sys; data=json.load(sys.stdin); sys.exit(0 if data and all(float(v) >= 100 for v in data.values()) else 1)' >/dev/null 2>&1; then
      return 0
    fi
    sleep 3
  done
  echo "Segmentos nao chegaram a loadstatus=100 a tempo." >&2
  return 1
}

apply_profile() {
  local scenario="$1"
  local profile_file="$PROFILE_DIR/$scenario.env"
  echo "Aplicando perfil: $scenario"
  docker compose --env-file "$profile_file" up -d --force-recreate broker historical
  wait_broker
  wait_loadstatus
}

restore_balanced() {
  echo "Restaurando perfil final Balanced..."
  docker compose --env-file "$FINAL_PROFILE" up -d --force-recreate broker historical >/dev/null
  wait_broker >/dev/null
  wait_loadstatus >/dev/null
  echo "Perfil Balanced ativo."
}

trap restore_balanced EXIT

mkdir -p "$OUT_ROOT"

for scenario in "${SCENARIOS[@]}"; do
  apply_profile "$scenario"
  echo "Rodando benchmark para $scenario"
  DRUID_CAPACITY_SCENARIO="$scenario" UV_CACHE_DIR=/tmp/uv-cache \
    uv run python scripts/performance/run_druid_benchmark.py \
      --profile "$BENCH_PROFILE" \
      --capacity-scenario "$scenario" \
      --broker-url "$BROKER_SQL_URL" \
      --coordinator-url "$COORDINATOR_URL" \
      --collect-docker \
      --out-root "$OUT_ROOT" \
      --run-id "$scenario"
done

UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/performance/compare_capacity_results.py \
  --matrix-dir "$OUT_ROOT"

trap - EXIT
restore_balanced

echo "Matriz concluida em: $OUT_ROOT"
