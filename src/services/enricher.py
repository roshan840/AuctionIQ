import time
import json
import requests
import threading
from typing import Optional, Dict, Any, List
from src.utils.logger import logger
from src.config import config
from src.models import PropertyEnrichment

class KeyManager:
    """Thread-safe manager for multiple API keys with fallback logic."""
    
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.current_index = 0
        self.cooldowns = {key: 0 for key in keys}
        self.lock = threading.Lock()

    def get_key(self) -> Optional[str]:
        """Gets an available API key that isn't on cooldown."""
        with self.lock:
            now = time.time()
            # Try to find a key that is past its cooldown
            for _ in range(len(self.keys)):
                key = self.keys[self.current_index]
                if now >= self.cooldowns[key]:
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    return key
                self.current_index = (self.current_index + 1) % len(self.keys)
            return None

    def mark_cooldown(self, key: str, duration: int = 60, reason: str = "failure"):
        """Puts a key on cooldown if it failed."""
        with self.lock:
            self.cooldowns[key] = time.time() + duration
            logger.warning(f"API Key {key[:8]}... put on cooldown for {duration}s. Reason: {reason}")
            # Only advance current index if this key is now blocked
            if self.keys[self.current_index] == key:
                self.current_index = (self.current_index + 1) % len(self.keys)

    def seconds_until_next_key(self) -> int:
        """Returns wait time until the next key becomes available."""
        with self.lock:
            if not self.keys:
                return 0
            now = time.time()
            waits = [max(0, int(self.cooldowns[key] - now)) for key in self.keys]
            return min(waits) if waits else 0

