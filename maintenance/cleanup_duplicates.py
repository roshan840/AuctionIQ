import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config

def cleanup_duplicates():
    db_path = config.DB_NAME
    print(f"🧹 Starting database cleanup: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Deduplicate by auction_id (strongest)
    print("Deduplicating by auction_id...")
    cursor.execute("""
        DELETE FROM properties 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM properties 
            WHERE auction_id IS NOT NULL AND auction_id != 'N/A'
            GROUP BY auction_id
        ) AND auction_id IS NOT NULL AND auction_id != 'N/A'
    """)
    removed_aid = cursor.rowcount
    print(f"Removed {removed_aid} records with duplicate auction_ids.")

    # 2. Deduplicate by Fingerprint (title + bank_name + reserve_price)
    print("Deduplicating by Fingerprint (title + bank + price)...")
    cursor.execute("""
        DELETE FROM properties 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM properties 
            GROUP BY title, bank_name, reserve_price
        )
    """)
    removed_fp = cursor.rowcount
    print(f"Removed {removed_fp} records with duplicate fingerprints.")
    
    conn.commit()
    conn.close()
    print("✅ Cleanup complete.")

if __name__ == "__main__":
    cleanup_duplicates()
