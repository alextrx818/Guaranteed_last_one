# LOGGING ANALYSIS REFERENCE: See logging_indepth_analysis.md for comprehensive independent analysis methodology
import json
import logging
import os
import time
from datetime import datetime
import pytz
import sys
sys.path.append('../shared_utils')
from persistent_state import PersistentStateManager

class PrettyPrintLogger:
    def __init__(self, log_dir="pretty_print_log", max_fetches=50):
        # Simple S3 delegation - no local state needed
        print(f"[Pretty Print Logger] Initialized - delegates to S3 external script")
    
    def log_fetch(self, merged_data, fetch_id, nyc_timestamp):
        """Delegate to external S3 script for logging"""
        try:
            import subprocess
            import tempfile
            
            print(f"[Pretty Print Logger] Starting delegation - fetch_id: {fetch_id}")
            
            # Create temp file with log data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                log_data = {
                    "cleaned_data": merged_data,
                    "fetch_id": fetch_id,
                    "nyc_timestamp": nyc_timestamp
                }
                json.dump(log_data, temp_file)
                temp_file_path = temp_file.name
            
            print(f"[Pretty Print Logger] Created temp file: {temp_file_path}")
            
            # Execute external S3 script
            script_path = os.path.join(os.path.dirname(__file__), 'pretty_print_rotating_s3.py')
            print(f"[Pretty Print Logger] Calling S3 script: {script_path}")
            
            result = subprocess.run([
                sys.executable, script_path, temp_file_path
            ], capture_output=True, text=True)
            
            print(f"[Pretty Print Logger] S3 script return code: {result.returncode}")
            if result.stdout:
                print(f"[Pretty Print Logger] S3 script stdout: {result.stdout}")
            if result.stderr:
                print(f"[Pretty Print Logger] S3 script stderr: {result.stderr}")
            
            if result.returncode != 0:
                print(f"[Pretty Print Logger] S3 script failed with code {result.returncode}")
            else:
                print(f"[Pretty Print Logger] S3 delegation successful")
                
        except Exception as e:
            print(f"[Pretty Print Logger] Error delegating to S3: {e}")
    
    def rotate_log(self):
        # No-op - rotation handled by S3 script
        pass

