import sys
import os

try:
    from superset.app import create_app
    from superset.extensions import db
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.sql_lab import Query
    
    app = create_app()
    with app.app_context():
        database = db.session.query(Database).filter_by(database_name='Apache Druid Lakehouse').first()
        if not database:
            print("❌ Erro: Banco 'Apache Druid Lakehouse' não encontrado.")
            sys.exit(1)
            
        print(f"✅ DB ID: {database.id}")
        
        # Read the queries passed via env vars or just use fixed definitions
        import json
        queries_json = os.environ.get('DATASETS_JSON')
        if not queries_json:
            print("❌ Nenhuma query passada em DATASETS_JSON")
            sys.exit(1)
            
        datasets = json.loads(queries_json)
        
        for name, sql in datasets.items():
            # Create or update SqlaTable
            table = db.session.query(SqlaTable).filter_by(table_name=name, database_id=database.id).first()
            if not table:
                table = SqlaTable(table_name=name, database=database)
                db.session.add(table)
                print(f"Criando dataset {name}...")
            else:
                print(f"Atualizando dataset {name}...")
            
            table.sql = sql
            table.is_sqllab_view = True
            table.schema = "druid"
            
        db.session.commit()
        print("✅ Todos os datasets foram criados/atualizados com sucesso!")
        
except ImportError as e:
    print(f"Execute isso dentro do container Superset. Erro: {e}")
