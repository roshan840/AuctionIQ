import argparse
from src.utils.logger import logger
from src.database.repository import DatabaseRepository
from src.services.scraper import ScraperService
from src.services.enricher import AIService

def main():
    parser = argparse.ArgumentParser(description="Scrape Auction Properties")
    parser.add_argument("--city", type=str, default="pune", help="City slug to scrape (e.g., pune, mumbai, thane)")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to scrape")
    parser.add_argument("--enrich", action="store_true", help="Run AI enrichment after scraping")
    args = parser.parse_args()

    logger.info(f"🚀 Starting Scraper Engine (CLI Mode) - City: {args.city}, Limit: {args.pages} pages")
    
    # Initialize Core Services
    repo = DatabaseRepository()
    scraper = ScraperService(repo)
    
    # Run Scraper
    new_count = scraper.scrape_city_auctions(args.city, args.pages)
    logger.info(f"✅ Scraping Complete. Added {new_count} records.")
    
    if args.enrich:
        logger.info("🤖 Starting AI Enrichment for pending records...")
        enricher = AIService()
        pending = repo.get_pending_enrichment()
        
        if not pending:
            logger.info("No records pending enrichment.")
            return

        success_count = 0
        batch_size = 10
        total_batches = (len(pending) + batch_size - 1) // batch_size
        
        for i in range(0, len(pending), batch_size):
            batch = pending[i : i + batch_size]
            logger.info(f"Enriching batch {i//batch_size + 1}/{total_batches}...")
            
            batch_data = [p.dict() for p in batch]
            enriched_results = enricher.enrich_properties_batch(batch_data)
            
            for prop, enriched_data in zip(batch, enriched_results):
                if enriched_data:
                    # Calculate discount manually
                    discount = None
                    if enriched_data.market_rate_sqft and prop.rate_sqft:
                        discount = round(((enriched_data.market_rate_sqft - prop.rate_sqft) / enriched_data.market_rate_sqft) * 100, 2)
                    
                    update_payload = enriched_data.model_dump()
                    update_payload['discount_rate_percent'] = discount
                    
                    if repo.update_enrichment(prop.id, update_payload):
                        success_count += 1
        
        logger.info(f"✅ Enrichment Complete. Processed {success_count} properties.")

if __name__ == "__main__":
    main()
