import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
import sqlite3

def verify():
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    
    total = c.execute("SELECT count(*) FROM properties").fetchone()[0]
    valid_desc = c.execute("SELECT count(*) FROM properties WHERE description IS NOT NULL AND description != 'N/A' AND description != ''").fetchone()[0]
    
    print(f"Total Records: {total}")
    print(f"Records with Description: {valid_desc}")
    
    # Show a sample description if available
    sample = c.execute("SELECT description FROM properties WHERE description IS NOT NULL AND description != 'N/A' LIMIT 1").fetchone()
    if sample:
        print(f"Sample Description: {sample[0][:100]}...")
        
    conn.close()

if __name__ == "__main__":
    verify()
    
    # Check for new columns
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    try:
        c.execute("SELECT market_rate_sqft, discount_rate_percent FROM properties LIMIT 1")
        print("New columns (market_rate_sqft, discount_rate_percent) exist.")
    except Exception as e:
        print(f"New columns missing: {e}")
    conn.close()
