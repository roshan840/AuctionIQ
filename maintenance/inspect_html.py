"""
Check the actual description HTML structure
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

desc_header = soup.find(re.compile(r'^h[3-6]|strong|b'), string=re.compile(r'Description', re.IGNORECASE))

if desc_header:
    print("Found description header:")
    print(f"Tag: {desc_header.name}")
    print(f"Text: {desc_header.get_text()}")
    
    print("\n" + "=" * 80)
    print("Parent container:")
    print("=" * 80)
    parent = desc_header.parent
    print(f"Parent tag: {parent.name}")
    print(f"Parent text (first 500 chars): {parent.get_text()[:500]}")
    
    print("\n" + "=" * 80)
    print("Parent's next sibling:")
    print("=" * 80)
    parent_next = parent.next_sibling
    count = 0
    while parent_next and count < 5:
        if hasattr(parent_next, 'name') and parent_next.name:
            print(f"\nSibling {count + 1}:")
            print(f"Tag: {parent_next.name}")
            print(f"Classes: {parent_next.get('class', [])}")
            text = parent_next.get_text(strip=True)
            print(f"Text (first 300 chars): {text[:300]}")
            if 'sq' in text.lower() or 'mtr' in text.lower():
                print(">>> CONTAINS AREA INFO <<<")
                print(f"Full text: {text}")
                break
            count += 1
        parent_next = parent_next.next_sibling
