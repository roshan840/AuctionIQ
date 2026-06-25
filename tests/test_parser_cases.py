
import os
import sys
import requests
from bs4 import BeautifulSoup

# Add src to path
sys.path.append(os.getcwd())

from src.parser.auction_parser import AuctionParser
from src.config import config

def check_property_extraction(url, expected_fields):
    print(f"\n[TEST] URL: {url}")
    headers = config.HEADERS
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        details = AuctionParser.parse_details(soup, url, "Test Summary")
        
        failures = []
        for field, min_val in expected_fields.items():
            actual = details.get(field)
            
            # Validation logic
            if actual is None or actual == "N/A" or actual == 0:
                failures.append(f"Field '{field}' is missing or empty")
            elif isinstance(actual, (int, float)) and actual < min_val:
                failures.append(f"Field '{field}' value {actual} is less than {min_val}")
                
        if not failures:
            print(f"✅ PASSED")
            return True
        else:
            print(f"❌ FAILED:")
            for f in failures:
                print(f"  - {f}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Define test cases with required fields and minimum values (if numeric)
    test_cases = [
        {
            "url": "https://www.eauctionsindia.com/properties/661138",
            "expected": {
                "title": 1,
                "reserve_price": 1000000,
                "notice_image_url": 1,
                "area_sqft": 100
            }
        },
        {
            "url": "https://www.eauctionsindia.com/properties/661157",
            "expected": {
                "title": 1,
                "notice_image_url": 1
            }
        },
        {
            "url": "https://www.eauctionsindia.com/properties/645220",
            "expected": {
                "title": 1,
                "area_sqft": 10
            }
        },
        {
            "url": "https://www.eauctionsindia.com/properties/658408",
            "expected": {
                "title": 1,
                "area_sqft": 10
            }
        },
        {
            "url": "https://www.eauctionsindia.com/properties/660682",
            "expected": {
                "title": 1,
                "area_sqft": 10
            }
        }
    ]
    
    overall_success = True
    print("=== Auction Intelligence Test Suite ===")
    for case in test_cases:
        if not check_property_extraction(case["url"], case["expected"]):
            overall_success = False
            
    print("\n" + "="*40)
    if overall_success:
        print("OVERALL RESULT: ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("OVERALL RESULT: SOME TESTS FAILED")
        sys.exit(1)
