#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

SPECS_DIR="$PROJECT_ROOT/infrastructure/druid_specs"
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"

echo "=================================================="
echo "🔥 Etapa 5: Streaming de Eventos"
echo "=================================================="

echo "📋 Criando supervisor Kafka da fato de eventos no Druid..."
FATO_SPEC="$SPECS_DIR/fato_eventos_incendio.json"

if [[ ! -f "$FATO_SPEC" ]]; then
  echo "❌ Spec da fato de eventos não encontrado: $FATO_SPEC"
  exit 1
fi

RESPOSTA=$(curl -fs -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"$FATO_SPEC" \
  "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor")

echo "✅ Supervisor da fato de eventos criado."

echo
echo "🚀 Iniciando produtor de eventos..."
echo "   (Ctrl+C para parar o streaming)"
echo

uv run python -m src.streaming.produtor_eventos
