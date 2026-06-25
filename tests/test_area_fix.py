"""
Clean test for area extraction
"""
import requests
from bs4 import BeautifulSoup
from src.parser.auction_parser import AuctionParser

test_url = "https://www.eauctionsindia.com/properties/659567"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print("Testing area extraction fix...")
print("=" * 60)

response = requests.get(test_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

data = AuctionParser.parse_details(soup, test_url)

print(f"Title: {data['title']}")
print(f"Reserve Price: Rs. {data['reserve_price']:,.0f}" if data['reserve_price'] else "Reserve Price: N/A")
print(f"\nDescription: {data['description'][:150]}..." if data['description'] != 'N/A' else "Description: N/A")
print(f"\nArea (sqft): {data['area_sqft']}" if data['area_sqft'] else "Area: NOT FOUND")
print(f"Rate/sqft: Rs. {data['rate_sqft']:,.2f}" if data.get('rate_sqft') else "Rate/sqft: NOT CALCULATED")

if data['area_sqft']:
    print("\nSUCCESS: Area extraction is working!")
else:
    print("\nFAILED: Area extraction still not working")
