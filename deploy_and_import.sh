#!/bin/bash
echo "Subindo o ambiente Docker..."
docker compose up -d

echo "Monitorando a inicialização do Superset..."
count=0
while ! docker compose logs superset 2>&1 | grep -q "Iniciando o servidor web do Superset"; do
  sleep 5
  count=$((count+1))
  if [ $count -gt 30 ]; then
    echo "Timeout esperando o Superset inicializar."
    exit 1
  fi
done

echo "Superset estabilizado. Injetando os dashboards exportados..."
docker cp infrastructure/superset/exports/superset_dashboards_export_20260908_144952.zip superset:/tmp/dashboards.zip
docker exec superset superset import-dashboards -p /tmp/dashboards.zip -u admin
echo "Injeção concluída!"
