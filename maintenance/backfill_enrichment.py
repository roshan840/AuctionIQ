import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from pune_auction_scraper import enrich_property_data

DB_NAME = config.DB_NAME

def calculate_market_rates_and_discounts(property_ids=None, force_recalculate=False):
    """
    Calculate market rates and discounts for properties in the database.
    (Copied/Adapted from app.py to run standalone)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Build query
    if property_ids:
        placeholders = ','.join('?' * len(property_ids))
        if force_recalculate:
            query = f"SELECT * FROM properties WHERE id IN ({placeholders})"
            params = property_ids
        else:
            query = f"SELECT * FROM properties WHERE id IN ({placeholders}) AND (market_rate_sqft IS NULL OR market_rate_sqft = '')"
            params = property_ids
    else:
        if force_recalculate:
            query = "SELECT * FROM properties"
            params = []
        else:
            query = "SELECT * FROM properties WHERE market_rate_sqft IS NULL OR market_rate_sqft = ''"
            params = []
    
    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"Found {len(rows)} properties to process.")
    
    for row in rows:
        prop_dict = dict(zip(columns, row))
        prop_id = prop_dict['id']
        title = prop_dict.get('title', 'Unknown')
        
        print(f"Processing ID {prop_id}: {title[:30]}...")
        
        # Convert database row to item format expected by enrich_property_data
        item = {
            'City': prop_dict.get('city', ''),
            'Area': prop_dict.get('area_locality', ''),
            'Description': prop_dict.get('description', ''),
            'Listing Summary': prop_dict.get('listing_summary', ''),
            'URL': prop_dict.get('source_url', ''),
            'Reserve Price': prop_dict.get('reserve_price'),
            'Area(Sqft)': prop_dict.get('area_sqft'),
            'Sqft Rate(on reserve price)': prop_dict.get('rate_sqft')
        }
        
        try:
            # Enrich with market rate data
            enriched = enrich_property_data(item)
            
            if enriched:
                market_rate = enriched.get('market_rate')
                
                # Calculate discount if we have both market rate and reserve rate
                discount = None
                if market_rate and isinstance(market_rate, (int, float)):
                    reserve_rate = prop_dict.get('rate_sqft')
                    if reserve_rate and isinstance(reserve_rate, (int, float)):
                        try:
                            discount = ((market_rate - reserve_rate) / market_rate) * 100
                            discount = round(discount, 2)
                        except:
                            pass
                
                # Update database
                cursor.execute("""
                    UPDATE properties 
                    SET market_rate_sqft = ?,
                        discount_rate_percent = ?,
                        village = ?,
                        property_type = ?,
                        floor = ?,
                        society_name = ?
                    WHERE id = ?
                """, (
                    market_rate,
                    discount,
                    enriched.get('village'),
                    enriched.get('property_type'),
                    enriched.get('floor'),
                    enriched.get('society_name'),
                    prop_id
                ))
                
                conn.commit()
                success_count += 1
                print(f"  -> Success: Market Rate {market_rate}, Village {enriched.get('village')}")
                results.append({
                    'id': prop_id,
                    'status': 'success'
                })
            else:
                failed_count += 1
                print("  -> Failed: No data returned from API")
                results.append({
                    'id': prop_id,
                    'status': 'failed'
                })
                
        except Exception as e:
            failed_count += 1
            print(f"  -> Error: {e}")
            results.append({
                'id': prop_id,
                'status': 'error'
            })
    
    conn.close()
    return success_count, failed_count
    
if __name__ == "__main__":
    s, f = calculate_market_rates_and_discounts()
    print(f"\nFinal Result: {s} Succeeded, {f} Failed.")
