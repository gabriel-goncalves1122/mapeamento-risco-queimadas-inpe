#!/usr/bin/env bash
set -euo pipefail
# ==============================================================================
# SCRIPT: Reinício Completo do Ambiente CCO-DataOps
# ==============================================================================
# Reutiliza os scripts existentes em scripts/etapas/.
# Sequência:
#   1. Exportar dashboards/datasources do Superset (backup)
#   2. Derrubar TODOS os containers + volumes
#   3. Etapa 03: Docker + Kafka (sobe containers, cria tópicos, aguarda Druid)
#   4. Etapa 04: Dimensões + Lookups
#   5. Etapa 05: Supervisores Kafka (com sample_bucket) + Produtor
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="$PROJECT_ROOT/infrastructure/superset/exports"

echo "================================================================"
echo "🔄 REINÍCIO COMPLETO — CCO-DataOps ($TIMESTAMP)"
echo "================================================================"

# =========================================================================
# FASE 1: BACKUP DO SUPERSET
# =========================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 FASE 1: Exportando Dashboards e Datasources do Superset"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "$EXPORT_DIR"

echo "  📊 Exportando dashboards..."
docker exec superset superset export-dashboards \
  -f "/tmp/superset_dashboards_export_${TIMESTAMP}.zip" 2>/dev/null || true
docker cp "superset:/tmp/superset_dashboards_export_${TIMESTAMP}.zip" \
  "$EXPORT_DIR/superset_dashboards_export_${TIMESTAMP}.zip" 2>/dev/null && \
  echo "  ✅ Dashboards salvos." || \
  echo "  ⚠️  Não foi possível exportar dashboards."

echo "  📋 Exportando datasources..."
docker exec superset superset export-datasources \
  -f "/tmp/superset_datasources_export_${TIMESTAMP}.yaml" 2>/dev/null || true
docker cp "superset:/tmp/superset_datasources_export_${TIMESTAMP}.yaml" \
  "$EXPORT_DIR/superset_datasources_export_${TIMESTAMP}.yaml" 2>/dev/null && \
  echo "  ✅ Datasources salvos." || \
  echo "  ⚠️  Não foi possível exportar datasources."

echo ""
echo "  📂 Backups em: $EXPORT_DIR/"
ls -lh "$EXPORT_DIR/"*"${TIMESTAMP}"* 2>/dev/null || true

# =========================================================================
# FASE 2: DERRUBAR TUDO
# =========================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 FASE 2: Derrubando containers e volumes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose down -v --remove-orphans
echo "  ✅ Todos os containers e volumes removidos."

# =========================================================================
# FASE 3: ETAPA 03 — Docker + Kafka
# =========================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 FASE 3: Executando scripts/etapas/03_docker_e_kafka.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash scripts/etapas/03_docker_e_kafka.sh

# =========================================================================
# FASE 4: ETAPA 04 — Dimensões + Lookups
# =========================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 FASE 4: Executando scripts/etapas/04_druid_dimensoes.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash scripts/etapas/04_druid_dimensoes.sh

# =========================================================================
# FASE 5: ETAPA 05 — Supervisores + Produtor (com sample_bucket)
# =========================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔥 FASE 5: Executando scripts/etapas/05_streaming_eventos.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash scripts/etapas/05_streaming_eventos.sh
