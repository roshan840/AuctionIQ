import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEYS", "").split(",")[0].strip()

def test_gemini():
    print("Testing Gemini API...")
    if not GEMINI_API_KEY:
        print("Set GEMINI_API_KEYS in .env before running this test.")
        return
    model = "gemini-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    prompt_text = """
    Extract JSON data:
    Description: luxury flat for sale in Baner, Pune. 2 BHK. Market rate is around 8500.
    Fields: market_rate (number), village, property_type.
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    headers = { "Content-Type": "application/json" }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            return
            
        data = response.json()
        print("Response Data:")
        print(json.dumps(data, indent=2))
        
        # Check content
        try:
            content = data['candidates'][0]['content']['parts'][0]['text']
            print("\nExtracted Content:")
            print(content)
        except:
            print("Could not parse candidates.")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_gemini()
