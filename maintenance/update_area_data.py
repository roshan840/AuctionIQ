"""
Re-scrape existing properties to update area data
"""
import sqlite3
from src.database.repository import DatabaseRepository
from src.services.scraper import ScraperService
from src.utils.logger import logger

print("=" * 80)
print("RE-SCRAPING EXISTING PROPERTIES TO UPDATE AREA DATA")
print("=" * 80)

# Get all existing URLs
repo = DatabaseRepository()
conn = sqlite3.connect("auctions.db")
cursor = conn.cursor()

cursor.execute("SELECT id, source_url, title, area_sqft FROM properties")
properties = cursor.fetchall()

print(f"\nFound {len(properties)} properties in database")
print(f"Properties without area data: {sum(1 for p in properties if not p[3])}")

# Re-scrape properties without area data
scraper = ScraperService(repo)
updated_count = 0

for prop_id, url, title, area_sqft in properties:
    if not area_sqft:  # Only update if area is missing
        print(f"\nRe-scraping: {title[:60]}...")
        try:
            # Scrape the property again
            prop = scraper._scrape_detail_page(url)
            if prop and prop.area_sqft:
                # Update the database
                cursor.execute("""
                    UPDATE properties 
                    SET area_sqft = ?, rate_sqft = ?, description = ?
                    WHERE id = ?
                """, (prop.area_sqft, prop.rate_sqft, prop.description, prop_id))
                conn.commit()
                updated_count += 1
                print(f"  ✓ Updated: Area = {prop.area_sqft} sqft, Rate = ₹{prop.rate_sqft:,.2f}/sqft" if prop.rate_sqft else f"  ✓ Updated: Area = {prop.area_sqft} sqft")
            else:
                print(f"  ✗ No area data found")
        except Exception as e:
            print(f"  ✗ Error: {e}")

conn.close()

print("\n" + "=" * 80)
print("UPDATE COMPLETE")
print("=" * 80)
print(f"Properties updated: {updated_count}")
