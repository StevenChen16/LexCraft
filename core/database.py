import sqlite3
from typing import List, Optional

class ContractDatabase:
    """Database operations for contract templates and clauses"""
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._setup_database()
        
    def _setup_database(self):
        """Create necessary tables if they don't exist"""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY,
                location TEXT,
                contract_type TEXT,
                property_type TEXT,
                content TEXT
            );
            
            CREATE TABLE IF NOT EXISTS clauses (
                id INTEGER PRIMARY KEY,
                category TEXT,
                content TEXT,
                prerequisites TEXT
            );
            
            CREATE TABLE IF NOT EXISTS regulations (
                id INTEGER PRIMARY KEY,
                location TEXT,
                category TEXT,
                content TEXT
            );
        """)
        self.conn.commit()
        
    def get_template(self, location: str, contract_type: str,
                    property_type: str) -> Optional[str]:
        """Retrieve appropriate contract template"""
        self.cursor.execute("""
            SELECT content FROM templates
            WHERE location = ? AND contract_type = ? AND property_type = ?
        """, (location, contract_type, property_type))
        
        result = self.cursor.fetchone()
        return result[0] if result else None
        
    def get_clauses(self, category: str) -> List[str]:
        """Retrieve special clauses by category"""
        self.cursor.execute("""
            SELECT content FROM clauses WHERE category = ?
        """, (category,))
        
        return [row[0] for row in self.cursor.fetchall()]
        
    def get_regulations(self, location: str, category: str) -> List[str]:
        """Retrieve relevant regulations"""
        self.cursor.execute("""
            SELECT content FROM regulations
            WHERE location = ? AND category = ?
        """, (location, category))
        
        return [row[0] for row in self.cursor.fetchall()]
