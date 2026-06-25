import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
import sqlite3

def check_duplicates():
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Check by auction_id
    print("--- Checking by auction_id ---")
    cursor.execute("""
        SELECT auction_id, COUNT(*) as count 
        FROM properties 
        WHERE auction_id IS NOT NULL AND auction_id != 'N/A' 
        GROUP BY auction_id 
        HAVING count > 1
    """)
    dups = cursor.fetchall()
    print(f"Duplicate auction_ids: {len(dups)}")
    for d in dups[:10]:
        print(dict(d))

    # 2. Check by title and bank_name
    print("\n--- Checking by title and bank_name ---")
    cursor.execute("""
        SELECT title, bank_name, COUNT(*) as count 
        FROM properties 
        GROUP BY title, bank_name 
        HAVING count > 1
    """)
    dups = cursor.fetchall()
    print(f"Duplicate title/bank combos: {len(dups)}")
    for d in dups[:10]:
        print(dict(d))
        
    conn.close()

if __name__ == "__main__":
    check_duplicates()