class PrettyPrintProcessor:
    def __init__(self):
        self.logger = PrettyPrintLogger()
    
    def find_unprocessed_fetch_id(self):
        """Find the next unprocessed fetch ID from tracking file"""
        tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
        
        try:
            with open(tracking_file, 'r') as f:
                content = f.read()
            
            print(f"[Pretty Print DEBUG] Reading tracking file...")
            
            # Split by closing brace to get individual entries
            entries = content.split('}\n{')
            print(f"[Pretty Print DEBUG] Found {len(entries)} entries in tracking file")
            
            unprocessed_entries = []
            for i, entry_str in enumerate(entries):
                # Fix JSON formatting for middle entries
                if i > 0:
                    entry_str = '{' + entry_str
                if i < len(entries) - 1:
                    entry_str = entry_str + '}'
                
                try:
                    entry = json.loads(entry_str)
                    if entry.get("pretty_print.py") == "":  # Not processed yet
                        unprocessed_entries.append(entry)
                        print(f"[Pretty Print DEBUG] Found unprocessed entry: {entry.get('fetch_id')}")
                except json.JSONDecodeError:
                    continue
            
            print(f"[Pretty Print DEBUG] Found {len(unprocessed_entries)} unprocessed entries")
            
            # Return the NEWEST unprocessed entry (last in the list)
            if unprocessed_entries:
                fetch_id = unprocessed_entries[-1].get("fetch_id")
                print(f"[Pretty Print DEBUG] Returning fetch_id: {fetch_id}")
                return fetch_id
            
            print(f"[Pretty Print DEBUG] No unprocessed entries found")
            return None  # Nothing to process
        except Exception as e:
            print(f"[Pretty Print DEBUG] Error reading tracking file: {e}")
            return None
    
    def extract_fetch_data_by_id(self, fetch_id, input_file_path):
        """Extract complete fetch data between header and footer markers"""
        try:
            with open(input_file_path, 'r') as f:
                content = f.read()
            
            print(f"[Pretty Print DEBUG] Looking for fetch_id: {fetch_id} in {input_file_path}")
            
            # Find start marker - match the format used in merge.json with fetch number
            start_marker = f'| {fetch_id} |'  # This will match "| wBaabkhI3x78 |" pattern
            start_pos = content.find(start_marker)
            
            if start_pos == -1:
                print(f"[Pretty Print DEBUG] Start marker not found: {start_marker}")
                return None
            
            print(f"[Pretty Print DEBUG] Found start marker at position: {start_pos}")
            
            # Find end marker - same pattern for end
            end_marker = f'| {fetch_id} |'  # Same pattern for end
            end_pos = content.find(end_marker, start_pos + len(start_marker))  # Find NEXT occurrence
            
            if end_pos == -1:
                print(f"[Pretty Print DEBUG] End marker not found: {end_marker}")
                return None
            
            print(f"[Pretty Print DEBUG] Found end marker at position: {end_pos}")
            
            # Extract JSON between markers
            fetch_section = content[start_pos:end_pos]
            json_start = fetch_section.find('\n{')
            json_end = fetch_section.rfind('\n}') + 2
            
            if json_start == -1 or json_end == -1:
                print(f"[Pretty Print DEBUG] Could not find JSON boundaries")
                return None
            
            json_content = fetch_section[json_start:json_end]
            print(f"[Pretty Print DEBUG] Successfully extracted JSON data")
            return json.loads(json_content)
            
        except Exception as e:
            print(f"[Pretty Print DEBUG] Error extracting fetch data for {fetch_id}: {e}")
            return None
    
    def mark_fetch_completed(self, fetch_id):
        """Mark fetch as completed in tracking file"""
        tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
        
        try:
            # Read all entries
            with open(tracking_file, 'r') as f:
                content = f.read()
            
            # Split by closing brace to get individual entries
            entries = content.split('}\n{')
            
            updated_entries = []
            for i, entry_str in enumerate(entries):
                # Fix JSON formatting for middle entries
                if i > 0:
                    entry_str = '{' + entry_str
                if i < len(entries) - 1:
                    entry_str = entry_str + '}'
                
                try:
                    entry = json.loads(entry_str)
                    if entry.get("fetch_id") == fetch_id:
                        entry["pretty_print.py"] = "completed"
                    updated_entries.append(json.dumps(entry, indent=2))
                except json.JSONDecodeError:
                    continue
            
            # Write back updated entries
            with open(tracking_file, 'w') as f:
                f.write('\n'.join(updated_entries) + '\n')
                
        except Exception as e:
            print(f"Error marking fetch {fetch_id} as completed: {e}")
    
    def process_merged_data(self, merge_data_path):
        """Preserve enriched match data but remove raw reference data groups"""
        
        # Find unprocessed fetch ID using new tracking system
        fetch_id = self.find_unprocessed_fetch_id()
        if not fetch_id:
            return {"error": "No unprocessed fetch IDs found"}
        
        # Extract complete fetch data by ID
        latest_merge = self.extract_fetch_data_by_id(fetch_id, merge_data_path)
        if not latest_merge:
            return {"error": f"Could not extract data for fetch ID: {fetch_id}"}
        
        # Remove raw reference data groups while preserving enriched match data
        cleaned_data = self.clean_reference_data(latest_merge)
        
        # Log the cleaned data (preserves all enriched fields like team names, competition names)
        from datetime import datetime
        import pytz
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        nyc_timestamp = nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
        
        self.logger.log_fetch(cleaned_data, fetch_id, nyc_timestamp)
        
        # Mark fetch as completed in tracking file
        self.mark_fetch_completed(fetch_id)
        
        # Trigger pretty_print_conversion.py after pretty_print completes
        self.trigger_pretty_conversion()
        
        return cleaned_data
    
    def clean_reference_data(self, merged_data):
        """Remove raw countries, teams, competitions groups but preserve enriched match data"""
        try:
            import copy
            cleaned_data = copy.deepcopy(merged_data)
            
            # Remove reference_data section (raw countries, teams, competitions bulk data)
            if ("MERGED_DATA" in cleaned_data and 
                "MERGED_MATCH_CENTRIC_DATA" in cleaned_data["MERGED_DATA"] and
                "reference_data" in cleaned_data["MERGED_DATA"]["MERGED_MATCH_CENTRIC_DATA"]):
                del cleaned_data["MERGED_DATA"]["MERGED_MATCH_CENTRIC_DATA"]["reference_data"]
            
            # Remove raw teams, competitions, countries from SOURCE_RAW_API_DATA  
            if ("MERGED_DATA" in cleaned_data and 
                "SOURCE_RAW_API_DATA" in cleaned_data["MERGED_DATA"]):
                raw_api_data = cleaned_data["MERGED_DATA"]["SOURCE_RAW_API_DATA"]
                
                # Remove bulk raw data but keep live match data and odds
                if "teams" in raw_api_data:
                    del raw_api_data["teams"]
                if "competitions" in raw_api_data:
                    del raw_api_data["competitions"]
                if "countries" in raw_api_data:
                    del raw_api_data["countries"]
                
                # Filter odds data to prioritize Bet365 (company ID "2")
                if "match_odds" in raw_api_data:
                    raw_api_data["match_odds"] = self.filter_odds_companies(raw_api_data["match_odds"])
            
            # Clean individual match raw data while preserving enriched fields
            if ("MERGED_DATA" in cleaned_data and 
                "MERGED_MATCH_CENTRIC_DATA" in cleaned_data["MERGED_DATA"] and
                "matches" in cleaned_data["MERGED_DATA"]["MERGED_MATCH_CENTRIC_DATA"]):
                
                matches = cleaned_data["MERGED_DATA"]["MERGED_MATCH_CENTRIC_DATA"]["matches"]
                for match in matches:
                    # Remove raw_team_data but keep parsed_team with enriched names
                    if "home_team" in match and match["home_team"] and "raw_team_data" in match["home_team"]:
                        del match["home_team"]["raw_team_data"]
                    if "away_team" in match and match["away_team"] and "raw_team_data" in match["away_team"]:
                        del match["away_team"]["raw_team_data"]
                    
                    # Remove raw_competition_data but keep parsed_competition with enriched names
                    if "competition" in match and match["competition"] and "raw_competition_data" in match["competition"]:
                        del match["competition"]["raw_competition_data"]
                    
                    # Remove raw_match_details but keep parsed_details with enriched names
                    if "match_details" in match and match["match_details"] and "raw_match_details" in match["match_details"]:
                        del match["match_details"]["raw_match_details"]
                    
                    # Remove raw_odds_data but keep essential odds info
                    if "odds" in match and match["odds"] and "raw_odds_data" in match["odds"]:
                        del match["odds"]["raw_odds_data"]
                    
                    # Filter incidents to only show VAR incidents (type 28)
                    if "live_data" in match and "incidents" in match["live_data"]:
                        match["live_data"]["incidents"] = self.filter_incidents(match["live_data"]["incidents"])
                    
                    # Remove stats and tlive arrays from live_data
                    if "live_data" in match:
                        if "stats" in match["live_data"]:
                            del match["live_data"]["stats"]
                        if "tlive" in match["live_data"]:
                            del match["live_data"]["tlive"]
            
            # NOTE: Preserves all enriched data in matches including:
            # - home_team_name, away_team_name (from team enrichment)
            # - competition_name, country_name (from competition enrichment) 
            # - All live match data, odds, and match details
            # But removes all the raw API response data that was only used for enrichment
            # And filters odds to show only Bet365 (company ID "2") when available
            
            return cleaned_data
            
        except Exception as e:
            print(f"Warning: Could not clean reference data: {e}")
            return merged_data
    
    def filter_odds_companies(self, match_odds):
        """Filter odds to prioritize Bet365 (company ID "2"), fallback to next available"""
        filtered_odds = []
        
        for odds_item in match_odds:
            if isinstance(odds_item, dict) and "results" in odds_item:
                results = odds_item["results"]
                filtered_results = {}
                
                # Priority 1: Check for Bet365 (company ID "2")
                if "2" in results:
                    bet365_data = results["2"]
                    if self.has_valid_odds_data(bet365_data):
                        filtered_results["2"] = self.filter_odds_by_time_and_score(bet365_data)
                
                # If Bet365 not available or invalid, get next best company
                if not filtered_results:
                    for company_id, company_data in results.items():
                        if self.has_valid_odds_data(company_data):
                            filtered_results[company_id] = self.filter_odds_by_time_and_score(company_data)
                            break  # Take first valid company as fallback
                
                # Update odds item with filtered results
                if filtered_results:
                    filtered_item = odds_item.copy()
                    filtered_item["results"] = filtered_results
                    filtered_odds.append(filtered_item)
                else:
                    # Keep original if no valid data found
                    filtered_odds.append(odds_item)
            else:
                # Keep non-standard items as-is
                filtered_odds.append(odds_item)
        
        return filtered_odds
    
    def has_valid_odds_data(self, company_data):
        """Check if company has valid odds data in any market"""
        if not isinstance(company_data, dict):
            return False
        
        # Check for valid data in common market types
        market_types = ["asia", "eu", "ou", "corner", "bs"]
        for market in market_types:
            if market in company_data and isinstance(company_data[market], list) and len(company_data[market]) > 0:
                return True
        
        return False
    
    def filter_odds_by_time_and_score(self, company_data):
        """Filter odds by minutes 0-10, no duplicates, only 0-0 score, rename markets"""
        if not isinstance(company_data, dict):
            return company_data
        
        filtered_company_data = {}
        
        # Market name mappings
        market_mappings = {
            "asia": "Spread",
            "eu": "MoneyLine", 
            "bs": "O/U",
            "cr": "Corners"
        }
        
        for market_name, odds_array in company_data.items():
            if not isinstance(odds_array, list):
                continue
                
            # Get new market name
            new_market_name = market_mappings.get(market_name, market_name)
            
            # Track seen minutes to avoid duplicates
            seen_minutes = set()
            filtered_odds = []
            goal_scored_detected = False
            
            # Process odds in chronological order (reverse since newest are first)
            for odds_entry in reversed(odds_array):
                if not isinstance(odds_entry, list) or len(odds_entry) < 8:
                    continue
                
                minute_str = str(odds_entry[1])  # Field 1: Minutes elapsed
                score = odds_entry[7]  # Field 7: Current score
                
                # Check if score is 0-0 (goal scored check)
                if score != "0-0":
                    goal_scored_detected = True
                    continue
                
                # Filter by minutes 0-10
                if minute_str == "":
                    # Pre-match - always include if not seen
                    minute_key = "prematch"
                elif minute_str.isdigit():
                    minute_num = int(minute_str)
                    if minute_num > 10:
                        continue
                    minute_key = minute_str
                else:
                    continue
                
                # Skip if we've already seen this minute
                if minute_key in seen_minutes:
                    continue
                
                seen_minutes.add(minute_key)
                
                # Create filtered odds entry (remove fields 5, 6, 7)
                filtered_entry = [
                    odds_entry[0],  # Field 0: Timestamp
                    odds_entry[1],  # Field 1: Minutes elapsed
                    odds_entry[2],  # Field 2: First odds value
                    odds_entry[3],  # Field 3: Middle value (handicap/draw/total)
                    odds_entry[4]   # Field 4: Second odds value
                ]
                
                filtered_odds.append(filtered_entry)
            
            # If goal was scored, add message instead of odds
            if goal_scored_detected and not filtered_odds:
                filtered_company_data[new_market_name] = "Goal scored - odds invalid"
            elif filtered_odds:
                # Sort by minute (pre-match first, then 0-10)
                filtered_odds.sort(key=lambda x: -1 if x[1] == "" else int(x[1]))
                filtered_company_data[new_market_name] = filtered_odds
        
        return filtered_company_data
    
    def filter_incidents(self, incidents):
        """Filter incidents to only show VAR incidents (type 28) with only essential fields"""
        if not isinstance(incidents, list):
            return incidents
        
        # Filter to only include incident type 28 (VAR incidents) with only 3 fields
        var_incidents = []
        for incident in incidents:
            if isinstance(incident, dict) and incident.get("type") == 28:
                # Keep only type, var_reason, and var_result fields
                filtered_incident = {
                    "type": incident.get("type"),
                    "var_reason": incident.get("var_reason"),
                    "var_result": incident.get("var_result")
                }
                var_incidents.append(filtered_incident)
        
        return var_incidents
    
    def trigger_pretty_conversion(self):
        """Trigger pretty_print_conversion.py to process the latest pretty_print.json data"""
        try:
            import subprocess
            import sys
            
            # Run pretty_print_conversion.py as a subprocess to process the latest data
            pretty_conversion_script_path = os.path.join(os.path.dirname(__file__), '..', '5_pretty_print_conversion', 'pretty_print_conversion.py')
            
            print(f"[Pretty Print DEBUG] Calling pretty_print_conversion.py at: {pretty_conversion_script_path}")
            
            # Execute pretty_print_conversion.py with the current pretty_print.json
            result = subprocess.run([sys.executable, pretty_conversion_script_path, '--single-run'], 
                          cwd=os.path.join(os.path.dirname(__file__), '..', '5_pretty_print_conversion'),
                          check=False, capture_output=True, text=True)  # Capture output for debugging
            
            print(f"[Pretty Print DEBUG] Conversion return code: {result.returncode}")
            if result.stdout:
                print(f"[Pretty Print DEBUG] Conversion stdout: {result.stdout}")
            if result.stderr:
                print(f"[Pretty Print DEBUG] Conversion stderr: {result.stderr}")
            
        except Exception as e:
            print(f"[Pretty Print DEBUG] Error triggering pretty_conversion: {e}")
            # Continue normal operation even if pretty_conversion fails

