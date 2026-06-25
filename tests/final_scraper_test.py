import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.repository import DatabaseRepository
from src.services.scraper import ScraperService
from src.utils.logger import logger
from src.config import config
import sqlite3

print("=" * 80)
print("FINAL SCRAPER TEST")
print("=" * 80)

# Get initial stats
conn = sqlite3.connect(config.DB_NAME)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM properties")
initial_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM properties WHERE area_sqft IS NOT NULL AND area_sqft > 0")
initial_with_area = cursor.fetchone()[0]

print(f"\nInitial state:")
print(f"  Total properties: {initial_count}")
print(f"  Properties with area: {initial_with_area} ({initial_with_area*100//initial_count if initial_count > 0 else 0}%)")

# Test scraping
print(f"\n{'=' * 80}")
print("Testing scraper with 1 page...")
print("=" * 80)

repo = DatabaseRepository()
scraper = ScraperService(repo)

new_properties = scraper.scrape_city_auctions('pune', max_pages=1)

# Get final stats
cursor.execute("SELECT COUNT(*) FROM properties")
final_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM properties WHERE area_sqft IS NOT NULL AND area_sqft > 0")
final_with_area = cursor.fetchone()[0]

print(f"\n{'=' * 80}")
print("RESULTS")
print("=" * 80)
print(f"  Total properties: {final_count} (added {final_count - initial_count})")
print(f"  Properties with area: {final_with_area} ({final_with_area*100//final_count if final_count > 0 else 0}%)")
print(f"  New properties scraped: {new_properties}")

# Show sample of newest properties
print(f"\n{'=' * 80}")
print("Sample of latest properties:")
print("=" * 80)

cursor.execute("""
    SELECT title, area_sqft, reserve_price, rate_sqft 
    FROM properties 
    ORDER BY id DESC 
    LIMIT 5
""")

for i, (title, area, price, rate) in enumerate(cursor.fetchall(), 1):
    print(f"\n{i}. {title[:60]}")
    print(f"   Area: {area} sqft" if area else "   Area: N/A")
    print(f"   Price: Rs. {price:,.0f}" if price else "   Price: N/A")
    print(f"   Rate: Rs. {rate:,.2f}/sqft" if rate else "   Rate: N/A")

conn.close()

print(f"\n{'=' * 80}")
if final_with_area > initial_with_area or new_properties > 0:
    print("SUCCESS: SCRAPER IS WORKING CORRECTLY!")
else:
    print("WARNING: No new data scraped (might be already in database)")
print("=" * 80)
