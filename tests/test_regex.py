"""
Test area regex patterns
"""
test_descriptions = [
    "Plot No. P11, Gat No. 199/200/2/11 Gulmohar Greens Na Plots, Village-Boriaindi Road, Tal- Daund, Dist Pune, Pune Maharashtra-412202 Admeasuring An Area of 131.22 Sq Mtr",
    "Flat admeasuring 1200 sq ft",
    "Property of 850 sqft",
    "Area: 2500 square feet",
    "Measuring 100 sq. ft.",
    "Plot of 500 sq.mtr"
]

import re

def extract_area(text: str):
    """Regex to find area in sqft or sqm from description text."""
    text = text.lower()
    # Sq Ft patterns
    sqft_patterns = [
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?|square|sqr\.?)\s*(?:ft\.?|feet|fts)\b',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*sqft\b'
    ]
    
    for pat in sqft_patterns:
        match = re.search(pat, text)
        if match:
            try:
                return ("sqft", float(match.group(1).replace(',', '')))
            except: continue
            
    # Sq Mtr patterns
    sqmtr_pat = r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?|square|sqr\.?)\s*(?:mt(?:r|er)s?|m\.?)\b'
    match = re.search(sqmtr_pat, text)
    if match:
        try:
            sqm = float(match.group(1).replace(',', ''))
            sqft = round(sqm * 10.7639, 2)
            return ("sqm", sqm, "->", sqft, "sqft")
        except: pass
        
    return None

print("Testing area extraction patterns:")
print("=" * 80)

for desc in test_descriptions:
    result = extract_area(desc)
    print(f"\nText: {desc}")
    print(f"Result: {result}")
