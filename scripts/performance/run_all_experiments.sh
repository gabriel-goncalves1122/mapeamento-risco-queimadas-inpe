#!/usr/bin/env bash
# ==============================================================================
# BATERIA CIENTÍFICA MESTRA - PROJETO DATAOPS / DRUID
# ==============================================================================
# Este script orquestra todo o processo de coleta de métricas, testes de estresse
# (Superset, queries frias, queries quentes), consolidação multicenário
# e geração final dos relatórios acadêmicos em PDF (LaTeX).
# ==============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export UV_CACHE_DIR=/tmp/uv-cache

echo "🚀 INICIANDO BATERIA CIENTÍFICA COMPLETA DE TESTES..."
echo "1. Validando integridade dos Dados e Contratos (Pytest)..."
cd "$PROJECT_ROOT"
uv run pytest infrastructure/tests/integration/test_data_integrity.py

echo "========================================================================"
echo "2. Executando Matriz de Capacidade de Estresse (Docker + Druid)"
echo "   -> Simulação Superset (Dashboards e Virtual Datasets)"
echo "   -> Múltiplos níveis de concorrência (1, 2, 4, 8, 16 usuários)"
echo "   -> Comparação Cold Cache (Disco) vs Warm Cache (Memória)"
echo "   -> Monitoramento de CPU, RAM e I/O de todos os containers"
echo "========================================================================"
# Usamos o perfil 'stress' para forçar as métricas extremas do sistema
export BENCH_PROFILE="stress" 
bash scripts/performance/run_capacity_matrix.sh

# Pegamos a pasta gerada na execução acima (a pasta mais recente dentro de druid_capacity)
LATEST_MATRIX_DIR=$(ls -td "$PROJECT_ROOT"/data/results/performance/druid_capacity/*/ | head -1)

echo "========================================================================"
echo "3. Processando Ativos Visuais e Relatórios LaTeX..."
echo "   -> Gerando mapas de calor, histogramas e tabelas sumárias"
echo "========================================================================"
uv run python scripts/performance/report_generator/main.py --matrix-dir "$LATEST_MATRIX_DIR"

# echo "========================================================================"
# echo "4. Compilando Relatório Final PDF (pdflatex)..."
# echo "========================================================================"
# bash scripts/performance/compile_capacity_reports.sh "$LATEST_MATRIX_DIR"

echo ""
echo "✅ BATERIA DE TESTES CIENTÍFICOS FINALIZADA COM SUCESSO!"
echo "📂 Todos os resultados em CSV estão na pasta:"
echo "   $LATEST_MATRIX_DIR"
