#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

SPECS_DIR="$PROJECT_ROOT/infrastructure/druid_specs"
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"

DIM_SPECS=(
  "dim_municipios_coordenadas.json"
  "dim_hospitais_cnes.json"
  "dim_terras_indigenas_funai.json"
  "dim_rodovias_federais.json"
  "dim_ons_linhas_transmissao.json"
  "dim_ons_subestacoes.json"
  "dim_ons_sistemas_isolados.json"
)

echo "=================================================="
echo "📊 Etapa 4: Ingestão de Dimensões no Druid"
echo "=================================================="

echo "🔎 Validando JSONs..."
for spec_name in "${DIM_SPECS[@]}"; do
  python3 -m json.tool "$SPECS_DIR/$spec_name" > /dev/null
  echo "  ✅ $spec_name válido"
done

echo
echo "📤 Enviando tasks batch ao Druid..."
for spec_name in "${DIM_SPECS[@]}"; do
  spec_path="$SPECS_DIR/$spec_name"
  if [[ ! -f "$spec_path" ]]; then
    echo "  ⚠️ Spec não encontrado: $spec_path"
    continue
  fi
  RESPOSTA=$(curl -fs -X POST \
    -H "Content-Type: application/json" \
    --data-binary @"$spec_path" \
    "$DRUID_OVERLORD_URL/druid/indexer/v1/task")
  echo "  ✅ $spec_name enviado"
done

echo
echo "✅ Etapa 4 concluída: Dimensões enviadas ao Druid."
echo "   Aguarde alguns segundos para o Druid indexar os segmentos."
