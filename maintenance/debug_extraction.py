import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def debug_one_property():
    # 1. Get a random property URL
    list_url = "https://www.eauctionsindia.com/city/pune"
    resp = requests.get(list_url, headers=HEADERS)
    soup = BeautifulSoup(resp.content, "html.parser")
    
    link = soup.find('a', href=re.compile(r'/properties/\d+'))
    if not link:
        print("Could not find any property link on list page.")
        return
        
    full_url = "https://www.eauctionsindia.com" + link['href']
    print(f"inspecting: {full_url}")
    
    # 2. Fetch Detail Page
    d_resp = requests.get(full_url, headers=HEADERS)
    d_soup = BeautifulSoup(d_resp.content, "html.parser")
    
    # 3. Dump relevant parts
    # Look for "Sale Notice" or similar text
    text_matches = d_soup.find_all(string=re.compile("Sale Notice", re.IGNORECASE))
    print(f"\nFound {len(text_matches)} text matches for 'Sale Notice':")
    for tm in text_matches:
        print("--- Match ---")
        print(tm)
        print("Parent:", tm.parent)
        print("Grandparent:", tm.parent.parent)
        
    # Look for any links with 'pdf' or 'jpg'
    file_links = d_soup.find_all('a', href=re.compile(r'\.(pdf|jpg|png|jpeg)$', re.IGNORECASE))
    print(f"\nFound {len(file_links)} file links:")
    for fl in file_links:
        print("-", fl['href'])

if __name__ == "__main__":
    debug_one_property()
