# LOGGING ANALYSIS REFERENCE: See logging_indepth_analysis.md for comprehensive independent analysis methodology
import json
import logging
import os
import time
from datetime import datetime, timedelta
import pytz
import sys
sys.path.append('../shared_utils')
from persistent_state import PersistentStateManager

class AlertUnderdogHalfLogger:
    def __init__(self, log_dir="alert_underdog_0half_log", max_fetches=1440):  # 1440 = 24 hours * 60 minutes
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.state_manager = PersistentStateManager("alert_underdog_0half", max_fetches)
        self.fetch_count, self.accumulated_data = self.state_manager.load_state()
        self.current_date = None
        self.setup_logging()
    
    def get_nyc_time(self):
        """Get current NYC timezone datetime object"""
        nyc_tz = pytz.timezone('America/New_York')
        return datetime.now(nyc_tz)
    
    def get_nyc_timestamp(self):
        """Get current NYC timezone timestamp in MM/DD/YYYY format with AM/PM"""
        nyc_time = self.get_nyc_time()
        return nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
    def get_current_date(self):
        """Get current date in NYC timezone"""
        return self.get_nyc_time().date()
    
    def is_new_day(self):
        """Check if it's a new day (for midnight rotation)"""
        current_date = self.get_current_date()
        if self.current_date is None:
            self.current_date = current_date
            return False
        elif current_date != self.current_date:
            self.current_date = current_date
            return True
        return False
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Set current date
        self.current_date = self.get_current_date()
        
        # Create timestamped log filename
        timestamp = self.get_nyc_time().strftime("%Y%m%d_%H%M%S")
        log_filename = f"alert_underdog_0half_log_{timestamp}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
        
        self.logger = logging.getLogger('alert_underdog_0half_logger')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        handler = logging.FileHandler(self.log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def midnight_rotation(self):
        """Rotate logs at midnight - clear accumulated data and start fresh"""
        print(f"Midnight rotation: Starting new day at {self.get_nyc_timestamp()}")
        
        # Save final data of previous day to rotated log
        if self.accumulated_data:
            with open(self.log_path, 'w') as f:
                json.dump(self.accumulated_data, f, indent=2)
        
        # Reset state for new day
        self.state_manager.reset_state()
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
        
        # Clear main JSON file for new day
        with open('alert_underdog_0half.json', 'w') as f:
            json.dump([], f, indent=2)
    
    def log_fetch(self, monitor_data, fetch_id, nyc_timestamp):
        """Pure catch-all pass-through logging with NYC timestamps"""
        
        # Check for midnight rotation
        if self.is_new_day():
            self.midnight_rotation()
        
        self.fetch_count += 1
        
        # Create log entry with NYC timestamp
        log_entry = {
            "UNDERDOG_HEADER": {
                "fetch_number": self.fetch_count,
                "nyc_timestamp": nyc_timestamp,
                "fetch_start": "=== UNDERDOG CATCH-ALL DATA START ==="
            },
            "MONITOR_CENTRAL_DATA": monitor_data,  # Pure pass-through
            "UNDERDOG_FOOTER": {
                "nyc_timestamp": nyc_timestamp,
                "fetch_end": "=== UNDERDOG CATCH-ALL DATA END ==="
            }
        }
        
        self.accumulated_data.append(log_entry)
        
        # Save state after each fetch
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Write to main alert_underdog_0half.json file (only current day)
        with open('alert_underdog_0half.json', 'a') as f:
            f.write(f'=== FETCH START: {fetch_id} | {nyc_timestamp} ===\n')
            json.dump(log_entry, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: {fetch_id} | {nyc_timestamp} ===\n')
        
        # Auto-rotate if max fetches reached (backup safety)
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

class AlertUnderdogHalfProcessor:
    def __init__(self):
        self.logger = AlertUnderdogHalfLogger()
    
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
                    if entry.get("alert_underdog_0half.py") == "":  # Not processed yet
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
                        entry["alert_underdog_0half.py"] = "completed"
                    updated_entries.append(json.dumps(entry, indent=2))
                except json.JSONDecodeError:
                    continue
            
            # Write back updated entries
            with open(tracking_file, 'w') as f:
                f.write('\n'.join(updated_entries) + '\n')
                
        except Exception as e:
            print(f"Error marking fetch {fetch_id} as completed: {e}")
    
    def process_monitor_data(self, monitor_data_path):
        """Pure catch-all pass-through from monitor_central.json"""
        
        # Find unprocessed fetch ID using new tracking system
        fetch_id = self.find_unprocessed_fetch_id()
        if not fetch_id:
            return {"error": "No unprocessed fetch IDs found"}
        
        # Extract complete fetch data by ID
        latest_monitor = self.extract_fetch_data_by_id(fetch_id, monitor_data_path)
        if not latest_monitor:
            return {"error": f"Could not extract data for fetch ID: {fetch_id}"}
        
        # Pure pass-through - no modifications, just catch-all logging
        passthrough_data = latest_monitor
        
        # Log the complete monitor data (pure catch-all pass-through)
        from datetime import datetime
        import pytz
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        nyc_timestamp = nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
        
        self.logger.log_fetch(passthrough_data, fetch_id, nyc_timestamp)
        
        # Mark fetch as completed in tracking file
        self.mark_fetch_completed(fetch_id)
        
        return passthrough_data

# Initialize the processor
alert_underdog_0half_processor = AlertUnderdogHalfProcessor()

# Main execution
if __name__ == "__main__":
    import sys
    import signal
    
    # Check for single-run mode
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        # Single execution mode - just do one pass-through and exit
        try:
            result = alert_underdog_0half_processor.process_monitor_data("../6_monitor_central/monitor_central.json")
            print(f"Single alert_underdog_0half completed! Logged to: alert_underdog_0half.json")
        except Exception as e:
            print(f"Single alert_underdog_0half failed: {e}")
        sys.exit(0)
    
    # Global flag for graceful shutdown (continuous mode)
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous alert_underdog_0half...")
        running = False
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_alert_underdog_0half():
        global running
        fetch_count = 0
        
        print("Starting Alert Underdog 0-Half Continuous Pass-Through...")
        print("Processing every 60 seconds from monitor_central.json")
        print("Auto-rotates at midnight EST/EDT")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            fetch_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Fetch #{fetch_count}] Starting pass-through...")
                
                # Perform the pass-through
                result = alert_underdog_0half_processor.process_monitor_data("../6_monitor_central/monitor_central.json")
                
                # Calculate duration
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"[Fetch #{fetch_count}] Completed in {duration:.2f} seconds")
                print(f"[Fetch #{fetch_count}] Logged to: alert_underdog_0half.json")
                
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
        
        print("\nContinuous alert_underdog_0half stopped. Goodbye!")
    
    # Run the continuous alert_underdog_0half
    try:
        continuous_alert_underdog_0half()
    except KeyboardInterrupt:
        print("\nShutdown complete.")