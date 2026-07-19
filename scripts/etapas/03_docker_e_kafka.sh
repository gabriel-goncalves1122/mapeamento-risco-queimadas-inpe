#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

KAFKA_CONTAINER="kafka"
KAFKA_BOOTSTRAP_DOCKER="kafka:9092"
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"

TOPICOS=(
  "streaming_focos_incendio"
  "streaming_eventos_incendio"
)

SERVICOS=(
  zookeeper-kafka
  kafka
  zookeeper
  postgres
  coordinator
  middlemanager
  broker
  historical
)

echo "=================================================="
echo "🐳 Etapa 3: Docker + Kafka"
echo "=================================================="

echo "📦 Subindo containers..."
docker compose up -d --build "${SERVICOS[@]}"

echo
echo "⏳ Aguardando Kafka..."
until docker exec "$KAFKA_CONTAINER" kafka-topics \
  --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
  --list >/dev/null 2>&1; do
  echo "  ⏳ Kafka ainda não está pronto..."
  sleep 5
done
echo "✅ Kafka pronto."

echo
echo "📋 Criando tópicos Kafka..."
for TOPICO in "${TOPICOS[@]}"; do
  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server "$KAFKA_BOOTSTRAP_DOCKER" \
    --create \
    --if-not-exists \
    --topic "$TOPICO" \
    --partitions 1 \
    --replication-factor 1
  echo "  ✅ Tópico '$TOPICO' pronto."
done

echo
echo "⏳ Aguardando Druid Coordinator/Overlord..."
until curl -fs "$DRUID_OVERLORD_URL/status/health" >/dev/null 2>&1; do
  echo "  ⏳ Druid ainda não está pronto..."
  sleep 5
done
echo "✅ Druid Coordinator/Overlord pronto."

echo
echo "⏳ Aguardando API de tasks do Druid..."
until curl -fs "$DRUID_OVERLORD_URL/druid/indexer/v1/tasks" >/dev/null 2>&1; do
  echo "  ⏳ API de tasks ainda não está pronta..."
  sleep 5
done
echo "✅ API de tasks pronta."

echo
echo "✅ Etapa 3 concluída: Docker e Kafka operacionais."