class AIService:
    """Service for enriching property data using Gemini AI."""
    
    def __init__(self):
        self.key_manager = KeyManager(config.GEMINI_API_KEYS)
        primary_model = config.GEMINI_MODEL_NAME
        self.models = []
        for model in [primary_model, "gemini-2.0-flash", "gemini-2.5-flash"]:
            if model and model not in self.models:
                self.models.append(model)
        self.model = self.models[0] if self.models else "gemini-2.0-flash"
        self.endpoint_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    @staticmethod
    def _mask_key(api_key: str) -> str:
        if not api_key:
            return "***"
        if len(api_key) < 10:
            return "***"
        return f"{api_key[:6]}...{api_key[-4:]}"

    def check_api_keys_health(self) -> List[Dict[str, Any]]:
        """Checks whether each configured API key is currently usable."""
        statuses: List[Dict[str, Any]] = []
        if not self.key_manager.keys:
            return [{
                "key": "***",
                "ok": False,
                "status_code": None,
                "message": "No GEMINI_API_KEYS configured in .env"
            }]

        for key in self.key_manager.keys:
            masked = self._mask_key(key)
            try:
                resp = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
                    timeout=15
                )
                if resp.status_code == 200:
                    statuses.append({
                        "key": masked,
                        "ok": True,
                        "status_code": 200,
                        "message": "Key is valid"
                    })
                else:
                    error_msg = f"HTTP {resp.status_code}"
                    try:
                        error_msg = resp.json().get("error", {}).get("message", error_msg)
                    except ValueError:
                        pass
                    statuses.append({
                        "key": masked,
                        "ok": False,
                        "status_code": resp.status_code,
                        "message": error_msg
                    })
            except requests.RequestException as exc:
                statuses.append({
                    "key": masked,
                    "ok": False,
                    "status_code": None,
                    "message": f"Request error: {exc}"
                })
        return statuses

    def enrich_property(self, property_data: Dict[str, Any]) -> Optional[PropertyEnrichment]:
        """Enriches a single property data by calling Gemini API."""
        results = self.enrich_properties_batch([property_data])
        return results[0] if results else None

    def enrich_properties_batch(self, properties: List[Dict[str, Any]]) -> List[Optional[PropertyEnrichment]]:
        """Enriches multiple properties in a single API call for better throughput."""
        if not properties:
            return []
        if not self.key_manager.keys:
            raise RuntimeError(
                "❌ No Gemini API keys configured. Add GEMINI_API_KEYS in .env to enable enrichment."
            )
            
        prompt = self._build_batch_prompt(properties)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        headers = {"Content-Type": "application/json"}
        
        max_attempts = max(12, len(self.key_manager.keys) * 12)
        for attempt in range(max_attempts):
            api_key = self.key_manager.get_key()
            if not api_key:
                # If no keys available, wait a bit and try again
                wait_seconds = max(2, min(30, self.key_manager.seconds_until_next_key() + 1))
                logger.warning(f"All API keys on cooldown. Waiting {wait_seconds}s before retry...")
                time.sleep(wait_seconds)
                continue
                
            try:
                response = None
                model_not_supported = False
                for model_name in self.models:
                    url = f"{self.endpoint_template.format(model=model_name)}?key={api_key}"
                    response = requests.post(url, json=payload, headers=headers, timeout=60)
                    if response.status_code == 404 and "not found" in response.text.lower():
                        model_not_supported = True
                        logger.warning(
                            f"Model {model_name} unavailable for key {self._mask_key(api_key)}; trying fallback."
                        )
                        continue
                    self.model = model_name
                    model_not_supported = False
                    break

                if model_not_supported and response is not None and response.status_code == 404:
                    self.key_manager.mark_cooldown(api_key, 180, reason="Model Not Supported (404)")
                    continue
                
                if response.status_code == 429:
                    # Exponential backoff for rate limiting
                    wait_time = min(2 ** (attempt % 5) + 5, 45) 
                    logger.warning(f"Rate limited (429) on key {self._mask_key(api_key)}... Wait {wait_time}s")
                    self.key_manager.mark_cooldown(api_key, wait_time + 10, reason="Rate Limited (429)")
                    time.sleep(wait_time)
                    continue
                    
                if response.status_code == 403:
                    # Quota exceeded or permission denied - long cooldown
                    logger.error(f"Quota exceeded or Access denied (403) on key {self._mask_key(api_key)}...")
                    self.key_manager.mark_cooldown(api_key, 7200, reason="Daily Quota Exceeded (403)") # 2 hours
                    continue

                if response.status_code == 400 and "expired" in response.text.lower():
                    logger.error(f"Expired API key detected: {self._mask_key(api_key)}")
                    self.key_manager.mark_cooldown(api_key, 86400, reason="Expired Key (400)")
                    continue

                response.raise_for_status()
                result = response.json()
                
                # Success! Small mandatory sleep to stay under RPM (Requests per Minute)
                time.sleep(2) 
                
                if 'candidates' not in result or not result['candidates']:
                    logger.error(f"AI response missing candidates: {result}")
                    return [None] * len(properties)

                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                return self._parse_batch_response(raw_text, len(properties))
                
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_json = e.response.json()
                        error_msg = error_json.get('error', {}).get('message', error_msg)
                    except (ValueError, json.JSONDecodeError):
                        pass
                
                logger.error(f"Batch request failed with key {self._mask_key(api_key)}: {error_msg}")
                self.key_manager.mark_cooldown(api_key, 15, reason="General Exception")
                time.sleep(2)
                
        # Determine specific failure reason for the user
        quota_keys = [k for k, v in self.key_manager.cooldowns.items() if v > time.time() + 3600]
        if len(quota_keys) == len(self.key_manager.keys):
            raise RuntimeError(
                "AI DAILY QUOTA EXCEEDED: All API keys have reached their daily usage limit. "
                "AI enrichment will resume tomorrow, or you can add more API keys to .env."
            )
        else:
            raise RuntimeError(
                "AI RATE LIMITED: The API keys are temporarily paused to avoid blocking. "
                "Please wait 1-2 minutes and try again, or use 'Smart Sync' for automated retries."
            )

    def _build_batch_prompt(self, properties: List[Dict[str, Any]]) -> str:
        """Constructs a batch prompt for Gemini."""
        prop_blocks = []
        unique_cities = set()
        for i, data in enumerate(properties):
            city = data.get('city') or 'Unknown City'
            unique_cities.add(str(city))
            block = f"""
            [Property {i+1}]
            City: {city}
            Area: {data.get('area_locality', 'N/A')}
            Description: {data.get('description', '')[:800]}
            """
            prop_blocks.append(block)
            
        blocks_text = "\n".join(prop_blocks)
        cities_str = ", ".join(unique_cities)
        
        return f"""
        You are a real estate expert specializing in Indian property markets (including {cities_str}). 
        Analyze the {len(properties)} bank auction properties listed below and extract structured metadata for each.
        
        {blocks_text}
        
        Task: For EACH property, extract exactly these fields:
        1. 'area_sqft': Total area in square feet. If only Sq Mtr is mentioned, convert it (1 Sqm = 10.76 Sqft). Return a number.
        2. 'market_rate_sqft': Estimated average market rate per sqft for this area (Return a single number based on current market trends in {cities_str}).
        3. 'village': Village/Local area name.
        4. 'property_type': (e.g., Flat, Shop, Plot, Office).
        5. 'floor': Which floor (e.g., 2nd Floor, Ground).
        6. 'society_name': Apartment or project name.
        7. 'investment_score': A number from 0-100 indicating how good a deal this is (based on discount vs market rate and area quality).
        8. 'risk_rating': 'Low', 'Medium', or 'High' based on property type and area profile.
        
        Rules:
        - Return ONLY a JSON ARRAY contains {len(properties)} objects, one for each property in order.
        - NO markdown formatting.
        - If unknown for a property, return null for that field.
        
        Format example:
        [
            {{
                "area_sqft": 1050,
                "market_rate_sqft": 6500,
                "village": "Local Area",
                "property_type": "Flat",
                "floor": "4th Floor",
                "society_name": "Project Name",
                "investment_score": 85,
                "risk_rating": "Low"
            }},
            ...
        ]
        """

    def _parse_batch_response(self, text: str, expected_count: int) -> List[Optional[PropertyEnrichment]]:
        """Parses and validates the batched AI response."""
        try:
            # Clean markdown if present
            clean_text = text.replace('```json', '').replace('```', '').strip()
            # Find the first [ and last ] to handle potential extra text
            start = clean_text.find('[')
            end = clean_text.rfind(']')
            if start != -1 and end != -1:
                clean_text = clean_text[start:end+1]
                
            data_list = json.loads(clean_text)
            
            if not isinstance(data_list, list):
                logger.error("AI response is not a JSON array")
                return [None] * expected_count
                
            results = []
            for item in data_list:
                try:
                    results.append(PropertyEnrichment(**item))
                except Exception:
                    results.append(None)
                    
            # Pad or truncate to match expected count
            while len(results) < expected_count:
                results.append(None)
            return results[:expected_count]
            
        except Exception as e:
            logger.error(f"Failed to parse batch AI response: {e} | Text: {text[:200]}...")
            return [None] * expected_count

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """Deprecated: Use _build_batch_prompt instead."""
        return self._build_batch_prompt([data])

    def _parse_response(self, text: str) -> Optional[PropertyEnrichment]:
        """Deprecated: Use _parse_batch_response instead."""
        results = self._parse_batch_response(text, 1)
        return results[0] if results else None

    def generate_market_summary(self, properties_data: List[Dict[str, Any]]) -> str:
        """Generates a high-level AI summary of the current market state."""
        if not properties_data:
            return "No data available for analysis."
            
        # Aggregate data for prompt
        cities = {}
        total_val = 0
        enriched_count = 0
        for p in properties_data:
            c = p.get('city', 'Unknown')
            cities[c] = cities.get(c, 0) + 1
            total_val += (p.get('reserve_price') or 0)
            if p.get('market_rate_sqft'): enriched_count += 1
            
        avg_disc = sum(p.get('discount_rate_percent', 0) or 0 for p in properties_data if p.get('discount_rate_percent')) / (enriched_count or 1)
        top_deals = sorted([p for p in properties_data if p.get('investment_score')], 
                          key=lambda x: x.get('investment_score', 0), reverse=True)[:3]
        
        context = {
            "total_properties": len(properties_data),
            "cities": dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]),
            "avg_discount_on_enriched": f"{avg_disc:.1f}%",
            "total_reserve_cr": f"{total_val/1e7:.1f}Cr",
            "top_picks": [{"title": t['title'][:50], "score": t['investment_score'], "city": t['city']} for t in top_deals]
        }
        
        prompt = f"""
        Analyze this Bank Auction Market data and provide a professional investor's briefing:
        {json.dumps(context, indent=2)}
        
        Structure:
        1. **Market Sentiment**: 2 sentences on overall value.
        2. **Key Insights**: 3 bullet points on geographic hotspots, bank volume, or specific deal quality.
        3. **Investor Advice**: 1 sentence recommendation.
        
        Tone: Professional, Data-driven, Concise. Use Markdown.
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        api_key = self.key_manager.get_key()
        if not api_key: return "AI Summary unavailable (Keys on cooldown)."
        
        try:
            url = f"{self.endpoint_template.format(model=self.model)}?key={api_key}"
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as exc:
            logger.warning(f"Market summary request failed: {exc}")
        
        return "Market summary is temporarily unavailable. Detailed analytics are available in the charts below."

