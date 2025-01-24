import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG, INITIAL_DB_CONFIG
from sqlalchemy import create_engine
from orm import Base

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # 连接到默认的postgres数据库
        conn = psycopg2.connect(**INITIAL_DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", 
                      (DB_CONFIG['database'],))
        if not cursor.fetchone():
            # 创建新数据库
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"Database {DB_CONFIG['database']} created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")

def drop_tables():
    """Drop all existing tables"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Drop tables in correct order (respecting foreign key constraints)
        cursor.execute("""
            DROP TABLE IF EXISTS 
                clause_translations,
                legal_explanations,
                field_options,
                template_fields,
                contract_structures,
                special_clauses,
                contract_templates
            CASCADE
        """)
        
        conn.commit()
        print("All tables dropped successfully")
        
    except Exception as e:
        print(f"Error dropping tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def setup_tables():
    """Create tables in the database"""
    try:
        # Create SQLAlchemy engine
        engine = create_engine(f'postgresql://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}')
        
        # Create all tables
        Base.metadata.create_all(engine)
        print("Tables created successfully")
        
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_database()
    drop_tables()  # First drop existing tables
    setup_tables()  # Then create new tables