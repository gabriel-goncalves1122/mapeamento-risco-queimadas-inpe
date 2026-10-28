#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

SPECS_DIR="$PROJECT_ROOT/infrastructure/druid/specs"
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"

echo "=================================================="
echo "🔥 Etapa 5: Streaming de Eventos"
echo "=================================================="

echo "📋 Criando supervisores Kafka das Fatos no Druid..."
FATO_EVENTOS_SPEC="$SPECS_DIR/fato_eventos_incendio.json"
FATO_FOCOS_SPEC="$SPECS_DIR/fato_focos_incendio.json"

if [[ ! -f "$FATO_EVENTOS_SPEC" ]]; then
  echo "❌ Spec da fato de eventos não encontrado: $FATO_EVENTOS_SPEC"
  exit 1
fi

if [[ ! -f "$FATO_FOCOS_SPEC" ]]; then
  echo "❌ Spec da fato de focos não encontrado: $FATO_FOCOS_SPEC"
  exit 1
fi

RESPOSTA_EVENTOS=$(curl -fs -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"$FATO_EVENTOS_SPEC" \
  "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor")
echo "  ✅ Supervisor da fato de eventos criado."

RESPOSTA_FOCOS=$(curl -fs -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"$FATO_FOCOS_SPEC" \
  "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor")
echo "  ✅ Supervisor da fato de focos criado."

echo
echo "🚀 Iniciando produtor de eventos..."
echo "   (Ctrl+C para parar o streaming)"
echo

uv run python -m pipelines.gold.src.streaming.produtor_eventos
