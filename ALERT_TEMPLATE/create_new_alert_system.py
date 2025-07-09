#!/usr/bin/env python3
"""
NEW ALERT SYSTEM TEMPLATE GENERATOR
Creates a complete, self-contained alert system with built-in results tracking
"""

import os
import json
from datetime import datetime

def create_alert_system(alert_name, criteria_description, output_dir_base="/root/Guaranteed_last_one"):
    """
    Create a complete, self-contained alert system
    
    Args:
        alert_name: Name of the alert (e.g., "alert_corners_5plus")
        criteria_description: Description of the alert criteria
        output_dir_base: Base directory for all alert systems
    """
    
    # Create directory structure
    alert_dir = f"{output_dir_base}/{alert_name}"
    os.makedirs(alert_dir, exist_ok=True)
    
    # Create the main alert processor
    create_main_alert_processor(alert_dir, alert_name, criteria_description)
    
    # Create the results tracker
    create_results_tracker(alert_dir, alert_name)
    
    # Create configuration file
    create_config_file(alert_dir, alert_name, criteria_description)
    
    # Create README
    create_readme(alert_dir, alert_name, criteria_description)
    
    # Create run script
    create_run_script(alert_dir, alert_name)
    
    print(f"✅ Created complete alert system: {alert_dir}")
    print(f"📁 Files created:")
    print(f"   - {alert_name}.py (main alert processor)")
    print(f"   - {alert_name}_results.py (results tracker)")
    print(f"   - {alert_name}_config.json (configuration)")
    print(f"   - run_{alert_name}.py (runner script)")
    print(f"   - README.md (documentation)")
    
    return alert_dir

