import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config

db_path = config.DB_NAME

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get count
cursor.execute("SELECT COUNT(*) FROM properties")
count = cursor.fetchone()[0]
print(f"Total properties in database: {count}")

# Get sample data
cursor.execute("SELECT title, bank_name, city, reserve_price, area_sqft, source_url FROM properties LIMIT 5")
rows = cursor.fetchall()

print(f"\nSample properties:")
for i, row in enumerate(rows, 1):
    print(f"\n{i}. {row[0]}")
    print(f"   Bank: {row[1]}")
    print(f"   City: {row[2]}")
    print(f"   Price: ₹{row[3]:,.2f}" if row[3] else "   Price: N/A")
    print(f"   Area: {row[4]} sqft" if row[4] else "   Area: N/A")
    print(f"   URL: {row[5]}")

conn.close()
