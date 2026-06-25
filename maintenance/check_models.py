import requests
import os

# Multiple API keys for fallback when first key has issues
GEMINI_API_KEYS = [
    "AIzaSyCzILOT-ZL7V54lE7PtQ7d_UcYFurpFOs4",  # First key (primary)
    "AIzaSyCDw5NqIgUmJHImVFrBhst2P6TCSYgvYUQ"   # Second key (fallback)
]

def list_models():
    """List available Gemini models, trying each API key until one works."""
    for key_index, api_key in enumerate(GEMINI_API_KEYS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            print(f"Trying API key {key_index + 1}/{len(GEMINI_API_KEYS)}...")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            print("Available Models:")
            for m in data.get('models', []):
                print(f"- {m['name']}")
            print(f"\n✓ Successfully connected with API key {key_index + 1}")
            return
                
        except Exception as e:
            print(f"✗ API key {key_index + 1} failed: {e}")
            if key_index < len(GEMINI_API_KEYS) - 1:
                print(f"  Trying next API key...\n")
            else:
                print(f"\n✗ All API keys failed. Could not list models.")

if __name__ == "__main__":
    list_models()
