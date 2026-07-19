#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${1:-docs/performance/druid_capacity/20260630_000802}"
TEX_DIR="${REPORT_DIR}/tex"
PDF_DIR="${REPORT_DIR}/pdf"

reports=(
  "relatorio_capacidade_druid"
  "guia_metricas_benchmark"
  "catalogo_queries_benchmark"
  "apendice_evidencias_operacionais"
)

stale_reports=(
  "apendice_queries_benchmark"
  "apendice_metricas_operacionais"
)

if [ ! -d "${TEX_DIR}" ]; then
  echo "Diretorio LaTeX nao encontrado: ${TEX_DIR}" >&2
  exit 1
fi

mkdir -p "${PDF_DIR}"

for report in "${stale_reports[@]}"; do
  rm -f \
    "${TEX_DIR}/${report}.tex" \
    "${TEX_DIR}/${report}.aux" \
    "${TEX_DIR}/${report}.log" \
    "${TEX_DIR}/${report}.out" \
    "${TEX_DIR}/${report}.compile.log" \
    "${TEX_DIR}/${report}.pdf" \
    "${PDF_DIR}/${report}.pdf"
done

for report in "${reports[@]}"; do
  tex_file="${TEX_DIR}/${report}.tex"
  log_file="${TEX_DIR}/${report}.compile.log"

  if [ ! -f "${tex_file}" ]; then
    echo "Fonte LaTeX nao encontrado: ${tex_file}" >&2
    exit 1
  fi

  echo "Compilando ${report}.tex"
  (
    cd "${TEX_DIR}"
    pdflatex -interaction=nonstopmode "${report}.tex" > "${report}.compile.log" 2>&1 || true
    pdflatex -interaction=nonstopmode "${report}.tex" >> "${report}.compile.log" 2>&1 || true
  )

  if [ ! -f "${TEX_DIR}/${report}.pdf" ]; then
    echo "Falha ao compilar ${report}. Veja ${log_file}" >&2
    tail -n 80 "${log_file}" >&2 || true
    exit 1
  fi

  cp "${TEX_DIR}/${report}.pdf" "${PDF_DIR}/${report}.pdf"
  rm -f \
    "${TEX_DIR}/${report}.aux" \
    "${TEX_DIR}/${report}.log" \
    "${TEX_DIR}/${report}.out" \
    "${TEX_DIR}/${report}.compile.log" \
    "${TEX_DIR}/${report}.pdf"
done

echo "PDFs copiados para ${PDF_DIR}"
