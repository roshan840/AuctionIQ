# Market Rate and Discount Calculation Summary

## Overview
This document explains how Market Rate and Discount Percentage are calculated in the auction scraper.

## Calculation Flow

### 1. Reserve Rate Calculation
**Location:** `extract_area_and_calculate_rate()` function, lines 642-654

```
Reserve Rate (per sqft) = Reserve Price ÷ Area (sqft)
```

**Process:**
- Extracts area from property description using regex patterns
- Parses reserve price from auction data
- Calculates: `rate = reserve_price / area_sqft`
- Stores as: `item['Sqft Rate(on reserve price)']`

### 2. Market Rate (AI Enrichment)
**Location:** `enrich_property_data()` function, lines 419-573

**Process:**
- Calls Gemini API with property details (city, area, description)
- API extracts average market rate per sqft for the area
- Stores as: `item['Market Rate(Sqft)']`
- Cached in `property_enriched_data.json` to avoid redundant API calls

**Note:** Currently, most market rates are `null` in the cache, indicating the API may not be returning market rate values reliably.

### 3. Discount Percentage Calculation
**Location:** `extract_area_and_calculate_rate()` function, lines 672-682

**Formula:**
```python
discount = ((market_rate - reserve_rate) / market_rate) * 100
```

**Logic:**
- Only calculates if both market_rate and reserve_rate are available
- Positive discount = Good deal (reserve price is lower than market)
- Negative discount = Premium (reserve price is higher than market)
- Zero discount = Reserve price equals market rate

**Example:**
- Market Rate: ₹5,000/sqft
- Reserve Rate: ₹4,000/sqft
- Discount: ((5000 - 4000) / 5000) × 100 = **20%**

## Code Implementation

```python
# Step 1: Calculate Reserve Rate
if area_sqft:
    reserve_price = parse_price(item.get('Reserve Price'))
    if reserve_price:
        rate = reserve_price / area_sqft
        item['Sqft Rate(on reserve price)'] = round(rate, 2)

# Step 2: Get Market Rate from API
enriched = enrich_property_data(item)
if enriched:
    item['Market Rate(Sqft)'] = enriched.get('market_rate')

# Step 3: Calculate Discount
market_rate = item.get('Market Rate(Sqft)')
if market_rate and isinstance(market_rate, (int, float)) and item.get('Sqft Rate(on reserve price)') != "N/A":
    reserve_rate = item['Sqft Rate(on reserve price)']
    discount = ((market_rate - reserve_rate) / market_rate) * 100
    item['Discount Rate(%)'] = round(discount, 2)
```

## Database Storage

- `market_rate_sqft` (REAL): Market rate per square foot
- `discount_rate_percent` (REAL): Discount percentage
- Both fields can be NULL if data is unavailable

## Current Status

✅ **Calculation Formula:** Verified and working correctly
✅ **Code Logic:** Correctly implemented
⚠️ **Data Availability:** Most properties have NULL market rates (API may need adjustment)

## Testing

Run the scraper to test calculations:
```bash
python pune_auction_scraper.py --pages 1
```

Check database:
```python
import sqlite3
conn = sqlite3.connect('auctions.db')
c = conn.cursor()
c.execute("SELECT id, title, rate_sqft, market_rate_sqft, discount_rate_percent FROM properties WHERE market_rate_sqft IS NOT NULL LIMIT 5")
print(c.fetchall())
```

