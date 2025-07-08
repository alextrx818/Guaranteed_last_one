# API Credentials
user = "thenecpt"
secret = "0c55322e8e196d6ef9066fa4252cf386"

import json
import time
import asyncio
import aiohttp
from datetime import datetime
import pytz

class CacheManager:
    def __init__(self):
        self.cache_file = "team_compeition_country_cache.json"
        self.base_url = "https://api.thesports.com/v1/football/"
        self.auth_params = {'user': user, 'secret': secret}
        self.cache_data = self.load_cache()
        self.TTL_HOURS = 24
        self.semaphore = asyncio.Semaphore(30)
    
    def load_cache(self):
        """Load cache from JSON file"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_content = json.load(f)
                # Extract cache_data if it exists, otherwise use the whole content
                if "cache_data" in cache_content:
                    return cache_content["cache_data"]
                return cache_content
        except (FileNotFoundError, json.JSONDecodeError):
            return {"teams": {}, "competitions": {}, "countries": None, "countries_cached_at": 0}
    
    def save_cache(self):
        """Save cache to JSON file with timestamp"""
        nyc_tz = pytz.timezone('America/New_York')
        cache_wrapper = {
            "last_updated": datetime.now(nyc_tz).strftime("%m/%d/%Y %I:%M:%S %p %Z"),
            "cache_data": self.cache_data
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_wrapper, f, indent=2)
    
    def is_fresh(self, cached_at, ttl_hours=24):
        """Check if cached data is still fresh"""
        if not cached_at:
            return False
        age_hours = (time.time() - cached_at) / 3600
        return age_hours < ttl_hours
    
    async def fetch_endpoint(self, session, endpoint, params=None):
        """Fetch data from API endpoint"""
        url = f"{self.base_url}{endpoint}"
        request_params = self.auth_params.copy()
        if params:
            request_params.update(params)
        
        async with self.semaphore:
            try:
                async with session.get(url, params=request_params) as response:
                    return await response.json()
            except Exception as e:
                return {"error": str(e), "endpoint": endpoint, "params": params}
    
    async def get_team(self, session, team_id):
        """Get team data from cache or API"""
        # Check cache first
        cached_team = self.cache_data["teams"].get(team_id)
        if cached_team and self.is_fresh(cached_team.get("cached_at")):
            return cached_team["data"]
        
        # Cache miss - fetch from API
        fresh_data = await self.fetch_endpoint(session, "team/additional/list", {"uuid": team_id})
        
        # Store in cache
        self.cache_data["teams"][team_id] = {
            "data": fresh_data,
            "cached_at": time.time()
        }
        
        return fresh_data
    
    async def get_competition(self, session, competition_id):
        """Get competition data from cache or API"""
        # Check cache first
        cached_comp = self.cache_data["competitions"].get(competition_id)
        if cached_comp and self.is_fresh(cached_comp.get("cached_at")):
            return cached_comp["data"]
        
        # Cache miss - fetch from API
        fresh_data = await self.fetch_endpoint(session, "competition/additional/list", {"uuid": competition_id})
        
        # Store in cache
        self.cache_data["competitions"][competition_id] = {
            "data": fresh_data,
            "cached_at": time.time()
        }
        
        return fresh_data
    
    async def get_countries(self, session):
        """Get countries data from cache or API (cached for 7 days)"""
        # Check cache first (7 day TTL for countries)
        if (self.cache_data.get("countries") and 
            self.is_fresh(self.cache_data.get("countries_cached_at", 0), ttl_hours=168)):  # 7 days = 168 hours
            return self.cache_data["countries"]
        
        # Cache miss - fetch from API
        fresh_data = await self.fetch_endpoint(session, "country/list")
        
        # Store in cache
        self.cache_data["countries"] = fresh_data
        self.cache_data["countries_cached_at"] = time.time()
        
        return fresh_data
    
    async def get_cached_data(self, session, team_ids, competition_ids):
        """Main method: Get all cached team, competition and country data"""
        # Fetch teams (parallel for cache misses only)
        team_tasks = [self.get_team(session, team_id) for team_id in team_ids]
        team_results = await asyncio.gather(*team_tasks, return_exceptions=True)
        
        # Fetch competitions (parallel for cache misses only)
        comp_tasks = [self.get_competition(session, comp_id) for comp_id in competition_ids]
        comp_results = await asyncio.gather(*comp_tasks, return_exceptions=True)
        
        # Fetch countries (single call, cached for 7 days)
        countries_data = await self.get_countries(session)
        
        # Save cache after all operations
        self.save_cache()
        
        return team_results, comp_results, countries_data