def create_main_alert_processor(alert_dir, alert_name, criteria_description):
    """Create the main alert processor file"""
    
    template = f'''#!/usr/bin/env python3
"""
{alert_name.upper()} ALERT SYSTEM
{criteria_description}

SELF-CONTAINED: No dependencies on other alert systems
COMPLETE: Built-in logging, duplicate prevention, and Telegram alerts
"""

import json
import os
import time
from datetime import datetime
import pytz
import requests
import sys

# Add shared utilities
sys.path.append('../shared_utils')
from persistent_state import PersistentStateManager

class {alert_name.title().replace('_', '')}Logger:
    def __init__(self, log_dir="Alert_log/{alert_name}", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.state_manager = PersistentStateManager("{alert_name}", max_fetches)
        self.fetch_count, self.accumulated_data = self.state_manager.load_state()
        self.setup_logging()
    
    def get_nyc_timestamp(self):
        """Get current NYC timezone timestamp"""
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        return nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{alert_name}_log_{{timestamp}}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
    
    def log_fetch_qualifying_only(self, filtered_matches, fetch_id, nyc_timestamp):
        """CLEAN LOGGING: Only log when matches meet criteria - raw match data only"""
        if not filtered_matches or len(filtered_matches) == 0:
            return
        
        self.fetch_count += 1
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Write to rotating log
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # CLEAN LOGGING: Only the essential data
        with open('{alert_name}.json', 'a') as f:
            f.write(f'=== FETCH START: {{fetch_id}} | {{nyc_timestamp}} ===\\n')
            
            for match in filtered_matches:
                json.dump(match, f, indent=2)
                f.write('\\n')
            
            f.write(f'=== FETCH END: {{fetch_id}} | {{nyc_timestamp}} ===\\n')
        
        # Auto-track results
        self.track_alert_for_results(filtered_matches, fetch_id, nyc_timestamp)
        
        if self.state_manager.should_rotate(self.fetch_count):
            self.rotate_log()
    
    def track_alert_for_results(self, filtered_matches, fetch_id, nyc_timestamp):
        """Automatically track alerts for results analysis"""
        try:
            import sys
            sys.path.append('.')
            from {alert_name}_results import {alert_name.title().replace('_', '')}ResultsTracker
            
            tracker = {alert_name.title().replace('_', '')}ResultsTracker()
            
            for match in filtered_matches:
                tracker.add_new_alert(match, fetch_id, nyc_timestamp)
                
        except Exception as e:
            print(f"⚠️ Results tracking failed: {{e}}")
    
    def rotate_log(self):
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        self.state_manager.reset_state()
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
        open('{alert_name}.json', 'w').close()

class {alert_name.title().replace('_', '')}Processor:
    def __init__(self):
        self.logger = {alert_name.title().replace('_', '')}Logger()
        self.load_config()
    
    def load_config(self):
        """Load configuration from config file"""
        try:
            with open('{alert_name}_config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {{
                "telegram_bot_token": "7848696790:AAFhzVNuNsL_hUvsZMabpCUz2RVRhc0PMo8",
                "telegram_chat_id": "6128359776",
                "criteria": {{
                    # TODO: Define your criteria here
                    "status_id": 3,
                    "min_total": 3.0
                }}
            }}
    
    def find_unprocessed_fetch_id(self):
        """Find the next unprocessed fetch ID from tracking file"""
        tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
        
        try:
            with open(tracking_file, 'r') as f:
                content = f.read()
            
            entries = content.split('}}\\n{{')
            unprocessed_entries = []
            
            for i, entry_str in enumerate(entries):
                if i > 0:
                    entry_str = '{{' + entry_str
                if i < len(entries) - 1:
                    entry_str = entry_str + '}}'
                
                try:
                    entry = json.loads(entry_str)
                    if (entry.get("monitor_central.py") == "completed" and 
                        entry.get("{alert_name}.py") == ""):
                        unprocessed_entries.append(entry)
                except json.JSONDecodeError:
                    continue
            
            if unprocessed_entries:
                return unprocessed_entries[-1].get("fetch_id")
            
            return None
        except Exception as e:
            print(f"Error reading tracking file: {{e}}")
            return None
    
    def extract_fetch_data_by_id(self, fetch_id, input_file_path):
        """Extract complete fetch data between header and footer markers"""
        try:
            with open(input_file_path, 'r') as f:
                content = f.read()
            
            start_marker = f'=== FETCH START: {{fetch_id}} |'
            start_pos = content.find(start_marker)
            
            if start_pos == -1:
                return None
            
            end_marker = f'=== FETCH END: {{fetch_id}} |'
            end_pos = content.find(end_marker, start_pos)
            
            if end_pos == -1:
                return None
            
            fetch_section = content[start_pos:end_pos]
            json_start = fetch_section.find('\\n{{')
            json_end = fetch_section.rfind('\\n}}') + 2
            
            if json_start == -1 or json_end == -1:
                return None
            
            json_content = fetch_section[json_start:json_end]
            return json.loads(json_content)
            
        except Exception as e:
            print(f"Error extracting fetch data for {{fetch_id}}: {{e}}")
            return None
    
    def mark_fetch_completed(self, fetch_id):
        """Mark fetch as completed in tracking file"""
        tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
        
        try:
            with open(tracking_file, 'r') as f:
                content = f.read()
            
            entries = content.split('}}\\n{{')
            updated_entries = []
            
            for i, entry_str in enumerate(entries):
                if i > 0:
                    entry_str = '{{' + entry_str
                if i < len(entries) - 1:
                    entry_str = entry_str + '}}'
                
                try:
                    entry = json.loads(entry_str)
                    if entry.get("fetch_id") == fetch_id:
                        entry["{alert_name}.py"] = "completed"
                    updated_entries.append(json.dumps(entry, indent=2))
                except json.JSONDecodeError:
                    continue
            
            with open(tracking_file, 'w') as f:
                f.write('\\n'.join(updated_entries) + '\\n')
                
        except Exception as e:
            print(f"Error marking fetch {{fetch_id}} as completed: {{e}}")
    
    def send_telegram_alert(self, filtered_matches):
        """Send telegram alert for matches"""
        if not filtered_matches:
            return
        
        try:
            alerts = self.format_telegram_message(filtered_matches)
            
            url = f"https://api.telegram.org/bot{{self.config['telegram_bot_token']}}/sendMessage"
            
            for alert in alerts:
                payload = {{
                    'chat_id': self.config['telegram_chat_id'],
                    'text': alert,
                    'parse_mode': 'Markdown'
                }}
                
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Telegram alert sent for {alert_name}")
                else:
                    print(f"❌ Telegram alert failed: {{response.status_code}}")
                
        except Exception as e:
            print(f"❌ Telegram alert error: {{e}}")
    
    def format_telegram_message(self, matches):
        """Format matches for telegram alerts"""
        alerts = []
        for match in matches:
            match_info = match.get("match_info", {{}})
            
            alert = (f"🔔 *{alert_name.upper()} ALERT*\\n\\n"
                    f"⚽ {{match_info.get('home_team', 'Unknown')}} vs {{match_info.get('away_team', 'Unknown')}}\\n"
                    f"🏆 {{match_info.get('competition_name', 'Unknown')}}\\n"
                    f"📊 {{match_info.get('live_score', 'N/A')}}\\n"
                    f"⏰ {{datetime.now().strftime('%I:%M:%S %p')}}")
            alerts.append(alert)
        
        return alerts
    
    def filter_matches(self, matches):
        """
        TODO: IMPLEMENT YOUR FILTERING LOGIC HERE
        
        This is where you define what makes a match qualify for alerts.
        Return a list of matches that meet your criteria.
        
        Example criteria:
        - Status ID: 3 (Half-time)
        - Live Score: 0-0
        - O/U Total >= 3.0
        """
        filtered = []
        
        for match in matches:
            # TODO: Add your criteria here
            # Example:
            # status = match.get("match_info", {{}}).get("status", "")
            # if "Status ID: 3" in status:
            #     filtered.append(match)
            
            pass  # Remove this when you implement your logic
        
        # Apply duplicate prevention
        filtered = self.remove_duplicates(filtered)
        return filtered
    
    def get_existing_match_ids(self):
        """Read existing match IDs from log to prevent duplicates"""
        try:
            with open('{alert_name}.json', 'r') as f:
                content = f.read()
            
            existing_ids = set()
            fetch_sections = content.split('=== FETCH START:')
            
            for section in fetch_sections[1:]:
                try:
                    json_start = section.find('\\n{{')
                    json_end = section.find('\\n=== FETCH END:')
                    
                    if json_start != -1 and json_end != -1:
                        json_content = section[json_start:json_end].strip()
                        json_objects = json_content.split('}}\\n{{')
                        
                        for i, json_obj in enumerate(json_objects):
                            if i > 0:
                                json_obj = '{{' + json_obj
                            if i < len(json_objects) - 1:
                                json_obj = json_obj + '}}'
                            
                            try:
                                entry_data = json.loads(json_obj)
                                if isinstance(entry_data, dict) and "match_info" in entry_data:
                                    match_id = entry_data["match_info"].get("match_id")
                                    if match_id:
                                        existing_ids.add(match_id)
                            except json.JSONDecodeError:
                                continue
                                
                except json.JSONDecodeError:
                    continue
            
            return existing_ids
        except (FileNotFoundError, IOError):
            return set()
    
    def get_alerted_match_ids_persistent(self):
        """Read persistent alerted match IDs file"""
        alerted_file = '{alert_name}_alerted_match_ids.txt'
        try:
            with open(alerted_file, 'r') as f:
                ids = set(line.strip() for line in f if line.strip())
            return ids
        except FileNotFoundError:
            return set()
    
    def save_alerted_match_id_persistent(self, match_id, home_team, away_team):
        """Save match ID to persistent tracking file"""
        alerted_file = '{alert_name}_alerted_match_ids.txt'
        try:
            with open(alerted_file, 'a') as f:
                f.write(f"{{match_id}}\\n")
            print(f"💾 PERSISTENT SAVE: {{match_id}} - {{home_team}} vs {{away_team}}")
        except Exception as e:
            print(f"⚠️ PERSISTENT SAVE ERROR: {{e}}")

    def remove_duplicates(self, filtered_matches):
        """Multi-layer duplicate prevention"""
        log_existing_ids = self.get_existing_match_ids()
        persistent_existing_ids = self.get_alerted_match_ids_persistent()
        all_existing_ids = log_existing_ids.union(persistent_existing_ids)
        
        new_matches = []
        
        for match in filtered_matches:
            match_info = match.get("match_info", {{}})
            match_id = match_info.get("match_id")
            home_team = match_info.get("home_team", "Unknown")
            away_team = match_info.get("away_team", "Unknown")
            
            if match_id not in all_existing_ids:
                new_matches.append(match)
                self.save_alerted_match_id_persistent(match_id, home_team, away_team)
            
        return new_matches
    
    def process_monitor_data(self, monitor_data_path):
        """Main processing function"""
        fetch_id = self.find_unprocessed_fetch_id()
        if not fetch_id:
            return {{"error": "No unprocessed fetch IDs found"}}
        
        latest_monitor = self.extract_fetch_data_by_id(fetch_id, monitor_data_path)
        if not latest_monitor:
            return {{"error": f"Could not extract data for fetch ID: {{fetch_id}}"}}
        
        try:
            filtered_matches = self.filter_matches(latest_monitor.get("monitor_central_display", []))
            
            filtered_data = latest_monitor.copy()
            filtered_data["monitor_central_display"] = filtered_matches
            filtered_data["filtered_match_count"] = len(filtered_matches)
            
            if len(filtered_matches) > 0:
                for match in filtered_matches:
                    self.send_telegram_alert([match])
            
            nyc_tz = pytz.timezone('America/New_York')
            nyc_time = datetime.now(nyc_tz)
            nyc_timestamp = nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
            
            self.logger.log_fetch_qualifying_only(filtered_matches, fetch_id, nyc_timestamp)
            self.mark_fetch_completed(fetch_id)
            
            return filtered_data
        except Exception as e:
            print(f"Error processing {alert_name} data: {{e}}")
            return {{"error": f"Processing failed: {{e}}"}}

# Initialize the processor
{alert_name}_processor = {alert_name.title().replace('_', '')}Processor()

# Main execution
if __name__ == "__main__":
    import signal
    
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        try:
            result = {alert_name}_processor.process_monitor_data("../6_monitor_central/monitor_central.json")
            print(f"Single {alert_name} completed! Logged to: {alert_name}.json")
        except Exception as e:
            print(f"Single {alert_name} failed: {{e}}")
        sys.exit(0)
    
    # Continuous mode
    running = True
    
    def signal_handler(sig, frame):
        global running
        print(f"\\nReceived shutdown signal. Stopping continuous {alert_name}...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_{alert_name}():
        global running
        fetch_count = 0
        
        print(f"Starting {alert_name.title()} Continuous Pass-Through...")
        print("Processing every 60 seconds from monitor_central.json")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            fetch_count += 1
            start_time = time.time()
            
            try:
                print(f"\\n[Fetch #{{fetch_count}}] Starting pass-through...")
                
                result = {alert_name}_processor.process_monitor_data("../6_monitor_central/monitor_central.json")
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"[Fetch #{{fetch_count}}] Completed in {{duration:.2f}} seconds")
                print(f"[Fetch #{{fetch_count}}] Logged to: {alert_name}.json")
                
                target_interval = 60
                wait_time = max(0, target_interval - duration)
                
                if wait_time > 0:
                    print(f"[Fetch #{{fetch_count}}] Waiting {{wait_time:.2f}} seconds...")
                    
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        time.sleep(0.5)
                else:
                    print(f"[Fetch #{{fetch_count}}] Starting next pass-through immediately")
                
            except Exception as e:
                print(f"[Fetch #{{fetch_count}}] Error occurred: {{e}}")
                print(f"[Fetch #{{fetch_count}}] Waiting 60 seconds before retry...")
                
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    time.sleep(0.5)
        
        print(f"\\nContinuous {alert_name} stopped. Goodbye!")
    
    try:
        continuous_{alert_name}()
    except KeyboardInterrupt:
        print("\\nShutdown complete.")
'''
    
    with open(f"{alert_dir}/{alert_name}.py", 'w') as f:
        f.write(template)

