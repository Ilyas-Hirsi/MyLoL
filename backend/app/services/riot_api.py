import requests
import time
import threading
from collections import deque
from typing import List, Dict, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class RiotAPIService:
    def __init__(self):
        self.api_key = settings.RIOT_API_KEY
        self.region = settings.RIOT_API_REGION
        self.account_region = settings.RIOT_API_ACCOUNT_REGION
        self.base_url = f"https://{self.region}.api.riotgames.com"
        self.account_url = f"https://{self.account_region}.api.riotgames.com"
        # Sliding-window limiter: rate_limit requests per rate_window seconds.
        self.rate_limit = settings.RIOT_API_RATE_LIMIT
        self.rate_window = settings.RIOT_API_RATE_WINDOW_SECONDS
        self._request_times: deque = deque()
        self._rate_lock = threading.Lock()

    def _rate_limit(self):
        """Throttle to rate_limit requests per rate_window seconds."""
        with self._rate_lock:
            now = time.time()
            # Drop timestamps outside the window.
            while self._request_times and now - self._request_times[0] >= self.rate_window:
                self._request_times.popleft()

            # Window full: wait for the oldest request to expire.
            if len(self._request_times) >= self.rate_limit:
                sleep_for = self.rate_window - (now - self._request_times[0])
                if sleep_for > 0:
                    logger.debug(f"Rate limit reached, sleeping {sleep_for:.2f}s")
                    time.sleep(sleep_for)
                now = time.time()
                while self._request_times and now - self._request_times[0] >= self.rate_window:
                    self._request_times.popleft()

            self._request_times.append(time.time())
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make a rate-limited request to Riot API"""
        self._rate_limit()
        
        headers = {"X-Riot-Token": self.api_key}
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            if response.status_code == 209:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 403:
                logger.error("Forbidden: check API key, rate limits, or permissions.")
                return None
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(60)  # Wait 1 minute for rate limit reset
                return self._make_request(url, params)
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_puuid(self, riot_id: str, tag: str) -> Optional[str]:
        """Get PUUID from Riot ID and tag"""
        url = f"{self.account_url}/riot/account/v1/accounts/by-riot-id/{riot_id}/{tag}/"
        data = self._make_request(url)
        if data:
            return data.get("puuid")
        else:
            logger.error("API call failed (getting PUUID)")
            return None
    
    def get_match_history(self, puuid: str, count: int = 100, start: int = 0, queue: Optional[int] = None) -> List[str]:
        """Get match history for a player"""
        url = f"{self.account_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params: Dict = {"count": count, "start": start}
        if queue is not None:
            params["queue"] = queue
        return self._make_request(url, params) or []
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed match information"""
        url = f"{self.account_url}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)

    def get_match_timeline(self, match_id: str) -> Optional[Dict]:
        """Get the per-minute timeline (frames) for a match."""
        url = f"{self.account_url}/lol/match/v5/matches/{match_id}/timeline"
        return self._make_request(url)
    
    def get_champion_mastery(self, puuid: str) -> List[Dict]:
        """Get champion mastery data"""
        url = f"{self.base_url}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        return self._make_request(url) or []


# Global instance
riot_api = RiotAPIService()
