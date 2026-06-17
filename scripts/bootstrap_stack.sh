#!/usr/bin/env bash
set -euo pipefail

# ==================================================
# Bootstrap completo do ambiente DataOps
# ==================================================
# Faz:
# - docker compose down -v
# - sobe somente os containers necessários
# - cria tópico Kafka
# - envia tasks batch das dimensões para o Druid
# - cria supervisor Kafka da fato
#
# Não faz:
# - não executa produtor_focos.py
# - não sobe router, para poupar recursos
# ==================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPECS_DIR="$PROJECT_ROOT/infrastructure/druid_specs"

KAFKA_CONTAINER="kafka"
KAFKA_BOOTSTRAP_DOCKER="kafka:9092"
TOPICO_KAFKA="streaming_focos_incendio"

# No seu compose, o Coordinator também atua como Overlord.
# Portanto a API de tasks/supervisors fica em localhost:8081.
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"

SERVICOS_NECESSARIOS=(
  zookeeper-kafka
  kafka
  zookeeper
  postgres
  coordinator
  middlemanager
  broker
  historical
  superset
)

echo "=================================================="
echo "⚠️  RESET DE AMBIENTE DOCKER"
echo "=================================================="
echo "Este script vai derrubar containers e apagar volumes."
echo "Dados antigos do Druid/Kafka serão removidos."
echo
echo "Serviços que serão iniciados:"
printf ' - %s\n' "${SERVICOS_NECESSARIOS[@]}"
echo
echo "Observação: o serviço router NÃO será iniciado para poupar recursos."
echo

read -p "Digite SIM para continuar: " CONFIRMACAO

if [[ "$CONFIRMACAO" != "SIM" ]]; then
  echo "Operação cancelada."
  exit 0
fi

cd "$PROJECT_ROOT"

echo
echo "=================================================="
echo "1. Derrubando containers e removendo volumes"
echo "=================================================="

docker compose down -v --remove-orphans

echo
echo "=================================================="
echo "2. Subindo somente os serviços necessários"
echo "=================================================="

docker compose up -d --build "${SERVICOS_NECESSARIOS[@]}"

echo
echo "=================================================="
echo "3. Aguardando Kafka"
echo "=================================================="

until docker exec "$KAFKA_CONTAINER" kafka-topics \
  --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
  --list >/dev/null 2>&1; do
  echo "⏳ Kafka ainda não está pronto..."
  sleep 5
done

echo "✅ Kafka pronto."

echo
echo "=================================================="
echo "4. Criando tópico Kafka"
echo "=================================================="

docker exec "$KAFKA_CONTAINER" kafka-topics \
  --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
  --create \
  --if-not-exists \
  --topic "$TOPICO_KAFKA" \
  --partitions 1 \
  --replication-factor 1

echo "✅ Tópico '$TOPICO_KAFKA' pronto."

echo
echo "=================================================="
echo "5. Aguardando Druid Coordinator/Overlord"
echo "=================================================="

echo "🔎 Testando endpoint: $DRUID_OVERLORD_URL/status/health"

until curl -fs "$DRUID_OVERLORD_URL/status/health" >/dev/null 2>&1; do
  echo "⏳ Druid ainda não está pronto em $DRUID_OVERLORD_URL..."
  sleep 5
done

echo "✅ Druid Coordinator/Overlord respondeu healthcheck."

echo
echo "🔎 Aguardando API de tasks do Overlord..."

until curl -fs "$DRUID_OVERLORD_URL/druid/indexer/v1/tasks" >/dev/null 2>&1; do
  echo "⏳ API de tasks ainda não está pronta..."
  sleep 5
done

echo "✅ API de tasks pronta."

echo
echo "🔎 Aguardando API de supervisors..."

until curl -fs "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor" >/dev/null 2>&1; do
  echo "⏳ API de supervisors ainda não está pronta..."
  sleep 5
done

echo "✅ API de supervisors pronta."

echo
echo "=================================================="
echo "6. Validando JSONs dos specs"
echo "=================================================="

for spec in "$SPECS_DIR"/*.json; do
  echo "🔎 Validando: $(basename "$spec")"
  python3 -m json.tool "$spec" >/dev/null
done

echo "✅ Todos os JSONs são válidos."

echo
echo "=================================================="
echo "7. Enviando tasks batch das dimensões"
echo "=================================================="

DIM_SPECS=(
  "dim_municipios_coordenadas.json"
  "dim_hospitais_cnes.json"
  "dim_terras_indigenas_funai.json"
  "dim_rodovias_federais.json"
  "dim_ons_linhas_transmissao.json"
  "dim_ons_subestacoes.json"
  "dim_ons_sistemas_isolados.json"
)

for spec_name in "${DIM_SPECS[@]}"; do
  spec_path="$SPECS_DIR/$spec_name"

  if [[ ! -f "$spec_path" ]]; then
    echo "⚠️ Spec não encontrado: $spec_path"
    continue
  fi

  echo "📤 Enviando task: $spec_name"

  RESPOSTA=$(curl -fs -X POST \
    -H "Content-Type: application/json" \
    --data-binary @"$spec_path" \
    "$DRUID_OVERLORD_URL/druid/indexer/v1/task")

  echo "✅ Task enviada: $spec_name"
  echo "   Resposta: $RESPOSTA"
done

echo
echo "=================================================="
echo "8. Criando supervisor Kafka da fato"
echo "=================================================="

FATO_SPEC="$SPECS_DIR/fato_focos_incendio.json"

if [[ ! -f "$FATO_SPEC" ]]; then
  echo "❌ Spec da fato não encontrado: $FATO_SPEC"
  exit 1
fi

RESPOSTA_SUPERVISOR=$(curl -fs -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"$FATO_SPEC" \
  "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor")

echo "✅ Supervisor da fato criado."
echo "   Resposta: $RESPOSTA_SUPERVISOR"

echo
echo "=================================================="
echo "9. Conferência"
echo "=================================================="

echo
echo "📌 Containers ativos:"
docker compose ps

echo
echo "📌 Tópicos Kafka:"
docker exec "$KAFKA_CONTAINER" kafka-topics \
  --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
  --list

echo
echo "📌 Supervisors Druid:"
curl -s "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor" | python3 -m json.tool || true

echo
echo "📌 Tasks Druid:"
curl -s "$DRUID_OVERLORD_URL/druid/indexer/v1/tasks" | python3 -m json.tool | head -n 120 || true

echo
echo "=================================================="
echo "✅ Bootstrap finalizado."
echo "=================================================="
echo
echo "A ingestão Python NÃO foi iniciada."
echo
echo "Quando quiser iniciar a ingestão:"
echo "source venv/bin/activate"
echo "python3 src/streaming/produtor_focos.py"
echo