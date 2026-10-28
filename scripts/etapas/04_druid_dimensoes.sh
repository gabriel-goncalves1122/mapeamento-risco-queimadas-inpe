#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "📊 Etapa 4: Configuração de Dimensões no Druid (Lookups)"
echo "=================================================="

uv run python scripts/etapas/04_druid_lookups.py

echo
echo "🚀 Ingerindo tabelas dimensionais (Batch) no Druid..."
SPECS_DIR="$PROJECT_ROOT/infrastructure/druid/specs"
DRUID_OVERLORD_URL="${DRUID_OVERLORD_URL:-http://localhost:8081}"

for spec_file in "$SPECS_DIR"/dim_*.json; do
  if [[ -f "$spec_file" ]]; then
    filename=$(basename "$spec_file")
    echo "  ➡️ Enviando task batch para $filename..."
    
    # Submete a task e extrai o ID retornado
    task_id=$(curl -fs -X POST -H "Content-Type: application/json" --data-binary @"$spec_file" "$DRUID_OVERLORD_URL/druid/indexer/v1/task" | jq -r '.task')
    
    if [[ -z "$task_id" || "$task_id" == "null" ]]; then
      echo "  ❌ Erro ao enviar a task para $filename. Resposta inesperada da API."
      exit 1
    fi

    echo "  ✅ Task enviada (ID: $task_id). Aguardando persistência..."
    
    # Faz o polling até a task ser concluída
    while true; do
      status=$(curl -s "$DRUID_OVERLORD_URL/druid/indexer/v1/task/$task_id/status" | jq -r '.status.status')
      
      if [[ "$status" == "SUCCESS" ]]; then
        echo "  ✅ Task finalizada com sucesso."
        break
      elif [[ "$status" == "FAILED" ]]; then
        echo "  ❌ Task falhou! Verifique os logs do Druid (Overlord) para a task $task_id."
        exit 1
      fi
      
      # Imprime um ponto de progresso a cada ciclo sem quebrar a linha
      echo -n "."
      sleep 5
    done
    echo "" # Nova linha após o loop
  fi
done

echo
echo "✅ Etapa 4 concluída: Lookups e Datasources dimensionais configurados no Druid."