def create_results_tracker(alert_dir, alert_name):
    """Create the results tracker file"""
    
    template = f'''#!/usr/bin/env python3
"""
{alert_name.upper()} RESULTS TRACKER
Tracks outcomes of {alert_name} alerts to measure betting success rate
"""

import json
import os
import time
from datetime import datetime, timedelta
import pytz

class {alert_name.title().replace('_', '')}ResultsTracker:
    def __init__(self):
        self.results_file = "{alert_name}_results_tracking.json"
        self.alert_log_file = "{alert_name}.json"
        self.monitor_data_file = "../6_monitor_central/monitor_central.json"
        
    def add_new_alert(self, match_data, fetch_id, timestamp):
        """Add a new alert to results tracking"""
        tracking_entry = {{
            "match_id": match_data["match_info"]["match_id"],
            "home_team": match_data["match_info"]["home_team"],
            "away_team": match_data["match_info"]["away_team"],
            "competition": match_data["match_info"]["competition_name"],
            "alert_timestamp": timestamp,
            "fetch_id": fetch_id,
            "status": "PENDING",
            "final_score": None,
            "outcome": None,
            "last_checked": None,
            "match_ended": False,
            "alert_criteria": "{alert_name} criteria met"
        }}
        
        # Load existing results
        results_data = self.load_existing_results()
        
        # Check if already exists
        existing_ids = [match["match_id"] for match in results_data["tracked_matches"]]
        if tracking_entry["match_id"] not in existing_ids:
            results_data["tracked_matches"].append(tracking_entry)
            self.save_results(results_data)
            print(f"📝 RESULT TRACKING: {{match_data['match_info']['home_team']}} vs {{match_data['match_info']['away_team']}}")
    
    def load_existing_results(self):
        """Load existing results tracking data"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {{
                "alert_system": "{alert_name}",
                "tracked_matches": [],
                "summary": {{
                    "total_alerts": 0,
                    "wins": 0,
                    "losses": 0,
                    "pending": 0,
                    "win_rate": 0.0
                }}
            }}
    
    def save_results(self, results_data):
        """Save results tracking data"""
        with open(self.results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
    
    def find_match_outcome(self, match_id):
        """Find the final outcome of a match from monitor_central.json"""
        try:
            with open(self.monitor_data_file, 'r') as f:
                content = f.read()
                
            fetch_sections = content.split('=== FETCH START:')
            
            for section in fetch_sections[1:]:
                try:
                    json_start = section.find('\\n{{')
                    json_end = section.find('\\n=== FETCH END:')
                    
                    if json_start != -1 and json_end != -1:
                        json_content = section[json_start:json_end].strip()
                        monitor_data = json.loads(json_content)
                        
                        for match in monitor_data.get("monitor_central_display", []):
                            if match.get("match_info", {{}}).get("match_id") == match_id:
                                status = match.get("match_info", {{}}).get("status", "")
                                live_score = match.get("match_info", {{}}).get("live_score", "")
                                
                                if "Status ID: 8" in status:  # Match ended
                                    return {{
                                        "match_ended": True,
                                        "final_score": live_score,
                                        "status": status
                                    }}
                                else:
                                    return {{
                                        "match_ended": False,
                                        "current_score": live_score,
                                        "status": status
                                    }}
                                    
                except json.JSONDecodeError:
                    continue
                    
            return None
            
        except FileNotFoundError:
            return None
    
    def analyze_outcome(self, match_data, final_score):
        """
        TODO: IMPLEMENT YOUR OUTCOME ANALYSIS LOGIC
        
        Determine if the alert would have been a winning bet.
        This depends on your specific criteria.
        
        For example, if your alert is for "goals will be scored":
        - WIN: Any goals scored in the match
        - LOSS: Match ended 0-0
        
        Return: "WIN" or "LOSS"
        """
        # TODO: Replace this with your actual logic
        if final_score and "0-0" not in final_score:
            return "WIN"  # Any goals scored
        else:
            return "LOSS"  # No goals scored
    
    def update_tracking_results(self):
        """Update results for all tracked matches"""
        results_data = self.load_existing_results()
        
        for match in results_data["tracked_matches"]:
            if match["status"] in ["PENDING", "MONITORING"]:
                outcome = self.find_match_outcome(match["match_id"])
                
                if outcome:
                    nyc_tz = pytz.timezone('America/New_York')
                    check_time = datetime.now(nyc_tz).strftime("%m/%d/%Y %I:%M:%S %p %Z")
                    match["last_checked"] = check_time
                    
                    if outcome["match_ended"]:
                        match["match_ended"] = True
                        match["final_score"] = outcome["final_score"]
                        
                        # Analyze the outcome based on your criteria
                        result = self.analyze_outcome(match, outcome["final_score"])
                        match["outcome"] = result
                        match["status"] = "WON" if result == "WIN" else "LOST"
                        
                        print(f"🏁 MATCH ENDED: {{match['home_team']}} vs {{match['away_team']}}")
                        print(f"   Final Score: {{outcome['final_score']}}")
                        print(f"   Result: {{result}}")
                    else:
                        match["status"] = "MONITORING"
        
        # Update summary statistics
        total_alerts = len(results_data["tracked_matches"])
        wins = len([m for m in results_data["tracked_matches"] if m["status"] == "WON"])
        losses = len([m for m in results_data["tracked_matches"] if m["status"] == "LOST"])
        pending = len([m for m in results_data["tracked_matches"] if m["status"] in ["PENDING", "MONITORING"]])
        
        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        
        results_data["summary"] = {{
            "total_alerts": total_alerts,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": round(win_rate, 2),
            "last_updated": datetime.now(pytz.timezone('America/New_York')).strftime("%m/%d/%Y %I:%M:%S %p %Z")
        }}
        
        self.save_results(results_data)
        return results_data
    
    def print_summary(self, results_data):
        """Print a summary of alert performance"""
        summary = results_data["summary"]
        
        print("\\n" + "=" * 60)
        print(f"📊 {{alert_name.upper()}} ALERT PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"📈 Total Alerts: {{summary['total_alerts']}}")
        print(f"✅ Wins: {{summary['wins']}}")
        print(f"❌ Losses: {{summary['losses']}}")
        print(f"⏳ Pending: {{summary['pending']}}")
        print(f"🎯 Win Rate: {{summary['win_rate']}}%")
        print(f"🕐 Last Updated: {{summary['last_updated']}}")
        
        if summary['total_alerts'] > 0:
            print("\\n📋 RECENT MATCHES:")
            for match in results_data["tracked_matches"][-5:]:
                status_emoji = {{"WON": "✅", "LOST": "❌", "PENDING": "⏳", "MONITORING": "🔄"}}
                emoji = status_emoji.get(match["status"], "❓")
                print(f"  {{emoji}} {{match['home_team']}} vs {{match['away_team']}} - {{match['status']}}")

def main():
    tracker = {alert_name.title().replace('_', '')}ResultsTracker()
    
    print(f"🚀 {{alert_name.upper()}} RESULTS TRACKER")
    print("=" * 40)
    
    results = tracker.update_tracking_results()
    tracker.print_summary(results)
    
    print(f"\\n📁 Results saved to: {{tracker.results_file}}")

if __name__ == "__main__":
    main()
'''
    
    with open(f"{alert_dir}/{alert_name}_results.py", 'w') as f:
        f.write(template)

