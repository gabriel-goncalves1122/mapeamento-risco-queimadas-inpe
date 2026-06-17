#!/bin/bash

echo "⚙️  1/5: Atualizando o banco de dados interno do Superset..."
superset db upgrade

echo "👤 2/5: Criando usuário Admin automatizado..."
superset fab create-admin \
              --username admin \
              --firstname Admin \
              --lastname Superset \
              --email admin@localhost \
              --password admin

echo "🛡️  3/5: Inicializando roles e permissões de segurança..."
superset init

echo "🔌 4/5: Conectando automaticamente ao Apache Druid..."
# Injeta a URI do Druid direto no banco do Superset
superset set_database_uri -d "Apache Druid Lakehouse" -u "druid://router:8888/druid/v2/sql/"

echo "🚀 5/5: Iniciando o servidor web do Superset..."
gunicorn \
    -w 2 \
    --timeout 120 \
    -b  0.0.0.0:8088 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    "superset.app:create_app()"