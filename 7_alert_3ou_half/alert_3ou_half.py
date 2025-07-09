# LOGGING ANALYSIS REFERENCE: See logging_indepth_analysis.md for comprehensive independent analysis methodology
import json
import logging
import os
import time
from datetime import datetime
import pytz
import requests
import sys
sys.path.append('../shared_utils')
from persistent_state import PersistentStateManager

class Alert3OUHalfLogger:
    def __init__(self, log_dir="Alert_log/alert_3ou_half", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.state_manager = PersistentStateManager("alert_3ou_half", max_fetches)
        self.fetch_count, self.accumulated_data = self.state_manager.load_state()
        self.setup_logging()
    
    def get_nyc_timestamp(self):
        """Get current NYC timezone timestamp in MM/DD/YYYY format with AM/PM"""
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        return nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"alert_3ou_half_log_{timestamp}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
    
    def log_fetch_qualifying_only(self, filtered_matches, fetch_id, nyc_timestamp):
        """CLEAN LOGGING: Only log when matches meet criteria - raw match data only"""
        if not filtered_matches or len(filtered_matches) == 0:
            # Don't log anything if no matches meet criteria
            return
        
        self.fetch_count += 1
        
        # Save state after each fetch (for rotation tracking)
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Write to rotating log (keep for internal tracking)
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # CLEAN LOGGING: Only the essential data
        with open('alert_3ou_half.json', 'a') as f:
            f.write(f'=== FETCH START: {fetch_id} | {nyc_timestamp} ===\n')
            
            # Log each qualifying match individually - raw format only
            for match in filtered_matches:
                json.dump(match, f, indent=2)
                f.write('\n')
            
            f.write(f'=== FETCH END: {fetch_id} | {nyc_timestamp} ===\n')
        
        # Check for rotation
        if self.state_manager.should_rotate(self.fetch_count):
            self.rotate_log()
    
    def rotate_log(self):
        # Save current accumulated data to rotated log before clearing
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Reset state
        self.state_manager.reset_state()
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
        # Clear the main alert_3ou_half.json file
        open('alert_3ou_half.json', 'w').close()

class Alert3OUHalfProcessor:
    def __init__(self):
        self.logger = Alert3OUHalfLogger()
    
    def find_unprocessed_fetch_id(self):
        """Find the next unprocessed fetch ID from tracking file"""
        tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
        
        try:
            with open(tracking_file, 'r') as f:
                content = f.read()
            
            # Split by closing brace to get individual entries
            entries = content.split('}\n{')
            
            unprocessed_entries = []
            for i, entry_str in enumerate(entries):
                # Fix JSON formatting for middle entries
                if i > 0:
                    entry_str = '{' + entry_str
                if i < len(entries) - 1:
                    entry_str = entry_str + '}'
                
                try:
                    entry = json.loads(entry_str)
                    # Only process if monitor_central.py is completed but alert_3ou_half.py is not
                    if (entry.get("monitor_central.py") == "completed" and 
                        entry.get("alert_3ou_half.py") == ""):
                        unprocessed_entries.append(entry)
                except json.JSONDecodeError:
                    continue
            
            # Return the NEWEST unprocessed entry (last in the list)
            if unprocessed_entries:
                return unprocessed_entries[-1].get("fetch_id")
            
            return None  # Nothing to process
        except Exception as e:
            print(f"Error reading tracking file: {e}")
            return None
    
    def extract_fetch_data_by_id(self, fetch_id, input_file_path):
        """Extract complete fetch data between header and footer markers"""
        try:
            with open(input_file_path, 'r') as f:
                content = f.read()
            
            # Find start marker
            start_marker = f'=== FETCH START: {fetch_id} |'
            start_pos = content.find(start_marker)
            
            if start_pos == -1:
                return None
            
            # Find end marker
            end_marker = f'=== FETCH END: {fetch_id} |'
            end_pos = content.find(end_marker, start_pos)
            
            if end_pos == -1:
                return None
            
            # Extract JSON between markers
            fetch_section = content[start_pos:end_pos]
            json_start = fetch_section.find('\n{')
            json_end = fetch_section.rfind('\n}') + 2
            
            if json_start == -1 or json_end == -1:
                return None
            
            json_content = fetch_section[json_start:json_end]
            return json.loads(json_content)
            
        except Exception as e:
            print(f"Error extracting fetch data for {fetch_id}: {e}")
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
                        entry["alert_3ou_half.py"] = "completed"
                    updated_entries.append(json.dumps(entry, indent=2))
                except json.JSONDecodeError:
                    continue
            
            # Write back updated entries
            with open(tracking_file, 'w') as f:
                f.write('\n'.join(updated_entries) + '\n')
                
        except Exception as e:
            print(f"Error marking fetch {fetch_id} as completed: {e}")
    
    # ===== TELEGRAM MESSAGING MODULE - ISOLATED SECTION =====
    def send_telegram_alert(self, filtered_matches):
        """Send telegram alert for 3OU half matches - completely separate from main logic"""
        if not filtered_matches:
            return
            
        TELEGRAM_BOT_TOKEN = '7848696790:AAFhzVNuNsL_hUvsZMabpCUz2RVRhc0PMo8'
        TELEGRAM_CHAT_ID = '6128359776'
        
        try:
            alerts = self.format_telegram_message(filtered_matches)
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            # Send each alert individually
            for alert in alerts:
                payload = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': alert,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Telegram alert sent for individual 3OU half match")
                else:
                    print(f"❌ Telegram alert failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Telegram alert error: {e}")
    
    def format_telegram_message(self, matches):
        """Format 3OU half matches for telegram - individual match format only"""
        # Always send individual alerts for each match
        alerts = []
        for match in matches:
            match_info = match.get("match_info", {})
            odds = match.get("odds", {})
            ou_total = odds.get("O/U", [{}])[0].get("Total", "N/A")
            
            alert = (f"🔔 *3OU HALF ALERT*\n\n"
                    f"⚽ {match_info.get('home_team', 'Unknown')} vs {match_info.get('away_team', 'Unknown')}\n"
                    f"🏆 {match_info.get('competition_name', 'Unknown')}\n"
                    f"📊 {match_info.get('live_score', 'N/A')}\n"
                    f"🎯 O/U Total: {ou_total}\n"
                    f"⏰ {datetime.now().strftime('%I:%M:%S %p')}")
            alerts.append(alert)
        
        return alerts
    # ===== END TELEGRAM MODULE =====
    
    def process_monitor_data(self, monitor_data_path):
        """Filter matches: Status 3 (Half-time), 0-0 score, O/U Total >= 3.0"""
        
        # Find unprocessed fetch ID using new tracking system
        fetch_id = self.find_unprocessed_fetch_id()
        if not fetch_id:
            return {"error": "No unprocessed fetch IDs found"}
        
        # Extract complete fetch data by ID
        latest_monitor = self.extract_fetch_data_by_id(fetch_id, monitor_data_path)
        if not latest_monitor:
            return {"error": f"Could not extract data for fetch ID: {fetch_id}"}
        
        try:
            # Filter matches based on criteria
            filtered_matches = self.filter_matches(latest_monitor.get("monitor_central_display", []))
            
            # Create filtered data structure
            filtered_data = latest_monitor.copy()
            filtered_data["monitor_central_display"] = filtered_matches
            filtered_data["filtered_match_count"] = len(filtered_matches)
            
            # Send telegram alert ONLY for NEW matches (after duplicate removal)
            if len(filtered_matches) > 0:
                # Send individual alert for each match
                for match in filtered_matches:
                    self.send_telegram_alert([match])
            
            # CLEAN LOGGING: Only log when matches meet criteria
            from datetime import datetime
            import pytz
            nyc_tz = pytz.timezone('America/New_York')
            nyc_time = datetime.now(nyc_tz)
            nyc_timestamp = nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
            
            # Use new clean logging method - only logs if filtered_matches has content
            self.logger.log_fetch_qualifying_only(filtered_matches, fetch_id, nyc_timestamp)
            
            # Mark fetch as completed in tracking file
            self.mark_fetch_completed(fetch_id)
            
            # Trigger alert_underdog_0half.py after alert_3ou_half completes
            self.trigger_underdog_alert()
            
            return filtered_data
        except Exception as e:
            print(f"Error processing alert_3ou_half data: {e}")
            return {"error": f"Processing failed: {e}"}
    
    def trigger_underdog_alert(self):
        """Trigger alert_underdog_0half.py to process the latest monitor_central.json data"""
        try:
            import subprocess
            import sys
            
            # Run alert_underdog_0half.py as a subprocess to process the latest data
            underdog_script_path = os.path.join(os.path.dirname(__file__), '..', '8_alert_underdog_0half', 'alert_underdog_0half.py')
            
            # Execute alert_underdog_0half.py with the current monitor_central.json
            subprocess.run([sys.executable, underdog_script_path, '--single-run'], 
                          cwd=os.path.join(os.path.dirname(__file__), '..', '8_alert_underdog_0half'),
                          check=False)  # Don't raise exception if underdog alert fails
            
        except Exception as e:
            print(f"Warning: Could not trigger underdog alert process: {e}")
            # Continue normal operation even if underdog alert fails
    
    # ==========================================
    # DUPLICATE PREVENTION LOGIC - SEPARATE FROM MAIN LOGGING
    # This is ONLY for checking existing data to prevent re-logging
    # Does NOT modify the main logging mechanism
    # ==========================================
    
    def get_existing_match_ids(self):
        """DUPLICATE PREVENTION: Read own log to find already-alerted match IDs"""
        try:
            with open('alert_3ou_half.json', 'r') as f:
                content = f.read()
            
            existing_ids = set()
            
            # Parse bookended format to extract JSON entries
            fetch_sections = content.split('=== FETCH START:')
            for section in fetch_sections[1:]:  # Skip first empty section
                try:
                    # Find the JSON content between start and end markers
                    json_start = section.find('\n{')
                    json_end = section.find('\n=== FETCH END:')
                    
                    if json_start != -1 and json_end != -1:
                        json_content = section[json_start:json_end].strip()
                        
                        # CLEAN LOGGING FORMAT: Handle multiple JSON objects (raw match data)
                        # Split by }\n{ to get individual match objects
                        json_objects = json_content.split('}\n{')
                        
                        for i, json_obj in enumerate(json_objects):
                            # Fix JSON formatting for middle objects
                            if i > 0:
                                json_obj = '{' + json_obj
                            if i < len(json_objects) - 1:
                                json_obj = json_obj + '}'
                            
                            try:
                                entry_data = json.loads(json_obj)
                                
                                # Extract match IDs from clean logging format (raw match data)
                                if isinstance(entry_data, dict) and "match_info" in entry_data:
                                    match_info = entry_data.get("match_info", {})
                                    match_id = match_info.get("match_id")
                                    if match_id:
                                        existing_ids.add(match_id)
                                        print(f"🔒 TRACKED MATCH ID: {match_id} - {match_info.get('home_team', 'Unknown')} vs {match_info.get('away_team', 'Unknown')}")
                                        
                            except json.JSONDecodeError:
                                continue
                                
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parse error in fetch section: {e}")
                    continue
            
            print(f"📊 DUPLICATE PREVENTION: Found {len(existing_ids)} previously alerted match IDs")
            return existing_ids
        except (FileNotFoundError, IOError):
            print("📝 DUPLICATE PREVENTION: No existing log file found - starting fresh")
            return set()
    
    def get_alerted_match_ids_persistent(self):
        """ADDITIONAL SAFETY: Read persistent alerted match IDs file"""
        alerted_file = 'alerted_match_ids.txt'
        try:
            with open(alerted_file, 'r') as f:
                ids = set(line.strip() for line in f if line.strip())
            print(f"🗃️ PERSISTENT TRACKING: Loaded {len(ids)} previously alerted match IDs")
            return ids
        except FileNotFoundError:
            print("🗃️ PERSISTENT TRACKING: No persistent file found - starting fresh")
            return set()
    
    def save_alerted_match_id_persistent(self, match_id, home_team, away_team):
        """ADDITIONAL SAFETY: Save match ID to persistent tracking file"""
        alerted_file = 'alerted_match_ids.txt'
        try:
            with open(alerted_file, 'a') as f:
                f.write(f"{match_id}\n")
            print(f"💾 PERSISTENT SAVE: {match_id} - {home_team} vs {away_team}")
        except Exception as e:
            print(f"⚠️ PERSISTENT SAVE ERROR: {e}")

    def remove_duplicates(self, filtered_matches):
        """ENHANCED DUPLICATE PREVENTION: Multi-layer check using log + persistent file"""
        # Layer 1: Check log file for previously alerted matches
        log_existing_ids = self.get_existing_match_ids()
        
        # Layer 2: Check persistent tracking file (safety net)
        persistent_existing_ids = self.get_alerted_match_ids_persistent()
        
        # Combine both sources
        all_existing_ids = log_existing_ids.union(persistent_existing_ids)
        
        new_matches = []
        
        print(f"🔍 DUPLICATE CHECK: Found {len(log_existing_ids)} IDs in log, {len(persistent_existing_ids)} in persistent file")
        print(f"🔍 DUPLICATE CHECK: Total {len(all_existing_ids)} unique existing match IDs")
        print(f"🔍 DUPLICATE CHECK: Checking {len(filtered_matches)} filtered matches")
        
        for match in filtered_matches:
            match_info = match.get("match_info", {})
            match_id = match_info.get("match_id")
            home_team = match_info.get("home_team", "Unknown")
            away_team = match_info.get("away_team", "Unknown")
            
            if match_id not in all_existing_ids:
                new_matches.append(match)
                print(f"✅ NEW MATCH: {home_team} vs {away_team} (ID: {match_id})")
                # Immediately save to persistent file to prevent race conditions
                self.save_alerted_match_id_persistent(match_id, home_team, away_team)
            else:
                print(f"🚫 DUPLICATE BLOCKED: {home_team} vs {away_team} (ID: {match_id})")
                
        print(f"🔍 DUPLICATE CHECK RESULT: {len(new_matches)} new matches after enhanced duplicate removal")
        return new_matches
    
    # ==========================================
    # END DUPLICATE PREVENTION - MAIN LOGIC CONTINUES UNCHANGED
    # ==========================================

    def filter_matches(self, matches):
        """Filter matches: Status 3 + Live Score 0-0 + O/U Total >= 3.0"""
        filtered = []
        
        for match in matches:
            # Check Status = 3 (Half-time)
            status = match.get("match_info", {}).get("status", "")
            if "Status ID: 3" not in status:
                continue
                
            # Check Live Score is 0-0 (HT: 0-0)
            live_score = match.get("match_info", {}).get("live_score", "")
            if live_score != "Live Score: 0-0 (HT: 0-0)":
                continue
                
            # Check O/U Total >= 3.0
            odds = match.get("odds", {})
            ou_odds = odds.get("O/U", [])
            if not ou_odds:
                continue
                
            # Get the Total from O/U odds
            total = None
            if isinstance(ou_odds, list) and len(ou_odds) > 0:
                total = ou_odds[0].get("Total")
                
            if total is None or float(total) < 3.0:
                continue
                
            # Match meets all criteria - add to filtered list
            filtered.append(match)
        
        # DUPLICATE PREVENTION: Remove already-logged matches
        filtered = self.remove_duplicates(filtered)
            
        return filtered

# Initialize the processor
alert_3ou_half_processor = Alert3OUHalfProcessor()

# Main execution
if __name__ == "__main__":
    import sys
    import signal
    
    # Check for single-run mode
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        # Single execution mode - just do one pass-through and exit
        try:
            result = alert_3ou_half_processor.process_monitor_data("../6_monitor_central/monitor_central.json")
            print(f"Single alert_3ou_half completed! Logged to: alert_3ou_half.json")
            
            # Auto-update results tracking
            try:
                from alert_3ou_half_results import AlertResultsTracker
                AlertResultsTracker().update_tracking_results()
            except Exception as e:
                print(f"Results tracking update failed: {e}")
        except Exception as e:
            print(f"Single alert_3ou_half failed: {e}")
        sys.exit(0)
    
    # Global flag for graceful shutdown (continuous mode)
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous alert_3ou_half...")
        running = False
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_alert_3ou_half():
        global running
        fetch_count = 0
        
        print("Starting Alert 3OU Half Continuous Pass-Through...")
        print("Processing every 60 seconds from monitor_central.json")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            fetch_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Fetch #{fetch_count}] Starting pass-through...")
                
                # Perform the pass-through
                result = alert_3ou_half_processor.process_monitor_data("../6_monitor_central/monitor_central.json")
                
                # Calculate duration
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"[Fetch #{fetch_count}] Completed in {duration:.2f} seconds")
                print(f"[Fetch #{fetch_count}] Logged to: alert_3ou_half.json")
                
                # Auto-update results tracking
                try:
                    from alert_3ou_half_results import AlertResultsTracker
                    AlertResultsTracker().update_tracking_results()
                except Exception as e:
                    print(f"Results tracking update failed: {e}")
                
                # Calculate wait time (60 seconds total cycle time)
                target_interval = 60
                wait_time = max(0, target_interval - duration)
                
                if wait_time > 0:
                    print(f"[Fetch #{fetch_count}] Waiting {wait_time:.2f} seconds...")
                    
                    # Wait in small increments to allow for graceful shutdown
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        time.sleep(0.5)
                else:
                    print(f"[Fetch #{fetch_count}] Starting next pass-through immediately")
                
            except Exception as e:
                print(f"[Fetch #{fetch_count}] Error occurred: {e}")
                print(f"[Fetch #{fetch_count}] Waiting 60 seconds before retry...")
                
                # Wait before retry
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    time.sleep(0.5)
        
        print("\nContinuous alert_3ou_half stopped. Goodbye!")
    
    # Run the continuous alert_3ou_half
    try:
        continuous_alert_3ou_half()
    except KeyboardInterrupt:
        print("\nShutdown complete.")