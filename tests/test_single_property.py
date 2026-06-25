import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
from src.parser.auction_parser import AuctionParser
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test with a known property
test_url = "https://www.eauctionsindia.com/properties/659567"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print(f"Testing URL: {test_url}\n")

response = requests.get(test_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Parse the details
data = AuctionParser.parse_details(soup, test_url)

print("Extracted Data:")
print("=" * 60)
for key, value in data.items():
    if value and str(value) != "N/A":
        print(f"{key}: {value}")

print("\n" + "=" * 60)
print("CRITICAL FIELDS:")
print("=" * 60)
print(f"Description: {data.get('description', 'N/A')[:200]}...")
print(f"Area (sqft): {data.get('area_sqft', 'N/A')}")
print(f"Rate/sqft: {data.get('rate_sqft', 'N/A')}")

# Let's manually search for area in the text
print("\n" + "=" * 60)
print("SEARCHING FOR AREA MENTIONS:")
print("=" * 60)
text = soup.get_text(separator="\n").lower()
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'sq' in line or 'area' in line or 'sqft' in line:
        print(f"Line {i}: {line.strip()}")
