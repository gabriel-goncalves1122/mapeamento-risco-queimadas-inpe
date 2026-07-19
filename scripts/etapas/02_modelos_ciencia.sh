#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "🔬 Etapa 2: Modelos Científicos"
echo "=================================================="

echo "📊 Executando Network Builder (Centralidade de Redes ONS)..."
uv run python src/science/network_builder.py
echo "✅ Network Builder concluído."

echo
echo "📊 Executando ST-DBSCAN (Clusterização Espaço-Temporal)..."
uv run python src/science/st_dbscan_clustering.py
echo "✅ ST-DBSCAN concluído."

echo
echo "🔎 Verificando outputs..."

FATOS_DIR="$PROJECT_ROOT/data/processed/fatos"
if [[ -f "$FATOS_DIR/fogo_eventos_stdbscan.csv" ]]; then
  LINES=$(wc -l < "$FATOS_DIR/fogo_eventos_stdbscan.csv")
  echo "  ✅ fogo_eventos_stdbscan.csv ($LINES linhas)"
else
  echo "  ❌ fogo_eventos_stdbscan.csv NÃO ENCONTRADO"
  exit 1
fi

echo
echo "✅ Etapa 2 concluída: Modelos científicos processados."
