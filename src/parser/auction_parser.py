import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from src.utils.logger import logger
from src.config import config

class AuctionParser:
    """Pure functions for parsing auction HTML content."""
    
    @staticmethod
    def extract_links(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extracts property detail links and summaries from a listing page."""
        results = []
        # Each property is usually in an 'item-card9' div or similar
        items = soup.find_all('div', class_=re.compile(r'item-card9|card', re.IGNORECASE))
        
        for item in items:
            link_tag = item.find('a', href=re.compile(r'/properties/\d+'))
            if link_tag:
                url = urljoin(base_url, link_tag['href'])
                summary = item.get_text(" ", strip=True)
                results.append({'url': url, 'summary': summary})
        
        # Fallback if no cards found
        if not results:
            links = soup.find_all('a', href=re.compile(r'/properties/\d+'))
            for link in links:
                results.append({'url': urljoin(base_url, link['href']), 'summary': "N/A"})
        
        # Deduplicate results based on URL
        unique_results = {}
        for res in results:
            if res['url'] not in unique_results:
                unique_results[res['url']] = res
        return list(unique_results.values())

    @staticmethod
    def parse_details(soup: BeautifulSoup, url: str, listing_summary: str = "N/A") -> Dict[str, Any]:
        """Parses the detail page of a property."""
        details = {'source_url': url, 'listing_summary': listing_summary}
        
        # Title
        title_tag = soup.find('h1')
        details['title'] = title_tag.get_text(strip=True) if title_tag else "Unknown Property"
        
        text_content = soup.get_text(separator="\n")
        
        # Pattern mapping for common fields
        patterns = {
            'bank_name': r'Bank Name\s*:\s*(.*)',
            'reserve_price': r'Reserve Price\s*:\s*(.*)',
            'emd': r'EMD\s*:\s*(.*)',
            'borrower_name': r'Borrower Name\s*:\s*(.*)',
            'auction_start_date': r'Auction Start Date\s*:\s*(.*)',
            'auction_end_time': r'Auction End Time\s*:\s*(.*)',
            'city': r'City/Town\s*:\s*(.*)',
            'area_locality': r'Area/Town\s*:\s*(.*)',
            'state': r'Province/State\s*:\s*(.*)',
            'branch_name': r'Branch Name\s*:\s*(.*)',
            'service_provider': r'Service Provider\s*:\s*(.*)',
            'asset_category': r'Asset Category\s*:\s*(.*)',
            'auction_type': r'Auction Type\s*:\s*(.*)',
            'property_type': r'Property Type\s*:\s*(.*)',
            'application_submission_date': r'Application Subbmision Date\s*:\s*(.*)',
            'possession_status': r'Possession\s*:\s*(.*)',
        }

        # Auction ID from URL
        auction_id_match = re.search(r'/properties/(\d+)', url)
        if auction_id_match:
            details['auction_id'] = auction_id_match.group(1)
        else:
            details['auction_id'] = "N/A"

        # Contact Details
        contact_block_match = re.search(r'Contact Details\s*:(.*?)(?:Description|Province/State|$)', text_content, re.IGNORECASE | re.DOTALL)
        if contact_block_match:
            lines = [l.strip() for l in contact_block_match.group(1).split('\n') if l.strip()]
            details['contact_details'] = " | ".join(lines) if lines else "N/A"
        else:
            # Fallback to CSS selector provided by User for Person & Mobile
            contact_node = soup.select_one('p.color-highlight')
            if contact_node:
                details['contact_details'] = contact_node.get_text(separator=' | ', strip=True)
            else:
                details['contact_details'] = "N/A"

        for key, pattern in patterns.items():
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                value = match.group(1).strip().split('\n')[0]
                details[key] = value
            else:
                details[key] = "N/A"

        # Price parsing
        details['reserve_price'] = AuctionParser._clean_price(details.get('reserve_price'))
        details['emd'] = AuctionParser._clean_price(details.get('emd'))
        
        # Notice Link
        details['notice_image_url'] = AuctionParser._extract_notice_link(soup)
        
        # Description
        details['description'] = AuctionParser._extract_description(soup)
        
        # Area extraction - try description first, then fall back to full text
        area = AuctionParser._extract_area(details['description'])
        if not area:
            # Fallback: search the entire page text
            area = AuctionParser._extract_area(text_content)
        details['area_sqft'] = area
        
        if area and details['reserve_price']:
            details['rate_sqft'] = round(details['reserve_price'] / area, 2)
            
        return details

    @staticmethod
    def _extract_notice_link(soup: BeautifulSoup) -> str:
        """Extracts the sale notice link (PDF or Image)."""
        # Strategy 1: Search for "Sale Notice" text node
        sn_node = soup.find(string=re.compile(r'Sale Notice', re.IGNORECASE))
        if sn_node:
            container = sn_node.find_parent(['div', 'tr', 'li', 'td'])
            if container:
                link = container.find('a', href=True)
                if link:
                    return urljoin(config.BASE_URL, link['href'])

        # Method 2: Fallback to common file patterns in 'a' tags
        file_links = soup.find_all('a', href=re.compile(r'\.(pdf|jpg|jpeg|png)$', re.IGNORECASE))
        for fl in file_links:
            href = fl['href']
            if 'logo' not in href.lower() and 'banner' not in href.lower():
                return urljoin(config.BASE_URL, href)
        
        return "N/A"

    @staticmethod
    def _clean_price(price_str: Optional[str]) -> Optional[float]:
        if not price_str or price_str == "N/A":
            return None
        clean = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(clean)
        except ValueError:
            return None

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str:
        """Extract property description from various HTML structures."""
        desc_header = soup.find(re.compile(r'^h[3-6]|strong|b'), string=re.compile(r'Description', re.IGNORECASE))
        if not desc_header:
            return "N/A"
        
        # Try multiple strategies to find the description content
        
        # Strategy 1: Check direct siblings
        curr = desc_header.next_sibling
        attempts = 0
        while curr and attempts < 10:
            if hasattr(curr, 'name'):
                if curr.name in ['div', 'p', 'span']:
                    text = curr.get_text(strip=True)
                    if text and len(text) > 20:
                        return text
            elif isinstance(curr, str) and len(curr.strip()) > 20:
                return curr.strip()
            curr = curr.next_sibling
            attempts += 1
        
        # Strategy 2: Check parent's next sibling
        if desc_header.parent:
            parent_next = desc_header.parent.next_sibling
            attempts = 0
            while parent_next and attempts < 10:
                if hasattr(parent_next, 'name'):
                    text = parent_next.get_text(strip=True)
                    if text and len(text) > 20:
                        return text
                elif isinstance(parent_next, str) and len(parent_next.strip()) > 20:
                    return parent_next.strip()
                parent_next = parent_next.next_sibling
                attempts += 1
        
        # Strategy 3: Look for common description containers near the header
        parent_container = desc_header.find_parent(['div', 'section', 'article'])
        if parent_container:
            # Find the next div/p after the header within the container
            for elem in parent_container.find_all(['div', 'p'], limit=5):
                if elem != desc_header and not desc_header in elem.parents:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 20 and 'description' not in text.lower():
                        return text
        
        return "N/A"

    @staticmethod
    def _extract_area(text: str) -> Optional[float]:
        """Regex to find area in sqft or sqm from description text."""
        if not text or text == "N/A":
            return None
            
        text = text.lower()
        # Sq Ft patterns
        sqft_patterns = [
            r'(?:area|total|carpet|built\s*up|plot|measuring|extent)\s*(?:area|of)?\s*(?:about|is|of)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?|square|sqr\.?|sq)\s*(?:ft\.?|feet|fts|foot)\b',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?|square|sqr\.?|sq)\s*(?:ft\.?|feet|fts|foot)\b',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*sqft\b',
            r'(?:plot|area)\s*(?:of)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?|ft\.?|mtrs?|sqm)\b'
        ]
        
        for pat in sqft_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1).replace(',', ''))
                    # If this matched mtrs/sqm in the last pattern, we need to convert
                    if 'sqm' in pat or 'mtr' in pat or 'sq.m' in text.lower()[match.start():match.end()+10]: 
                         # Check if the match was actually for meters
                         full_match = match.group(0).lower()
                         if 'mtr' in full_match or 'sqm' in full_match or 'm.' in full_match:
                             return round(val * 10.7639, 2)
                    return val
                except: continue
                
        # Sq Mtr patterns
        sqmtr_patterns = [
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?|square|sqr\.?)\s*(?:mt(?:r|er)s?|m\.?)\b',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*sqm\b',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*sq\.?\s*mtrs?\b'
        ]
        for pat in sqmtr_patterns:
            match = re.search(pat, text)
            if match:
                try:
                    return round(float(match.group(1).replace(',', '')) * 10.7639, 2)
                except: pass
            
        return None
