# LOGGING ANALYSIS REFERENCE: See logging_indepth_analysis.md for comprehensive independent analysis methodology
# 
# PIPELINE ORCHESTRATION NOTES:
# - all_api.py is the PIPELINE STARTER that fetches raw data from TheSports.com API
# - After each fetch completes, trigger_merge() function orchestrates post-fetch processing:
#   1. Starts merge.py (next pipeline stage)
#   2. Starts all_api_var_logger.py (VAR incident detection)
#   3. Creates all_api_mirror.json (lightweight monitoring file)
# - trigger_merge() is poorly named - it's really "trigger_entire_downstream_pipeline()"
#
# API Credentials
user = "thenecpt"
secret = "0c55322e8e196d6ef9066fa4252cf386"

import json
import logging
import os
import random
import string
import asyncio
import aiohttp
import time
from datetime import datetime
import pytz

class AllApiLogger:
    def __init__(self, log_dir="all_api_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
    
    def generate_random_id(self, length=12):
        """Generate random alphanumeric ID for fetch tracking"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def get_nyc_timestamp(self):
        """Get current NYC timezone timestamp in MM/DD/YYYY format with AM/PM"""
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        return nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
    def log_fetch_id_tracking(self, fetch_id):
        """Log fetch ID with timestamp for pipeline tracking"""
        tracking_entry = {
            "fetch_id": fetch_id,
            "created_at": self.get_nyc_timestamp(),
            "status": "created",
            "merge.py": "",
            "pretty_print.py": "",
            "pretty_print_conversion.py": "",
            "monitor_central.py": "",
            "alert_3ou_half.py": "",
            "alert_underdog_0half.py": ""
        }
        
        # Append to tracking log
        with open('all_api_fetch_id_tracking.json', 'a') as f:
            json.dump(tracking_entry, f, indent=2)
            f.write('\n')
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"all_api_log_{timestamp}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
        
        self.logger = logging.getLogger('all_api_logger')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        handler = logging.FileHandler(self.log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_fetch(self, raw_data, pipeline_duration=None, match_stats=None):
        """Log pure raw API data with header/footer containing random ID and NYC timestamp"""
        self.fetch_count += 1
        fetch_id = self.generate_random_id()
        self.log_fetch_id_tracking(fetch_id)
        nyc_timestamp = self.get_nyc_timestamp()
        
        footer_data = {
            "random_fetch_id": fetch_id,
            "nyc_timestamp": nyc_timestamp,
            "pipeline_completion_time_seconds": round(pipeline_duration, 3) if pipeline_duration else None,
            "fetch_end": "=== RAW API DATA END ==="
        }
        
        # Add match statistics to footer
        if match_stats:
            footer_data["total_matches"] = match_stats["total_matches"]
            footer_data["matches_in_play"] = match_stats["matches_in_play"]
            footer_data["match_status_breakdown"] = match_stats["status_breakdown"]
        
        log_entry = {
            "FETCH_HEADER": {
                "fetch_number": self.fetch_count,
                "random_fetch_id": fetch_id,
                "nyc_timestamp": nyc_timestamp,
                "fetch_start": "=== RAW API DATA START ==="
            },
            "RAW_API_DATA": raw_data,
            "FETCH_FOOTER": footer_data
        }
        
        # Write to rotating log
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Append to main all_api.json file
        with open('all_api.json', 'a') as f:
            f.write(f'=== FETCH START: {fetch_id} | {nyc_timestamp} ===\n')
            json.dump(log_entry, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: {fetch_id} | {nyc_timestamp} ===\n')
        
        if self.fetch_count >= self.max_fetches:
            self.rotate_log()
    
    def rotate_log(self):
        self.fetch_count = 0
        self.accumulated_data = []
        # Clear the main all_api.json file
        open('all_api.json', 'w').close()
        self.setup_logging()

class AllApiCatchAllFetcher:
    def __init__(self):
        self.base_url = "https://api.thesports.com/v1/football/"
        self.auth_params = {'user': user, 'secret': secret}
        self.logger = AllApiLogger()
        self.semaphore = asyncio.Semaphore(30)
    
    async def fetch_endpoint(self, session, endpoint, params=None):
        """Raw API fetch with error handling"""
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
    
    async def catch_all_fetch(self):
        """Main catch-all API fetcher that gets everything"""
        pipeline_start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Get live matches (entry point)
            live_data = await self.fetch_endpoint(session, "match/detail_live")
            
            all_data = {
                "live_matches": live_data,
                "match_details": [],
                "match_odds": []
            }
            
            # Step 2: Extract match IDs and fetch details + odds in parallel
            if live_data and "results" in live_data:
                match_ids = [match.get("id") for match in live_data["results"] if match.get("id")]
                
                # Parallel fetch match details and odds
                details_tasks = [self.fetch_endpoint(session, "match/recent/list", {"uuid": mid}) for mid in match_ids]
                odds_tasks = [self.fetch_endpoint(session, "odds/history", {"uuid": mid}) for mid in match_ids]
                
                details_results = await asyncio.gather(*details_tasks, return_exceptions=True)
                odds_results = await asyncio.gather(*odds_tasks, return_exceptions=True)
                
                all_data["match_details"] = details_results
                all_data["match_odds"] = odds_results
                
            
            # Calculate pipeline completion time
            pipeline_end_time = time.time()
            pipeline_duration = pipeline_end_time - pipeline_start_time
            
            # Count matches and analyze status breakdown
            match_stats = self.analyze_match_stats(all_data)
            
            # Log the complete raw data dump with pipeline timing and match stats
            self.logger.log_fetch(all_data, pipeline_duration, match_stats)
            
            # Trigger merge.py after all_api.py completes
            self.trigger_merge()
            
            return all_data
    
    def trigger_merge(self):
        """Trigger merge.py to process the latest all_api.json data"""
        try:
            import subprocess
            import sys
            
            # Run merge.py as a subprocess to process the latest data
            merge_script_path = os.path.join(os.path.dirname(__file__), '..', '3_merge', 'merge.py')
            
            # Execute merge.py with the current all_api.json
            subprocess.run([sys.executable, merge_script_path, '--single-run'], 
                          cwd=os.path.join(os.path.dirname(__file__), '..', '3_merge'),
                          check=False)  # Don't raise exception if merge fails
            
        except Exception as e:
            print(f"Warning: Could not trigger merge process: {e}")
            # Continue normal operation even if merge fails
        
        # Trigger VAR incident logger
        try:
            subprocess.run([sys.executable, 'all_api_var_logger.py'], cwd=os.path.dirname(__file__), check=False)
        except Exception as e:
            print(f"Warning: Could not trigger VAR logger: {e}")
        
        # Create monitoring mirror file
        try:
            subprocess.run([sys.executable, 'all_api_mirror.py'], cwd=os.path.dirname(__file__), check=False)
        except Exception as e:
            print(f"Warning: Could not create mirror file: {e}")
    
    def analyze_match_stats(self, all_data):
        """Analyze match statistics from live data"""
        # Match status code mappings (from all_status_code.json - Match state status id key)
        status_mappings = {
            0: "Abnormal(suggest hiding)",
            1: "Not started", 
            2: "First half",
            3: "Half-time",
            4: "Second half",
            5: "Overtime",
            6: "Overtime(deprecated)", 
            7: "Penalty Shoot-out",
            8: "End",
            9: "Delay",
            10: "Interrupt",
            11: "Cut in half",
            12: "Cancel",
            13: "To be determined"
        }
        
        status_counts = {}
        total_matches = 0
        
        # Extract matches from live_matches data
        if all_data.get("live_matches") and all_data["live_matches"].get("results"):
            for match in all_data["live_matches"]["results"]:
                if match.get("score") and len(match["score"]) > 1:
                    status_id = match["score"][1]  # score[1] is the match status
                    total_matches += 1
                    
                    if status_id in status_counts:
                        status_counts[status_id] += 1
                    else:
                        status_counts[status_id] = 1
        
        # Format the breakdown
        status_breakdown = []
        for status_id, count in sorted(status_counts.items()):
            status_name = status_mappings.get(status_id, "Unknown Status")
            status_breakdown.append(f"Status ID {status_id} ({status_name}): {count} matches")
        
        # Count in-play matches (status IDs 2-7)
        # 2=First half, 3=Half-time, 4=Second half, 5=Overtime, 6=Overtime(deprecated), 7=Penalty Shoot-out
        in_play_statuses = [2, 3, 4, 5, 6, 7]
        matches_in_play = sum(status_counts.get(status_id, 0) for status_id in in_play_statuses)
        
        return {
            "total_matches": total_matches,
            "matches_in_play": matches_in_play,
            "status_breakdown": status_breakdown,
            "raw_status_counts": status_counts
        }

# Initialize the fetcher
all_api_fetcher = AllApiCatchAllFetcher()

# Main execution
if __name__ == "__main__":
    import time
    import signal
    import sys
    
    # Global flag for graceful shutdown
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous fetch...")
        running = False
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    async def continuous_fetch():
        global running
        fetch_count = 0
        
        print("Starting All API Continuous Fetch Cycle...")
        print("Fetching every 60 seconds (or immediately if fetch takes >60s)")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            fetch_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Fetch #{fetch_count}] Starting at {all_api_fetcher.logger.get_nyc_timestamp()}")
                
                # Perform the fetch
                result = await all_api_fetcher.catch_all_fetch()
                
                # Calculate fetch duration
                end_time = time.time()
                fetch_duration = end_time - start_time
                
                print(f"[Fetch #{fetch_count}] Completed in {fetch_duration:.2f} seconds")
                print(f"[Fetch #{fetch_count}] Logged to: {all_api_fetcher.logger.log_path}")
                
                # Calculate wait time (60 seconds total cycle time)
                target_interval = 60
                wait_time = max(0, target_interval - fetch_duration)
                
                if wait_time > 0:
                    print(f"[Fetch #{fetch_count}] Waiting {wait_time:.2f} seconds until next fetch...")
                    
                    # Wait in small increments to allow for graceful shutdown
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        await asyncio.sleep(0.5)  # Check every 0.5 seconds
                else:
                    print(f"[Fetch #{fetch_count}] Fetch took longer than 60s, starting next fetch immediately")
                
            except Exception as e:
                print(f"[Fetch #{fetch_count}] Error occurred: {e}")
                print(f"[Fetch #{fetch_count}] Waiting 60 seconds before retry...")
                
                # Wait before retry
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    await asyncio.sleep(0.5)
        
        print("\nContinuous fetch stopped. Goodbye!")
    
    # Run the continuous fetch
    try:
        asyncio.run(continuous_fetch())
    except KeyboardInterrupt:
        print("\nShutdown complete.")