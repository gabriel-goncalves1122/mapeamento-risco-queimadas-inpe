#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "📦 Etapa 1: ETL Batch — Gerando Dimensões"
echo "=================================================="

uv run python pipelines/silver/src/etl_dimensions/run_etl.py

echo
echo "🔎 Verificando CSVs gerados..."
DIMS_DIR="$PROJECT_ROOT/pipelines/silver/data/dimensions"
EXPECTED_FILES=(
  "dim_municipios_coordenadas.csv"
  "dim_hospitais_cnes.csv"
  "dim_terras_indigenas.csv"
  "dim_rodovias_federais.csv"
  "dim_ons_linhas_transmissao.csv"
  "dim_ons_subestacoes.csv"
  "dim_ons_sistemas_isolados.csv"
)

ALL_OK=1
for f in "${EXPECTED_FILES[@]}"; do
  if [[ -f "$DIMS_DIR/$f" ]]; then
    LINES=$(wc -l < "$DIMS_DIR/$f")
    echo "  ✅ $f ($LINES linhas)"
  else
    echo "  ❌ $f NÃO ENCONTRADO"
    ALL_OK=0
  fi
done

if [[ $ALL_OK -eq 0 ]]; then
  echo "❌ Nem todos os CSVs foram gerados. Verifique os logs acima."
  exit 1
fi

echo
echo "✅ Etapa 1 concluída: Todas as dimensões geradas."
