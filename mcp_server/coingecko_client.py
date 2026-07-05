import os
import time
import logging
import requests
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coingecko_client")

class CoinGeckoClient:
    """
    CoinGecko API Client with caching support to protect against rate limits.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY")
        # Use pro base URL if key length matches standard pro pattern, else demo/public API
        if self.api_key and not self.api_key.startswith("CG-"):
            self.base_url = "https://pro-api.coingecko.com/api/v3"
            self.headers = {"x-cg-pro-api-key": self.api_key}
        elif self.api_key:
            self.base_url = "https://api.coingecko.com/api/v3"
            self.headers = {"x-cg-demo-api-key": self.api_key}
        else:
            self.base_url = "https://api.coingecko.com/api/v3"
            self.headers = {}

        # Simple memory TTL cache: { cache_key: (expiry_timestamp, data) }
        self._cache: Dict[str, tuple[float, Any]] = {}
        self.cache_ttl_seconds = 60  # Cache results for 60 seconds

    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            expiry, value = self._cache[key]
            if time.time() < expiry:
                logger.info(f"Cache hit for key: {key}")
                return value
            else:
                logger.info(f"Cache expired for key: {key}")
                del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        self._cache[key] = (time.time() + self.cache_ttl_seconds, value)

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Formulate cache key based on endpoint and sorted query params
        param_str = ""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        cache_key = f"{endpoint}?{param_str}"

        # Check Cache
        cached_data = self._get_cache(cache_key)
        if cached_data is not None:
            return cached_data

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info(f"API Request to: {url} with params: {params}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            # Handle rate limit (HTTP 429) gracefully
            if response.status_code == 429:
                logger.warning("CoinGecko API rate limit (429) hit. Returning empty data or raising.")
                raise Exception("CoinGecko API Rate Limit Exceeded (429). Please wait and try again.")
            
            response.raise_for_status()
            data = response.json()
            
            # Cache the successful response
            self._set_cache(cache_key, data)
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"CoinGecko API Error: {str(e)}")

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """
        Get simple price and 24h change details for a coin.
        """
        endpoint = "simple/price"
        params = {
            "ids": coin_id.lower().strip(),
            "vs_currencies": vs_currency.lower(),
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }
        return self._request(endpoint, params)

    def get_market_data(self, coin_id: str) -> Dict[str, Any]:
        """
        Get comprehensive market and listing data for a single coin.
        """
        endpoint = f"coins/{coin_id.lower().strip()}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        return self._request(endpoint, params)

    def get_historical_chart(self, coin_id: str, vs_currency: str = "usd", days: str = "7") -> Dict[str, Any]:
        """
        Get historical price data points for visual plotting.
        'days' can be 1, 7, 30, 90, 365, 'max'
        """
        endpoint = f"coins/{coin_id.lower().strip()}/market_chart"
        params = {
            "vs_currency": vs_currency.lower(),
            "days": days
        }
        return self._request(endpoint, params)

    def search_coins(self, query: str) -> Dict[str, Any]:
        """
        Search for coins, categories, and markets on CoinGecko.
        Helps verify token names or contract addresses.
        """
        endpoint = "search"
        params = {"query": query.strip()}
        return self._request(endpoint, params)
