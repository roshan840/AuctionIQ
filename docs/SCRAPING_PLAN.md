# Scraping Plan for eAuctionsIndia.com

## Current Implementation Status

### ✅ Already Implemented

The scraper **already visits detail pages** and extracts most fields:

1. **List Page Scraping** (`scrape_listings()`)
   - Scrapes: https://www.eauctionsindia.com/city/pune
   - Finds all property links: `/properties/{id}`
   - Extracts basic info from listing cards

2. **Detail Page Scraping** (`extract_details()`)
   - Visits each property URL: https://www.eauctionsindia.com/properties/{id}
   - Extracts comprehensive property data

### Current Fields Being Scraped

From **List Page**:
- Property URL
- Basic title/summary from card

From **Detail Page**:
- ✅ Detail Page Title (H1)
- ✅ Bank Name
- ✅ Reserve Price
- ✅ EMD
- ✅ Branch Name
- ✅ Service Provider
- ✅ Borrower Name
- ✅ Asset Category
- ✅ Auction Type
- ✅ Property Type
- ✅ Auction Start Date
- ✅ Auction End Time
- ✅ Application Submission Date
- ✅ City/Town
- ✅ Area/Town
- ✅ Province/State
- ✅ Description (full text)
- ✅ Sale Notice Link (PDF/image)

### ❌ Missing Fields

Based on the detail page structure, these fields are **NOT currently extracted**:

1. **Contact Details** (Phone Numbers)
   - Pattern: `Ph .: +91 20 25511034/8739018778/ 7509985705`
   - Location: Under "Bank Details" section
   - Multiple phone numbers separated by `/`

2. **Auction ID**
   - Pattern: `Auction ID :# 660682`
   - Currently not extracted (though it's in the URL)

## Recommended Enhancements

### 1. Add Contact Details Extraction

```python
# Add to extract_details() function
'Contact Details': r'Contact Details\s*:.*?Ph\s*\.?\s*:\s*(.*?)(?:\n|$)',
# Or more specific:
'Contact Phone': r'Ph\s*\.?\s*:\s*([^\n]+)',
```

### 2. Extract Auction ID

```python
# Extract from URL or page
auction_id_match = re.search(r'/properties/(\d+)', url)
if auction_id_match:
    details['Auction ID'] = auction_id_match.group(1)
```

### 3. Improve Field Extraction

Some fields might need better regex patterns based on actual HTML structure.

## Scraping Flow

```
1. Start: https://www.eauctionsindia.com/city/pune
   ↓
2. Extract all property links from listing page
   ↓
3. For each property link:
   a. Visit detail page: https://www.eauctionsindia.com/properties/{id}
   b. Extract all fields using extract_details()
   c. Merge with listing page data
   d. Process area/rate calculations
   e. Enrich with market rate API
   f. Save to database
   ↓
4. Move to next page (if max_pages not reached)
```

## Verification Checklist

- [x] List page scraping works
- [x] Detail page URLs are extracted correctly
- [x] Detail pages are visited
- [x] Most fields are extracted
- [ ] Contact Details extraction
- [ ] Auction ID extraction
- [ ] Verify all fields are saved to database

## Testing Plan

1. Run scraper with 1 page: `python pune_auction_scraper.py --pages 1`
2. Check database for all fields
3. Compare extracted data with actual page content
4. Verify no fields are missing

