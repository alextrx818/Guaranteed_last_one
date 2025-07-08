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
    
    def log_fetch(self, monitor_data):
        """Pure catch-all pass-through logging with NYC timestamps"""
        
        # Check for midnight rotation
        if self.is_new_day():
            self.midnight_rotation()
        
        self.fetch_count += 1
        nyc_timestamp = self.get_nyc_timestamp()
        
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
        with open('alert_underdog_0half.json', 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
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
    
    def process_monitor_data(self, monitor_data_path):
        """Pure catch-all pass-through from monitor_central.json"""
        
        # Read monitor_central.json data
        with open(monitor_data_path, 'r') as f:
            monitor_data = json.load(f)
        
        # Get the latest monitor data (last item in array)
        if not monitor_data or not isinstance(monitor_data, list):
            return {"error": "No valid data in monitor_central.json"}
        
        latest_monitor = monitor_data[-1]
        
        # Pure pass-through - no modifications, just catch-all logging
        passthrough_data = latest_monitor
        
        # Log the complete monitor data (pure catch-all pass-through)
        self.logger.log_fetch(passthrough_data)
        
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