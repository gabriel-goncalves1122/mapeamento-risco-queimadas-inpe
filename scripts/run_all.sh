#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ETAPAS_DIR="$PROJECT_ROOT/scripts/etapas"

SKIP_ETL=0
SKIP_DOCKER=0
SKIP_SCIENCE=0
RESET=0

VISUAL=0

for arg in "$@"; do
  case "$arg" in
    --skip-etl)     SKIP_ETL=1 ;;
    --skip-docker)  SKIP_DOCKER=1 ;;
    --skip-science) SKIP_SCIENCE=1 ;;
    --reset)        RESET=1 ;;
    --visual)       VISUAL=1 ;;
    --help)
      echo "Uso: scripts/run_all.sh [--skip-etl] [--skip-docker] [--skip-science] [--reset] [--visual]"
      echo
      echo "  --skip-etl      Pula a Etapa 1 (ETL Batch) se CSVs já existem"
      echo "  --skip-docker   Pula a Etapa 3 (Docker/Kafka) se containers já estão rodando"
      echo "  --skip-science  Pula a Etapa 2 (Modelos Científicos)"
      echo "  --reset         Faz docker compose down -v antes de tudo (modo nuclear)"
      echo "  --visual        Abre terminais paralelos em pop-up para monitorar Docker e Kafka"
      exit 0
      ;;
    *)
      echo "Opção desconhecida: $arg"
      echo "Use --help para ver as opções."
      exit 1
      ;;
  esac
done

echo "╔══════════════════════════════════════════════════╗"
echo "║     🚀 CCO-DataOps — Orquestrador Mestre 🚀     ║"
echo "╚══════════════════════════════════════════════════╝"
echo

if [[ $RESET -eq 1 ]]; then
  echo "⚠️  Modo RESET ativado. Derrubando containers e volumes..."
  docker compose down -v --remove-orphans
  echo "✅ Ambiente limpo."
  echo
fi

# ─────── Etapa 1: ETL Batch ───────
if [[ $SKIP_ETL -eq 0 ]]; then
  bash "$ETAPAS_DIR/01_etl_batch.sh"
else
  echo "⏭️  Etapa 1 (ETL Batch) pulada via --skip-etl"
fi
echo

# ─────── Etapa 2: Modelos Científicos ───────
if [[ $SKIP_SCIENCE -eq 0 ]]; then
  bash "$ETAPAS_DIR/02_modelos_ciencia.sh"
else
  echo "⏭️  Etapa 2 (Modelos Científicos) pulada via --skip-science"
fi
echo

# ─────── Etapa 3: Docker + Kafka ───────
if [[ $SKIP_DOCKER -eq 0 ]]; then
  bash "$ETAPAS_DIR/03_docker_e_kafka.sh"
  
  if [[ $VISUAL -eq 1 ]]; then
    echo "🖥️  [MONITOR] Abrindo terminal com 'docker stats'..."
    gnome-terminal --title="[Monitor] Docker Stats" -- bash -c "docker stats"
    sleep 2
  fi
else
  echo "⏭️  Etapa 3 (Docker/Kafka) pulada via --skip-docker"
fi
echo

# ─────── Etapa 4: Druid Dimensões ───────
if [[ $SKIP_DOCKER -eq 0 ]]; then
  bash "$ETAPAS_DIR/04_druid_dimensoes.sh"
  
  if [[ $VISUAL -eq 1 ]]; then
    echo "🖥️  [MONITOR] Abrindo terminal consumidor Kafka..."
    gnome-terminal --title="[Monitor] Kafka Consumer" -- bash -c "echo 'Escutando tópico streaming_eventos_incendio...'; docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic streaming_eventos_incendio; read -p 'Pressione ENTER para fechar a janela...'"
    sleep 2
    echo "🔥 O produtor rodará nesta janela principal. Pressione Ctrl+C para encerrar."
    echo
  fi
else
  echo "⏭️  Etapa 4 (Druid Dimensões) pulada (Docker não está ativo)"
fi
echo

# ─────── Etapa 5: Streaming ───────
if [[ $SKIP_DOCKER -eq 0 ]]; then
  bash "$ETAPAS_DIR/05_streaming_eventos.sh"
else
  echo "⏭️  Etapa 5 (Streaming) pulada (Docker não está ativo)"
fi

echo
echo "╔══════════════════════════════════════════════════╗"
echo "║            ✅ Pipeline Completo ✅               ║"
echo "╚══════════════════════════════════════════════════╝"
