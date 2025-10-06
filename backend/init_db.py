from database import create_database, engine
from models import Base
import os

def init_database():
    """Inicializar banco de dados SQLite"""
    print("Criando banco de dados...")
    
    # Verificar se o arquivo do banco já existe
    db_path = "./wex_intelligence.db"
    if os.path.exists(db_path):
        print(f"Banco de dados já existe em: {db_path}")
    else:
        print(f"Criando novo banco de dados em: {db_path}")
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")
    
    # Verificar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tabelas no banco: {tables}")

if __name__ == "__main__":
    init_database()