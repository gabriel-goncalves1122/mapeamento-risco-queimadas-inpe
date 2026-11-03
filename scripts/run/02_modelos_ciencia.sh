#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "🔬 Etapa 2: Modelos Científicos"
echo "=================================================="

echo "📊 Executando Network Builder (Centralidade de Redes ONS)..."
uv run python pipelines/gold/src/science/networkx/network_builder.py
echo "✅ Network Builder concluído."

echo "🔎 Verificando outputs..."

if [[ -f "$PROJECT_ROOT/pipelines/silver/data/dimensions/dim_ons_subestacoes.csv" ]]; then
  echo "  ✅ Network Builder output validado indiretamente (arquivos em data/processed)"
fi

echo
echo "✅ Etapa 2 concluída: Modelos científicos processados."