# Initialize the processor
pretty_print_processor = PrettyPrintProcessor()

# Main execution
if __name__ == "__main__":
    import sys
    
    # Check for single-run mode (called by merge.py)
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        # Single execution mode - just do one pass-through and exit
        try:
            result = pretty_print_processor.process_merged_data("../3_merge/merge.json")
            print(f"Single pretty-print completed! Data delegated to S3 logger.")
        except Exception as e:
            print(f"Single pretty-print failed: {e}")
        sys.exit(0)
    
    # Continuous mode (if run standalone)
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous pretty-print...")
        running = False
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_pretty_print():
        global running
        pretty_print_count = 0
        
        print("Starting Pretty Print Continuous Pass-Through...")
        print("Processing every 60 seconds from merge.json")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            pretty_print_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Pretty Print #{pretty_print_count}] Starting pass-through...")
                
                # Perform the pass-through
                result = pretty_print_processor.process_merged_data("../3_merge/merge.json")
                
                # Calculate duration
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"[Pretty Print #{pretty_print_count}] Completed in {duration:.2f} seconds")
                print(f"[Pretty Print #{pretty_print_count}] Data delegated to S3 logger")
                
                # Calculate wait time (60 seconds total cycle time)
                target_interval = 60
                wait_time = max(0, target_interval - duration)
                
                if wait_time > 0:
                    print(f"[Pretty Print #{pretty_print_count}] Waiting {wait_time:.2f} seconds...")
                    
                    # Wait in small increments to allow for graceful shutdown
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        time.sleep(0.5)
                else:
                    print(f"[Pretty Print #{pretty_print_count}] Starting next pass-through immediately")
                
            except Exception as e:
                print(f"[Pretty Print #{pretty_print_count}] Error occurred: {e}")
                print(f"[Pretty Print #{pretty_print_count}] Waiting 60 seconds before retry...")
                
                # Wait before retry
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    time.sleep(0.5)
        
        print("\nContinuous pretty-print stopped. Goodbye!")
    
    # Run the continuous pretty-print
    try:
        continuous_pretty_print()
    except KeyboardInterrupt:
        print("\nShutdown complete.")