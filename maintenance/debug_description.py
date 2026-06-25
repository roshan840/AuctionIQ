"""
Debug description extraction
"""
import requests
from bs4 import BeautifulSoup
import re

test_url = "https://www.eauctionsindia.com/properties/659567"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(test_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

print("Looking for 'Description' header...")
print("=" * 60)

# Find all elements containing "Description"
desc_headers = soup.find_all(re.compile(r'^h[3-6]|strong|b|span|div'), string=re.compile(r'Description', re.IGNORECASE))

print(f"Found {len(desc_headers)} potential description headers\n")

for i, header in enumerate(desc_headers, 1):
    print(f"\n--- Header {i} ---")
    print(f"Tag: {header.name}")
    print(f"Text: {header.get_text(strip=True)}")
    print(f"Parent: {header.parent.name}")
    
    # Try to find the description content
    print("\nTrying to find description content...")
    
    # Method 1: Next sibling
    curr = header.next_sibling
    count = 0
    while curr and count < 10:
        if hasattr(curr, 'name'):
            text = curr.get_text(strip=True)
            if text and len(text) > 20:
                print(f"  Next sibling ({curr.name}): {text[:200]}...")
                break
        elif isinstance(curr, str) and len(curr.strip()) > 20:
            print(f"  Next sibling (text): {curr.strip()[:200]}...")
            break
        curr = curr.next_sibling
        count += 1
    
    # Method 2: Parent's next sibling
    parent_next = header.parent.next_sibling
    count = 0
    while parent_next and count < 10:
        if hasattr(parent_next, 'name'):
            text = parent_next.get_text(strip=True)
            if text and len(text) > 20:
                print(f"  Parent's next sibling ({parent_next.name}): {text[:200]}...")
                break
        elif isinstance(parent_next, str) and len(parent_next.strip()) > 20:
            print(f"  Parent's next sibling (text): {parent_next.strip()[:200]}...")
            break
        parent_next = parent_next.next_sibling
        count += 1
