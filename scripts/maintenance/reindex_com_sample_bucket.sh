#!/usr/bin/env bash
set -euo pipefail
# ==============================================================================
# SCRIPT: Reingestão Completa com sample_bucket
# ==============================================================================
# Procedimento para reiniciar toda a ingestão do zero após a adição
# da coluna sample_bucket via transformSpec nas specs de ingestão.
#
# FLUXO:
#   1. Terminar supervisores antigos
#   2. Deletar datasources antigos (dados limpos)
#   3. Recriar supervisores com as specs atualizadas
#   4. Re-executar o produtor Python para republicar tudo do CSV
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

SPECS_DIR="$PROJECT_ROOT/infrastructure/druid/specs"
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"
DRUID_COORDINATOR_URL="${DRUID_COORDINATOR_URL:-http://localhost:8081}"

DATASOURCES=(
  "fato_focos_incendio"
  "fato_eventos_incendio"
)

echo "=================================================="
echo "🔄 Reingestão Completa com sample_bucket"
echo "=================================================="

# --------------------------------------------------------------------------
# 1. Terminar supervisores existentes
# --------------------------------------------------------------------------
echo ""
echo "🛑 Terminando supervisores existentes..."
for DS in "${DATASOURCES[@]}"; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor/$DS/terminate" 2>/dev/null || true)
  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "  ✅ Supervisor '$DS' terminado."
  else
    echo "  ⚠️  Supervisor '$DS' não encontrado ou já terminado (HTTP $HTTP_CODE)."
  fi
done

echo "⏳ Aguardando 10s para tasks finalizarem..."
sleep 10

# --------------------------------------------------------------------------
# 2. Deletar datasources antigos
# --------------------------------------------------------------------------
echo ""
echo "🗑️  Deletando datasources antigos..."
for DS in "${DATASOURCES[@]}"; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    "$DRUID_COORDINATOR_URL/druid/coordinator/v1/datasources/$DS" 2>/dev/null || true)
  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "  ✅ Datasource '$DS' marcado para exclusão."
  else
    echo "  ⚠️  Datasource '$DS' não encontrado (HTTP $HTTP_CODE). Pode já estar limpo."
  fi
done

echo "⏳ Aguardando 15s para limpeza de segmentos..."
sleep 15

# --------------------------------------------------------------------------
# 3. Recriar supervisores com as specs atualizadas (contendo transformSpec)
# --------------------------------------------------------------------------
echo ""
echo "📋 Criando supervisores Kafka com sample_bucket..."

FATO_FOCOS_SPEC="$SPECS_DIR/fato_focos_incendio.json"
FATO_EVENTOS_SPEC="$SPECS_DIR/fato_eventos_incendio.json"

if [[ ! -f "$FATO_FOCOS_SPEC" ]]; then
  echo "❌ Spec de focos não encontrado: $FATO_FOCOS_SPEC"
  exit 1
fi

if [[ ! -f "$FATO_EVENTOS_SPEC" ]]; then
  echo "❌ Spec de eventos não encontrado: $FATO_EVENTOS_SPEC"
  exit 1
fi

curl -fs -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"$FATO_FOCOS_SPEC" \
  "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor" > /dev/null
echo "  ✅ Supervisor 'fato_focos_incendio' criado com transformSpec."

curl -fs -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"$FATO_EVENTOS_SPEC" \
  "$DRUID_OVERLORD_URL/druid/indexer/v1/supervisor" > /dev/null
echo "  ✅ Supervisor 'fato_eventos_incendio' criado com transformSpec."

# --------------------------------------------------------------------------
# 4. Executar o produtor de streaming (republica tudo do CSV)
# --------------------------------------------------------------------------
echo ""
echo "🚀 Iniciando produtor de eventos (re-publicação completa do CSV)..."
echo "   (Ctrl+C para parar o streaming)"
echo ""

uv run python -m pipelines.gold.src.streaming.produtor_eventos
