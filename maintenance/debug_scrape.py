import requests
from bs4 import BeautifulSoup
import re

url = "https://www.eauctionsindia.com/properties/652782"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # improved search to see context
    # Find all elements with text 'Description'
    elements = soup.find_all(string=re.compile(r'Description', re.IGNORECASE))
    print(f"Found {len(elements)} 'Description' matches.")
    
    for i, el in enumerate(elements):
        parent = el.parent
        print(f"\n--- Match {i+1} ---")
        print(f"Tag: {parent.name}")
        print(f"Content: {el}")
        
        # Check parent hierarchy
        container = parent.parent
        print(f"Parent Tag: {container.name}")
        print("Container HTML Snippet:")
        print(str(container)[:500])
        
        # Check container's sibling
        sibling = container.next_sibling
        # If sibling is just text/newline, find next tag
        while sibling and (isinstance(sibling, str) and not sibling.strip()):
            sibling = sibling.next_sibling
            
        print("\nContainer's Next Tag Sibling:")
        if sibling:
           print(f"Tag: {sibling.name if hasattr(sibling, 'name') else 'Text'}")
           print(str(sibling)[:1000])
        else:
           print("None")

except Exception as e:
    print(e)
