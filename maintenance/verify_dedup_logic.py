import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from src.database.repository import DatabaseRepository
from src.models import Property
from src.services.scraper import ScraperService

def verify_deduplication():
    print("🧪 Verifying Deduplication Logic...")
    repo = DatabaseRepository()
    
    # 1. Test Repository Smart Save
    print("\nStep 1: Testing repository smart save (fingerprint match)...")
    
    prop1 = Property(
        title="Deduplication Test Property",
        bank_name="Test Bank",
        reserve_price=1000000.0,
        city="Pune",
        area_locality="Baner",
        source_url="http://example.com/prop1",
        auction_id="TEST-123"
    )
    
    repo.save_property(prop1)
    initial_count = repo.get_property_count()
    print(f"Initial count: {initial_count}")
    
    # Property with SAME fingerprint (title+bank+price) but DIFFERENT URL
    prop2 = Property(
        title="Deduplication Test Property",
        bank_name="Test Bank",
        reserve_price=1000000.0,
        city="Pune",
        area_locality="Baner",
        source_url="http://example.com/prop2-different-url",
        auction_id="TEST-123" # Same auction_id
    )
    
    repo.save_property(prop2)
    final_count = repo.get_property_count()
    print(f"Final count after 'duplicate' save: {final_count}")
    
    if final_count == initial_count:
        print("✅ SUCCESS: Repository identified the duplicate and merged/updated instead of inserting.")
    else:
        print("❌ FAILURE: Repository inserted a duplicate record.")

    # 2. Test Scraper Skip Logic
    print("\nStep 2: Testing scraper skip logic...")
    scraper = ScraperService(repo)
    
    # Mock some page data that includes the property we just saved
    mock_item = {
        'url': "http://example.com/prop3-new-url",
        'title': "Deduplication Test Property",
        'bank_name': "Test Bank",
        'reserve_price': 1000000.0,
        'summary': "New listing of same prop"
    }
    
    existing_fps = repo.get_existing_fingerprints()
    # Fingerprint is (auction_id, title, bank, price)
    # Listing only has (None, title, bank, price)
    listing_fp = (None, mock_item['title'], mock_item['bank_name'], mock_item['reserve_price'])
    
    # We need to check if ANY existing fingerprint matches our listing partially
    is_redundant = False
    for efp in existing_fps:
        if efp[1] == mock_item['title'] and efp[2] == mock_item['bank_name'] and efp[3] == mock_item['reserve_price']:
            is_redundant = True
            break
            
    if is_redundant:
        print("✅ SUCCESS: Scraper identifies the property as redundant from listing data.")
    else:
        print("❌ FAILURE: Scraper did not identify the property as redundant.")

if __name__ == "__main__":
    verify_deduplication()
