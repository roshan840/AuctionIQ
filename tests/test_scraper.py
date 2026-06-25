import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.repository import DatabaseRepository
from src.services.scraper import ScraperService
from src.utils.logger import logger

def test_scraper():
    """Test the scraper functionality"""
    logger.info("=" * 60)
    logger.info("SCRAPER TEST STARTED")
    logger.info("=" * 60)
    
    # Initialize repository and scraper
    repo = DatabaseRepository()
    scraper = ScraperService(repo)
    
    # Get initial count
    initial_count = repo.get_property_count()
    logger.info(f"Initial property count in database: {initial_count}")
    
    # Test scraping 2 pages
    logger.info("\nStarting scrape test (2 pages)...")
    new_properties = scraper.scrape_city_auctions('pune', max_pages=2)
    
    # Get final count
    final_count = repo.get_property_count()
    logger.info(f"\nFinal property count in database: {final_count}")
    logger.info(f"New properties added: {new_properties}")
    
    # Verify data quality
    logger.info("\n" + "=" * 60)
    logger.info("DATA QUALITY CHECK")
    logger.info("=" * 60)
    
    # Get sample properties
    sample_properties = repo.get_all_properties(limit=5)
    
    if sample_properties:
        logger.info(f"\nShowing sample of {len(sample_properties)} properties:")
        for i, prop in enumerate(sample_properties, 1):
            logger.info(f"\n--- Property {i} ---")
            logger.info(f"Title: {prop.title}")
            logger.info(f"Bank: {prop.bank_name}")
            logger.info(f"City: {prop.city}")
            logger.info(f"Reserve Price: Rs. {prop.reserve_price:,.2f}" if prop.reserve_price else "Reserve Price: N/A")
            logger.info(f"Area: {prop.area_sqft} sqft" if prop.area_sqft else "Area: N/A")
            logger.info(f"Rate/sqft: Rs. {prop.rate_sqft:,.2f}" if prop.rate_sqft else "Rate/sqft: N/A")
            logger.info(f"Auction Start: {prop.auction_start_date}")
            logger.info(f"Description: {prop.description[:100]}..." if prop.description and len(prop.description) > 100 else f"Description: {prop.description}")
            logger.info(f"URL: {prop.source_url}")
    else:
        logger.warning("No properties found in database!")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total properties in database: {final_count}")
    logger.info(f"New properties scraped: {new_properties}")
    
    if new_properties > 0:
        logger.info("\nSUCCESS: SCRAPER IS WORKING CORRECTLY!")
    elif final_count > 0:
        logger.info("\nWARNING: No new properties found (might be already scraped)")
    else:
        logger.error("\nFAILED: SCRAPER FAILED - No data in database!")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_scraper()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)
