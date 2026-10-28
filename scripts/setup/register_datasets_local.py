import sys
import glob
import os

try:
    from superset.app import create_app
    from superset.extensions import db
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable
    
    app = create_app()
    with app.app_context():
        database = db.session.query(Database).filter_by(database_name='Apache Druid Lakehouse').first()
        if not database:
            print("❌ Erro: Banco 'Apache Druid Lakehouse' não encontrado.")
            sys.exit(1)
            
        print(f"✅ DB ID: {database.id}")
        
        # O script precisa rodar a partir do diretorio do projeto para encontrar os sql
        # Passaremos as queries como argumento se necessario, mas como estamos no /app do container,
        # vamos ler de um dir montado ou passamos os conteudos.
        pass
except ImportError:
    print("Execute isso dentro do container Superset.")
