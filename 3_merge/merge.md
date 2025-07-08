# API Credentials
user = "thenecpt"
secret = "0c55322e8e196d6ef9066fa4252cf386"

import json
import logging
import os
import random
import string
import time
import asyncio
import aiohttp
from datetime import datetime
import pytz
import sys
sys.path.append('../cached_endpoints')
from team_compeition_country_cache import CacheManager

class MergeLogger:
    def __init__(self, log_dir="merge_log", max_fetches=50):
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
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"merge_log_{timestamp}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
        
        self.logger = logging.getLogger('merge_logger')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        handler = logging.FileHandler(self.log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_fetch(self, merged_data, merge_duration=None, match_stats=None):
        """Log merged data with header/footer using same random ID from all_api.py"""
        self.fetch_count += 1
        
        # Extract the random ID from all_api source data for pipeline continuity
        source_fetch_id = None
        if merged_data and merged_data.get("SOURCE_ALL_API_HEADER"):
            source_fetch_id = merged_data["SOURCE_ALL_API_HEADER"].get("random_fetch_id")
        
        # Use all_api's random ID if available, otherwise generate new one
        fetch_id = source_fetch_id if source_fetch_id else self.generate_random_id()
        nyc_timestamp = self.get_nyc_timestamp()
        
        footer_data = {
            "random_fetch_id": fetch_id,
            "nyc_timestamp": nyc_timestamp,
            "merge_completion_time_seconds": round(merge_duration, 3) if merge_duration else None,
            "fetch_end": "=== MERGED DATA END ==="
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
                "fetch_start": "=== MERGED DATA START ==="
            },
            "MERGED_DATA": merged_data,
            "FETCH_FOOTER": footer_data
        }
        
        self.accumulated_data.append(log_entry)
        
        # Write to rotating log
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Also write to main merge.json file
        with open('merge.json', 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        if self.fetch_count >= self.max_fetches:
            self.rotate_log()
    
    def rotate_log(self):
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()

class SportsMerger:
    def __init__(self):
        self.logger = MergeLogger()
        self.cache_manager = CacheManager()
    
    def find_by_id(self, data_array, target_id):
        """Find data object by ID in array"""
        for item in data_array:
            if isinstance(item, dict) and item.get("results"):
                for result in item["results"]:
                    if result.get("id") == target_id:
                        return item
        return None
    
    def find_by_uuid(self, data_array, target_uuid):
        """Find data object by UUID in query field"""
        for item in data_array:
            if isinstance(item, dict) and item.get("query", {}).get("uuid") == target_uuid:
                return item
        return None
    
    def parse_live_data(self, live_match):
        """Parse live match data preserving all raw fields"""
        score = live_match.get("score", [])
        
        live_data = {
            "raw_score_array": score,  # Preserve complete raw score array
            "stats": live_match.get("stats", []),
            "incidents": live_match.get("incidents", []),
            "tlive": live_match.get("tlive", [])
        }
        
        # Parse score array if available
        if len(score) >= 4:
            live_data["parsed_score"] = {
                "match_id": score[0] if len(score) > 0 else None,
                "status": score[1] if len(score) > 1 else None,
                "home_stats": score[2] if len(score) > 2 else [],
                "away_stats": score[3] if len(score) > 3 else [],
                "kickoff_timestamp": score[4] if len(score) > 4 else None,
                "compatible_ignore": score[5] if len(score) > 5 else None
            }
            
            # Parse team stats if available
            if len(score) > 2 and isinstance(score[2], list) and len(score[2]) >= 7:
                live_data["parsed_score"]["home_detailed"] = {
                    "score_regular": score[2][0],
                    "score_halftime": score[2][1], 
                    "red_cards": score[2][2],
                    "yellow_cards": score[2][3],
                    "corners": score[2][4],
                    "overtime_score": score[2][5],
                    "penalty_score": score[2][6]
                }
            
            if len(score) > 3 and isinstance(score[3], list) and len(score[3]) >= 7:
                live_data["parsed_score"]["away_detailed"] = {
                    "score_regular": score[3][0],
                    "score_halftime": score[3][1],
                    "red_cards": score[3][2], 
                    "yellow_cards": score[3][3],
                    "corners": score[3][4],
                    "overtime_score": score[3][5],
                    "penalty_score": score[3][6]
                }
        
        return live_data
    
    def extract_team_info(self, team_data):
        """Extract team information preserving all raw fields"""
        if not team_data or not team_data.get("results"):
            return None
        
        team_result = team_data["results"][0]
        return {
            "raw_team_data": team_data,  # Complete raw team response
            "parsed_team": {
                "id": team_result.get("id"),
                "name": team_result.get("name"),
                "short_name": team_result.get("short_name"),
                "logo": team_result.get("logo"),
                "country_id": team_result.get("country_id"),
                "competition_id": team_result.get("competition_id")
            }
        }
    
    def extract_competition_info(self, competition_data):
        """Extract competition information preserving all raw fields"""
        if not competition_data or not competition_data.get("results"):
            return None
        
        comp_result = competition_data["results"][0]
        return {
            "raw_competition_data": competition_data,  # Complete raw competition response
            "parsed_competition": {
                "id": comp_result.get("id"),
                "name": comp_result.get("name"),
                "short_name": comp_result.get("short_name"),
                "logo": comp_result.get("logo"),
                "country_id": comp_result.get("country_id"),
                "category_id": comp_result.get("category_id")
            }
        }
    
    def extract_match_details(self, match_detail_data, home_team_data=None, away_team_data=None, competition_data=None, countries_data=None):
        """Extract match details preserving all raw fields and adding team names and competition name"""
        if not match_detail_data or not match_detail_data.get("results"):
            return None
        
        detail_result = match_detail_data["results"][0]
        
        # Extract team names from team data
        home_team_name = None
        away_team_name = None
        
        if home_team_data and home_team_data.get("results"):
            home_team_name = home_team_data["results"][0].get("name")
        
        if away_team_data and away_team_data.get("results"):
            away_team_name = away_team_data["results"][0].get("name")
        
        # Extract competition name, country_id and country name from competition data
        competition_name = None
        country_id = None
        country_name = None
        if competition_data and competition_data.get("results"):
            competition_name = competition_data["results"][0].get("name")
            country_id = competition_data["results"][0].get("country_id")
            
            # Special case: FIFA competitions are world events
            if competition_name and "FIFA" in competition_name:
                country_name = "World Cup"
            # Otherwise lookup country name using competition's country_id
            elif country_id and countries_data:
                # countries_data is from cache manager, check if it has results
                countries_list = countries_data.get("results", []) if isinstance(countries_data, dict) else []
                for country in countries_list:
                    if country.get("id") == country_id:
                        country_name = country.get("name")
                        break
        
        return {
            "raw_match_details": match_detail_data,  # Complete raw match details response
            "parsed_details": {
                "id": detail_result.get("id"),
                "season_id": detail_result.get("season_id"),
                "competition_id": detail_result.get("competition_id"),
                "competition_name": competition_name,  # NEW FIELD
                "country_id": country_id,  # NEW FIELD - extracted from competition
                "country_name": country_name,  # NEW FIELD - resolved from country_id
                "home_team_id": detail_result.get("home_team_id"),
                "home_team_name": home_team_name,  # NEW FIELD
                "away_team_id": detail_result.get("away_team_id"),
                "away_team_name": away_team_name,  # NEW FIELD
                "status_id": detail_result.get("status_id"),
                "match_time": detail_result.get("match_time"),
                "venue_id": detail_result.get("venue_id"),
                "referee_id": detail_result.get("referee_id"),
                "neutral": detail_result.get("neutral"),
                "note": detail_result.get("note")
            }
        }
    
    def extract_odds_data(self, odds_data):
        """Extract odds data preserving all raw fields"""
        if not odds_data:
            return None
        
        return {
            "raw_odds_data": odds_data  # Complete raw odds response
        }
    
    async def fetch_reference_data(self, live_matches):
        """Fetch teams, competitions, and countries data using CacheManager"""
        team_ids = set()
        competition_ids = set()
        
        # Extract unique team and competition IDs from live matches
        for match in live_matches:
            if match.get("home_team_id"):
                team_ids.add(match["home_team_id"])
            if match.get("away_team_id"):
                team_ids.add(match["away_team_id"])
            if match.get("competition_id"):
                competition_ids.add(match["competition_id"])
        
        # Fetch data using cache manager
        async with aiohttp.ClientSession() as session:
            team_results, comp_results, countries_data = await self.cache_manager.get_cached_data(
                session, list(team_ids), list(competition_ids)
            )
            
            # Convert results to lookup dictionaries
            teams_dict = {}
            for i, team_id in enumerate(team_ids):
                if i < len(team_results) and team_results[i]:
                    teams_dict[team_id] = team_results[i]
            
            comps_dict = {}
            for i, comp_id in enumerate(competition_ids):
                if i < len(comp_results) and comp_results[i]:
                    comps_dict[comp_id] = comp_results[i]
            
            return teams_dict, comps_dict, countries_data

    def analyze_match_stats(self, merged_data):
        """Analyze match statistics from merged data"""
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
        total_matches = len(merged_data.get("matches", []))
        
        for match in merged_data.get("matches", []):
            status = match.get("live_data", {}).get("parsed_score", {}).get("status")
            if status is not None:
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
        
        # Format the breakdown
        status_breakdown = []
        for status_id, count in sorted(status_counts.items()):
            status_name = status_mappings.get(status_id, "Unknown Status")
            status_breakdown.append(f"Status ID {status_id} ({status_name}): {count} matches")
        
        # Count in-play matches (status IDs 2-7)
        in_play_statuses = [2, 3, 4, 5, 6, 7]
        matches_in_play = sum(status_counts.get(status_id, 0) for status_id in in_play_statuses)
        
        return {
            "total_matches": total_matches,
            "matches_in_play": matches_in_play,
            "status_breakdown": status_breakdown,
            "raw_status_counts": status_counts
        }
    
    async def merge_sports_data(self, all_api_data_path):
        """Main merge function - pure raw data reorganization"""
        merge_start_time = time.time()
        
        # Read all_api.json data
        with open(all_api_data_path, 'r') as f:
            all_api_data = json.load(f)
        
        # Get the latest fetch data (last item in array)
        if not all_api_data or not isinstance(all_api_data, list):
            return {"error": "No valid data in all_api.json"}
        
        latest_fetch = all_api_data[-1]
        raw_data = latest_fetch.get("RAW_API_DATA", {})
        
        # Process each live match
        live_matches = raw_data.get("live_matches", {}).get("results", [])
        
        # Extract team and competition IDs from match details
        match_details_array = raw_data.get("match_details", [])
        enhanced_live_matches = []
        for live_match in live_matches:
            enhanced_match = live_match.copy()
            match_id = live_match.get("id")
            
            # Find match details for this match
            match_detail_data = self.find_by_id(match_details_array, match_id)
            if match_detail_data and match_detail_data.get("results"):
                detail_result = match_detail_data["results"][0]
                enhanced_match["home_team_id"] = detail_result.get("home_team_id")
                enhanced_match["away_team_id"] = detail_result.get("away_team_id")
                enhanced_match["competition_id"] = detail_result.get("competition_id")
            
            enhanced_live_matches.append(enhanced_match)
        
        # Fetch reference data using cache manager
        teams_dict, comps_dict, countries_data = await self.fetch_reference_data(enhanced_live_matches)
        
        merged_matches = []
        
        for live_match in live_matches:
            match_id = live_match.get("id")
            if not match_id:
                continue
            
            # Find corresponding data for this match
            match_detail_data = self.find_by_id(raw_data.get("match_details", []), match_id)
            odds_data = self.find_by_uuid(raw_data.get("match_odds", []), match_id)
            
            # Extract team and competition IDs from match details
            home_team_data = None
            away_team_data = None 
            competition_data = None
            
            if match_detail_data and match_detail_data.get("results"):
                detail_result = match_detail_data["results"][0]
                home_team_id = detail_result.get("home_team_id")
                away_team_id = detail_result.get("away_team_id")
                competition_id = detail_result.get("competition_id")
                
                # Find team and competition data from cached reference data
                if home_team_id:
                    home_team_data = teams_dict.get(home_team_id)
                if away_team_id:
                    away_team_data = teams_dict.get(away_team_id)
                if competition_id:
                    competition_data = comps_dict.get(competition_id)
            
            # Create merged match object
            merged_match = {
                "match_id": match_id,
                "live_data": self.parse_live_data(live_match),
                "match_details": self.extract_match_details(match_detail_data, home_team_data, away_team_data, competition_data, countries_data),
                "home_team": self.extract_team_info(home_team_data),
                "away_team": self.extract_team_info(away_team_data),
                "competition": self.extract_competition_info(competition_data),
                "odds": self.extract_odds_data(odds_data)
            }
            
            merged_matches.append(merged_match)
        
        # Create final merged structure with complete passthrough
        merged_data = {
            "SOURCE_ALL_API_HEADER": latest_fetch.get("FETCH_HEADER", {}),
            "SOURCE_RAW_API_DATA": raw_data,  # Complete original raw data
            "MERGED_MATCH_CENTRIC_DATA": {
                "matches": merged_matches,
                "reference_data": {
                    "countries": countries_data,
                    "raw_all_teams": list(teams_dict.values()),
                    "raw_all_competitions": list(comps_dict.values())
                }
            },
            "SOURCE_ALL_API_FOOTER": latest_fetch.get("FETCH_FOOTER", {})
        }
        
        # Calculate merge completion time
        merge_end_time = time.time()
        merge_duration = merge_end_time - merge_start_time
        
        # Analyze match statistics
        match_stats = self.analyze_match_stats(merged_data)
        
        # Log the merged data
        self.logger.log_fetch(merged_data, merge_duration, match_stats)
        
        # Trigger pretty_print.py after merge completes
        self.trigger_pretty_print()
        
        return merged_data
    
    def trigger_pretty_print(self):
        """Trigger pretty_print.py to process the latest merge.json data"""
        try:
            import subprocess
            import sys
            
            # Run pretty_print.py as a subprocess to process the latest data
            pretty_print_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pretty_print', 'pretty_print.py')
            
            # Execute pretty_print.py with the current merge.json
            subprocess.run([sys.executable, pretty_print_script_path, '--single-run'], 
                          cwd=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pretty_print'),
                          check=False)  # Don't raise exception if pretty_print fails
            
        except Exception as e:
            print(f"Warning: Could not trigger pretty_print process: {e}")
            # Continue normal operation even if pretty_print fails

# Initialize the merger
sports_merger = SportsMerger()

# Main execution
if __name__ == "__main__":
    import signal
    import sys
    
    # Check for single-run mode (called by all_api.py)
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        # Single execution mode - just do one merge and exit
        try:
            result = asyncio.run(sports_merger.merge_sports_data("../all_api/all_api.json"))
            print(f"Single merge completed! Logged to: {sports_merger.logger.log_path}")
        except Exception as e:
            print(f"Single merge failed: {e}")
        sys.exit(0)
    
    # Global flag for graceful shutdown (continuous mode)
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous merge...")
        running = False
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_merge():
        global running
        merge_count = 0
        
        print("Starting Sports Data Continuous Merge Cycle...")
        print("Merging every 60 seconds from all_api.json")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            merge_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Merge #{merge_count}] Starting at {sports_merger.logger.get_nyc_timestamp()}")
                
                # Perform the merge
                result = asyncio.run(sports_merger.merge_sports_data("../all_api/all_api.json"))
                
                # Calculate merge duration
                end_time = time.time()
                merge_duration = end_time - start_time
                
                print(f"[Merge #{merge_count}] Completed in {merge_duration:.2f} seconds")
                print(f"[Merge #{merge_count}] Logged to: {sports_merger.logger.log_path}")
                
                # Calculate wait time (60 seconds total cycle time)
                target_interval = 60
                wait_time = max(0, target_interval - merge_duration)
                
                if wait_time > 0:
                    print(f"[Merge #{merge_count}] Waiting {wait_time:.2f} seconds until next merge...")
                    
                    # Wait in small increments to allow for graceful shutdown
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        time.sleep(0.5)  # Check every 0.5 seconds
                else:
                    print(f"[Merge #{merge_count}] Merge took longer than 60s, starting next merge immediately")
                
            except Exception as e:
                print(f"[Merge #{merge_count}] Error occurred: {e}")
                print(f"[Merge #{merge_count}] Waiting 60 seconds before retry...")
                
                # Wait before retry
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    time.sleep(0.5)
        
        print("\nContinuous merge stopped. Goodbye!")
    
    # Run the continuous merge
    try:
        continuous_merge()
    except KeyboardInterrupt:
        print("\nShutdown complete.")