def create_config_file(alert_dir, alert_name, criteria_description):
    """Create configuration file"""
    config = {
        "alert_name": alert_name,
        "description": criteria_description,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "telegram_bot_token": "7848696790:AAFhzVNuNsL_hUvsZMabpCUz2RVRhc0PMo8",
        "telegram_chat_id": "6128359776",
        "criteria": {
            "status_id": 3,
            "min_total": 3.0,
            "score_requirement": "0-0"
        },
        "settings": {
            "max_fetches": 50,
            "log_rotation": True,
            "duplicate_prevention": True
        }
    }
    
    with open(f"{alert_dir}/{alert_name}_config.json", 'w') as f:
        json.dump(config, f, indent=2)

def create_readme(alert_dir, alert_name, criteria_description):
    """Create README file"""
    readme_content = f"""# {alert_name.upper()} Alert System

## Description
{criteria_description}

## Self-Contained Design
This alert system is completely self-contained and independent. It includes:

- ✅ **Main Alert Processor** (`{alert_name}.py`)
- ✅ **Results Tracker** (`{alert_name}_results.py`) 
- ✅ **Configuration** (`{alert_name}_config.json`)
- ✅ **Clean Logging** (only logs qualifying matches)
- ✅ **Duplicate Prevention** (multi-layer system)
- ✅ **Telegram Integration** (real-time alerts)
- ✅ **Performance Tracking** (win/loss analysis)

## Quick Start

### 1. Configure Your Criteria
Edit `{alert_name}.py` and implement your filtering logic in the `filter_matches()` method.

### 2. Configure Results Analysis
Edit `{alert_name}_results.py` and implement your outcome analysis in the `analyze_outcome()` method.

### 3. Run Single Test
```bash
python3 {alert_name}.py --single-run
```

### 4. Run Continuous Mode
```bash
python3 run_{alert_name}.py
```

### 5. Check Results
```bash
python3 {alert_name}_results.py
```

## Files Structure
```
{alert_name}/
├── {alert_name}.py              # Main alert processor
├── {alert_name}_results.py      # Results tracker
├── {alert_name}_config.json     # Configuration
├── run_{alert_name}.py          # Runner script
├── {alert_name}.json           # Clean log output
├── {alert_name}_results_tracking.json  # Results data
├── {alert_name}_alerted_match_ids.txt  # Duplicate prevention
└── README.md                    # This file
```

## Customization Required

### 1. Filter Logic (`{alert_name}.py`)
```python
def filter_matches(self, matches):
    # TODO: Implement your criteria here
    # Example: Status ID 3, Score 0-0, O/U >= 3.0
    pass
```

### 2. Results Analysis (`{alert_name}_results.py`)
```python
def analyze_outcome(self, match_data, final_score):
    # TODO: Define what constitutes a "win"
    # Example: Any goals scored = WIN, 0-0 = LOSS
    pass
```

## Features

### Clean Logging
- Only logs when matches meet criteria
- Raw match data format (no metadata bloat)
- Bookended format for easy parsing

### Duplicate Prevention
- Multi-layer system (log file + persistent file)
- Prevents repeated alerts for same match
- Handles clean logging format correctly

### Results Tracking
- Automatic outcome tracking
- Win/loss analysis
- Performance metrics (win rate, etc.)
- Historical data preservation

### Telegram Integration
- Real-time alerts when criteria are met
- Individual alerts per match
- Customizable message format

## Independence
This system is completely independent:
- ✅ No dependencies on other alert systems
- ✅ Self-contained logging and tracking
- ✅ Independent configuration
- ✅ Can be deleted without affecting others
- ✅ Ready for production use

## Next Steps
1. Implement your filtering criteria
2. Define your outcome analysis logic
3. Test with single-run mode
4. Deploy in continuous mode
5. Monitor results and optimize

---
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    with open(f"{alert_dir}/README.md", 'w') as f:
        f.write(readme_content)

def create_run_script(alert_dir, alert_name):
    """Create runner script"""
    script_content = f'''#!/usr/bin/env python3
"""
Runner script for {alert_name.upper()} Alert System
"""

import os
import sys

def main():
    # Change to alert directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"🚀 Starting {alert_name.upper()} Alert System")
    print(f"📁 Working Directory: {{script_dir}}")
    print("=" * 50)
    
    # Import and run
    try:
        from {alert_name} import continuous_{alert_name}
        continuous_{alert_name}()
    except KeyboardInterrupt:
        print(f"\\n🛑 {alert_name.upper()} Alert System stopped by user")
    except Exception as e:
        print(f"❌ Error running {alert_name}: {{e}}")

if __name__ == "__main__":
    main()
'''
    
    with open(f"{alert_dir}/run_{alert_name}.py", 'w') as f:
        f.write(script_content)

# Example usage
if __name__ == "__main__":
    # Example: Create a new alert system for corner kicks
    create_alert_system(
        alert_name="alert_corners_5plus",
        criteria_description="Alert when a match has 5+ total corners at half-time with score 0-0"
    )
    
    print("\\n" + "=" * 60)
    print("🎯 SELF-CONTAINED ALERT SYSTEM CREATED!")
    print("=" * 60)
    print("✅ Complete independence from other systems")
    print("✅ Built-in results tracking")
    print("✅ Clean logging and duplicate prevention")
    print("✅ Ready for immediate deployment")
    print("✅ Can be deleted without affecting others")
    print("\\n🔧 Next steps:")
    print("1. Implement filtering criteria in the main processor")
    print("2. Define outcome analysis logic in results tracker")
    print("3. Test and deploy!")