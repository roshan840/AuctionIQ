import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import concurrent.futures
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from urllib.parse import urlparse
from src.utils.logger import logger
from src.config import config
from src.models import Property
from src.database.repository import DatabaseRepository
from src.parser.auction_parser import AuctionParser

class ScraperService:
    """Service to handle the auction scraping workflow."""
    
    def __init__(self, repository: DatabaseRepository):
        self.repo = repository
        self.using_cloudscraper = False
        self.session = self._create_session()
        
        # Advanced Technique 1: Automatic Retries on HTTP failures
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update(config.HEADERS)
        self._apply_cookie_string(config.EAUCTIONS_COOKIE)
        self._warmup_session()

    def _create_session(self):
        """Create an HTTP session; prefer cloudscraper if available."""
        try:
            import cloudscraper
            self.using_cloudscraper = True
            logger.info("Using cloudscraper session for anti-bot protected pages.")
            return cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False}
            )
        except Exception:
            self.using_cloudscraper = False
            logger.info("cloudscraper not available; falling back to requests session.")
            return requests.Session()

    def _warmup_session(self):
        """Hit homepage once to initialize cookies/challenge context."""
        try:
            self.session.get(config.BASE_URL, timeout=20)
        except Exception:
            # Best-effort warmup; scraper can still proceed.
            pass

    def _apply_cookie_string(self, cookie_string: str):
        """Apply a browser-copied cookie string to scraper session."""
        if not cookie_string:
            return
        parsed = self._parse_cookie_string(cookie_string)
        if not parsed:
            return
        host = urlparse(config.BASE_URL).hostname or "www.eauctionsindia.com"
        for key, value in parsed.items():
            self.session.cookies.set(key, value, domain=host, path="/")
            self.session.cookies.set(key, value, domain=f".{host}", path="/")
        logger.info(f"Applied {len(parsed)} Cloudflare/browser cookie(s) for scraper session.")

    @staticmethod
    def _parse_cookie_string(cookie_string: str) -> Dict[str, str]:
        cookies: Dict[str, str] = {}
        for item in cookie_string.split(";"):
            part = item.strip()
            if not part or "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                cookies[key] = value
        return cookies

    def set_cloudflare_cookie(self, cookie_string: str):
        """Public method to set Cloudflare/browser cookies at runtime."""
        self._apply_cookie_string(cookie_string)
        self._warmup_session()

    def test_cloudflare_access(self) -> Dict[str, object]:
        """Verify whether the current session can reach the auction site."""
        test_url = config.BASE_URL
        cookie_names = sorted({c.name for c in self.session.cookies if c.name})
        has_cf_clearance = any(name == "cf_clearance" for name in cookie_names)

        try:
            response = self.session.get(test_url, timeout=25)
            blocked = self._is_cloudflare_block(response)
            if blocked:
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "message": (
                        "Cloudflare challenge detected. Complete verification in Chrome, "
                        "then paste cf_clearance cookie here."
                    ),
                    "has_cf_clearance": has_cf_clearance,
                    "cookie_count": len(cookie_names),
                }

            response.raise_for_status()
            links = AuctionParser.extract_links(
                BeautifulSoup(response.content, "html.parser"),
                config.BASE_URL,
            )
            return {
                "ok": True,
                "status_code": response.status_code,
                "message": f"Access OK — found {len(links)} listing link(s) on homepage.",
                "has_cf_clearance": has_cf_clearance,
                "cookie_count": len(cookie_names),
            }
        except Exception as exc:
            return {
                "ok": False,
                "status_code": getattr(getattr(exc, "response", None), "status_code", None),
                "message": str(exc),
                "has_cf_clearance": has_cf_clearance,
                "cookie_count": len(cookie_names),
            }

    @staticmethod
    def _is_cloudflare_block(response: requests.Response) -> bool:
        """Detect Cloudflare challenge pages even if they return HTTP 200."""
        text = (response.text or "").lower()
        server = (response.headers.get("server") or "").lower()
        
        challenge_indicators = [
            "checking your browser",
            "just a moment",
            "verify you are human",
            "cf-browser-verification",
            "enable javascript and cookies",
            "access denied",
            "attention required"
        ]
        
        is_challenge = any(indicator in text for indicator in challenge_indicators)
        is_403 = response.status_code == 403
        is_cf_server = "cloudflare" in server
        
        return (is_403 and is_cf_server) or is_challenge

    def _get_page(self, url: str) -> requests.Response:
        """Fetch page with anti-bot detection and automated retries."""
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=25)
                
                if self._is_cloudflare_block(response):
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Cloudflare detected on {url}. Attempt {attempt+1}/{max_retries}. Waiting {wait_time}s...")
                    
                    if attempt == max_retries - 1:
                        if not self.using_cloudscraper:
                            raise RuntimeError(
                                "Blocked by Cloudflare. Install cloudscraper (`pip install cloudscraper`) "
                                "and retry scraping."
                            )
                        raise RuntimeError("Blocked by Cloudflare challenge. Please try applying fresh cookies in the UI.")
                    
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response
                
            except Exception as e:
                last_exception = e
                if "403" in str(e) or "Cloudflare" in str(e):
                    time.sleep(5)
                    continue
                raise e
                
        raise last_exception or RuntimeError(f"Failed to fetch {url} after {max_retries} attempts.")

    def _scrape_listing_pages(
        self,
        start_url: str,
        max_pages: int,
        default_city: Optional[str] = None,
        label: str = "scrape",
    ) -> int:
        """Shared listing-page scraper used by city and PAN-India flows."""
        total_new = 0
        any_page_processed = False
        last_error = None

        for page in range(1, max_pages + 1):
            url = start_url if page == 1 else f"{start_url}/{page}"
            logger.info(f"Scraping {label} page {page}: {url}")

            try:
                page_data = self._get_detail_links(url)
                any_page_processed = True
                if not page_data:
                    logger.warning(f"No links found on {label} page {page}. Stopping.")
                    break

                def process_property(item) -> Optional[Property]:
                    prop = self._scrape_detail_page(item["url"], item["summary"])
                    if prop and default_city and (prop.city == "N/A" or not prop.city):
                        prop.city = default_city
                    return prop

                batch: List[Property] = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(process_property, item): item for item in page_data}
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            prop = future.result()
                            if prop:
                                batch.append(prop)
                        except Exception as exc:
                            logger.error(f"Property generated an exception: {exc}")

                if batch:
                    total_new += self.repo.save_properties_batch(batch)

                time.sleep(0.5 + random.random())

            except Exception as e:
                last_error = str(e)
                logger.error(f"Failed to scrape {label} page {page}: {e}")

        if not any_page_processed and last_error:
            raise RuntimeError(last_error)
        return total_new

    def scrape_city_auctions(self, city_slug: str = "pune", max_pages: int = 3, city_name: Optional[str] = None):
        """Main entry point to scrape auctions for a specific city."""
        display_name = city_name or city_slug.capitalize().replace("-", " ")
        logger.info(f"Starting scrape for {display_name} ({city_slug}) - {max_pages} pages...")

        total_new = self._scrape_listing_pages(
            start_url=f"{config.BASE_URL}/city/{city_slug}",
            max_pages=max_pages,
            default_city=display_name,
            label=f"{city_slug}",
        )
        logger.info(f"Scrape completed for {city_slug}. Processed {total_new} records.")
        return total_new

    def scrape_pan_india_auctions(self, max_pages: int = 3):
        """Scrape auctions across PAN-India using the unified search endpoint."""
        logger.info(f"Starting PAN-India scrape - {max_pages} pages...")
        total_new = self._scrape_listing_pages(
            start_url=f"{config.BASE_URL}/search",
            max_pages=max_pages,
            default_city=None,
            label="PAN-India",
        )
        logger.info(f"PAN-India scrape completed. Processed {total_new} records.")
        return total_new

    def scrape_single_property(self, url: str) -> Optional[Property]:
        """Scrape a specific property detail URL directly."""
        logger.info(f"Targeting single property: {url}")
        try:
            prop = self._scrape_detail_page(url, "Manual target scrape")
            if prop:
                # Ensure city is set correctly if not found or mislabeled
                if prop.city == "N/A" or not prop.city:
                    prop.city = "Targeted Data"
                self.repo.save_property(prop)
                logger.info(f"Successfully scraped targeted property: {url}")
                return prop
        except Exception as e:
            logger.error(f"Failed to scrape single property {url}: {e}")
        return None

    def _get_detail_links(self, url: str) -> List[Dict[str, str]]:
        response = self._get_page(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return AuctionParser.extract_links(soup, config.BASE_URL)

    def _scrape_detail_page(self, url: str, listing_summary: str = "N/A") -> Optional[Property]:
        logger.debug(f"Fetching details: {url}")
        try:
            response = self._get_page(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = AuctionParser.parse_details(soup, url, listing_summary)
            return Property(**data)
        except Exception as e:
            logger.error(f"Error parsing detail page {url}: {e}")
            return None
