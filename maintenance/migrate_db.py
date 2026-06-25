import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config

DB_NAME = config.DB_NAME

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(properties)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'market_rate_sqft' not in columns:
        print("Adding market_rate_sqft column...")
        cursor.execute("ALTER TABLE properties ADD COLUMN market_rate_sqft REAL")
        
    if 'discount_rate_percent' not in columns:
        print("Adding discount_rate_percent column...")
        cursor.execute("ALTER TABLE properties ADD COLUMN discount_rate_percent REAL")

    # New columns for enrichment
    new_cols = {
        'village': 'TEXT',
        'property_type': 'TEXT',
        'floor': 'TEXT',
        'society_name': 'TEXT'
    }
    
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            print(f"Adding {col_name} column...")
            cursor.execute(f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
