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
    
    def log_fetch(self, monitor_data):
        """Pure catch-all pass-through logging with NYC timestamps"""
        self.fetch_count += 1
        nyc_timestamp = self.get_nyc_timestamp()
        
        # Add NYC timestamp to the data
        log_entry = {
            "ALERT_3OU_HEADER": {
                "fetch_number": self.fetch_count,
                "nyc_timestamp": nyc_timestamp,
                "fetch_start": "=== ALERT 3OU HALF DATA START ==="
            },
            "FILTERED_DATA": monitor_data,  # The filtered data
            "ALERT_3OU_FOOTER": {
                "nyc_timestamp": nyc_timestamp,
                "fetch_end": "=== ALERT 3OU HALF DATA END ==="
            }
        }
        
        # Save state after each fetch
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Write to rotating log
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Append to main alert_3ou_half.json file
        with open('alert_3ou_half.json', 'a') as f:
            json.dump(log_entry, f, indent=2)
            f.write('\n')
        
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
        
        # Read latest monitor from monitor_central.json (last line)
        with open(monitor_data_path, 'r') as f:
            lines = f.readlines()
        
        # Get the latest monitor data (last line)
        if not lines:
            return {"error": "No valid data in monitor_central.json"}
        
        try:
            latest_monitor = json.loads(lines[-1].strip())
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in latest monitor"}
        
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
        
        # Log the filtered data
        self.logger.log_fetch(filtered_data)
        
        # Trigger alert_underdog_0half.py after alert_3ou_half completes
        self.trigger_underdog_alert()
        
        return filtered_data
    
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
        """DUPLICATE PREVENTION: Read own log to find already-logged match IDs"""
        try:
            with open('alert_3ou_half.json', 'r') as f:
                data = json.load(f)
            existing_ids = set()
            for entry in data:
                for match in entry.get("monitor_central_display", []):
                    match_id = match.get("match_info", {}).get("match_id")
                    if match_id:
                        existing_ids.add(match_id)
            return existing_ids
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # If file doesn't exist or is corrupted, return empty set
            return set()
    
    def remove_duplicates(self, filtered_matches):
        """DUPLICATE PREVENTION: Remove matches already in log"""
        existing_ids = self.get_existing_match_ids()
        new_matches = []
        
        for match in filtered_matches:
            match_id = match.get("match_info", {}).get("match_id")
            if match_id not in existing_ids:
                new_matches.append(match)
                
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