"""
Debug the full flow
"""
import requests
from bs4 import BeautifulSoup
from src.parser.auction_parser import AuctionParser

test_url = "https://www.eauctionsindia.com/properties/659567"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(test_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract description using the parser
desc = AuctionParser._extract_description(soup)

print("Description extracted:")
print("=" * 80)
print(desc)
print("\n" + "=" * 80)
print(f"Length: {len(desc)} characters")

# Now try to extract area from this description
area = AuctionParser._extract_area(desc)
print(f"\nArea extracted: {area}")

# Also test with full text
print("\n" + "=" * 80)
print("Testing with full page text:")
full_text = soup.get_text(separator=" ")
area_from_full = AuctionParser._extract_area(full_text)
print(f"Area from full text: {area_from_full}")
