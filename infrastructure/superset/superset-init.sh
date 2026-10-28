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

echo "🔧 Configurando permissões do banco (allow_cvas = True)..."
python -c "
import sqlite3
import os
db_path = os.environ.get('SUPERSET_HOME', '/app/superset_home') + '/superset.db'
try:
    conn = sqlite3.connect(db_path)
    conn.execute(\"UPDATE dbs SET allow_cvas = 1, expose_in_sqllab = 1, allow_ctas = 1 WHERE database_name = 'Apache Druid Lakehouse'\")
    conn.commit()
    conn.close()
    print('✅ CVAS habilitado com sucesso.')
except Exception as e:
    print(f'Aviso: não foi possível atualizar CVAS via sqlite3: {e}')
"

echo "🚀 5/5: Iniciando o servidor web do Superset..."
gunicorn \
    -w 2 \
    --timeout 120 \
    -b  0.0.0.0:8088 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    "superset.app:create_app()"