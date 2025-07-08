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

class MonitorCentralLogger:
    def __init__(self, log_dir="monitor_central_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.state_manager = PersistentStateManager("monitor_central", max_fetches)
        self.fetch_count, self.accumulated_data = self.state_manager.load_state()
        self.setup_logging()
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"monitor_central_log_{timestamp}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
        
        self.logger = logging.getLogger('monitor_central_logger')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        handler = logging.FileHandler(self.log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_fetch(self, monitor_data):
        """Pure catch-all pass-through logging with persistent state"""
        self.fetch_count += 1
        
        # Pure pass-through - use the data exactly as received from pretty_print_conversion.json
        log_entry = monitor_data
        
        # Save state after each fetch
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Append to main monitor_central.json file
        with open('monitor_central.json', 'a') as f:
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
        # Clear the main monitor_central.json file
        open('monitor_central.json', 'w').close()

class MonitorCentralProcessor:
    def __init__(self):
        self.logger = MonitorCentralLogger()
        # Status mappings for display
        self.status_mappings = {
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
    
    def convert_temperature_to_fahrenheit(self, celsius_str):
        """Convert temperature to standard Fahrenheit format: 73°F"""
        try:
            if not celsius_str or celsius_str == "":
                return ""
            
            # Handle different input formats
            temp_input = str(celsius_str).replace("\u00b0", "")  # Remove Unicode degree
            
            # Remove all possible temperature symbols and units
            temp_str = (temp_input.replace("°C", "").replace("°F", "")
                       .replace("C", "").replace("F", "").strip())
            
            # Extract just the number
            temp_number = float(temp_str)
            
            # If input was Celsius, convert to Fahrenheit
            if "C" in str(celsius_str):
                fahrenheit = (temp_number * 9/5) + 32
                temp_number = fahrenheit
            
            # Return standard format: 73°F (using proper encoding)
            return f"{int(temp_number)}\u00b0F"
            
        except:
            return ""
    
    def mph_to_wind_classification(self, mph):
        """Convert mph to Beaufort Wind Scale classification"""
        try:
            mph_value = float(mph)
            if mph_value <= 1:
                return "Calm"
            elif mph_value <= 3:
                return "Light Air"
            elif mph_value <= 7:
                return "Light Breeze"
            elif mph_value <= 12:
                return "Gentle Breeze"
            elif mph_value <= 18:
                return "Moderate Breeze"
            elif mph_value <= 24:
                return "Fresh Breeze"
            elif mph_value <= 31:
                return "Strong Breeze"
            elif mph_value <= 38:
                return "Near Gale"
            elif mph_value <= 46:
                return "Gale"
            elif mph_value <= 54:
                return "Strong Gale"
            elif mph_value <= 63:
                return "Storm"
            else:
                return "Hurricane Force"
        except:
            return "Unknown"
    
    def ms_to_mph(self, wind_str):
        """Convert m/s to mph with Beaufort Scale Classification"""
        try:
            if not wind_str or wind_str == "":
                return ""
            
            # Handle different wind formats
            if "mph" in wind_str:
                # Already in mph, extract number and add classification
                import re
                mph_match = re.search(r'(\d+(?:\.\d+)?)', wind_str)
                if mph_match:
                    mph_value = float(mph_match.group(1))
                    classification = self.mph_to_wind_classification(mph_value)
                    return f"{mph_value:.0f}mph ({classification})"
            
            elif "m/s" in wind_str:
                # Convert from m/s to mph
                ms_value = float(wind_str.replace("m/s", "").strip())
                mph = ms_value * 2.237
                classification = self.mph_to_wind_classification(mph)
                return f"{mph:.0f}mph ({classification})"
                
            elif "km/h" in wind_str:
                # Convert from km/h to mph
                parts = wind_str.split()
                if len(parts) >= 1:
                    kmh = float(parts[0])
                    mph = kmh * 0.621371
                    classification = self.mph_to_wind_classification(mph)
                    return f"{mph:.0f}mph ({classification})"
            
            return wind_str
        except:
            return wind_str
    
    def weather_code_to_text(self, weather_code):
        """Convert numeric weather codes to natural language"""
        weather_mapping = {
            1: "Clear",
            2: "Partly Cloudy", 
            3: "Cloudy",
            4: "Light Rain",
            5: "Fair",
            6: "Moderate Rain",
            7: "Overcast",
            8: "Heavy Rain",
            9: "Thunderstorms",
            10: "Snow"
        }
        
        try:
            if isinstance(weather_code, str) and weather_code.isdigit():
                code = int(weather_code)
            elif isinstance(weather_code, int):
                code = weather_code
            else:
                return weather_code  # Return as-is if already text
                
            return weather_mapping.get(code, f"Unknown ({code})")
        except:
            return weather_code
    
    def convert_pressure_to_inhg(self, pressure_str):
        """Convert pressure to inHg format"""
        try:
            if not pressure_str or pressure_str == "":
                return ""
            
            # Handle different pressure formats
            if "mmHg" in pressure_str:
                # Convert mmHg to inHg
                # "760mmHg" → "29.9 inHg"
                mmhg = float(pressure_str.replace("mmHg", "").strip())
                inhg = mmhg * 0.03937
                return f"{inhg:.1f} inHg"
                
            elif "hPa" in pressure_str:
                # Convert hPa to inHg
                # "1013 hPa" → "29.9 inHg"
                hpa = float(pressure_str.replace("hPa", "").strip())
                inhg = hpa * 0.02953
                return f"{inhg:.1f} inHg"
                
            elif "inHg" in pressure_str:
                # Already in inHg, just clean format
                inhg = float(pressure_str.replace("inHg", "").strip())
                return f"{inhg:.1f} inHg"
            
            return pressure_str
        except:
            return pressure_str
    
    def format_status_display(self, status_id):
        """Format status for display"""
        if status_id is None:
            return ""
        status_name = self.status_mappings.get(status_id, "Unknown Status")
        return f"Status ID: {status_id} ({status_name})"
    
    def extract_monitor_display_data(self, conversion_data):
        """Extract and format data according to monitor central roadmap"""
        try:
            # Get timestamp from header
            timestamp = conversion_data.get("CONVERTED_DATA", {}).get("SOURCE_PRETTY_PRINT_HEADER", {}).get("nyc_timestamp", "")
            
            # Get matches array
            matches = conversion_data.get("CONVERTED_DATA", {}).get("MATCHES_WITH_CONVERTED_ODDS", [])
            
            monitor_matches = []
            
            for match in matches:
                # Extract basic match info
                match_details = match.get("match_details", {}).get("parsed_details", {})
                live_data = match.get("live_data", {})
                raw_match_details = match.get("raw_match_details", {})
                
                # Extract corner data
                home_corners = live_data.get("parsed_score", {}).get("home_detailed", {}).get("corners", 0)
                away_corners = live_data.get("parsed_score", {}).get("away_detailed", {}).get("corners", 0)
                
                # Convert environmental data with natural language identifiers
                environment = raw_match_details.get("environment", {})
                
                # Convert temperature and create clean field without Unicode issues
                temp_input = environment.get("temperature", "")
                if temp_input and temp_input != "":
                    try:
                        # Handle both Fahrenheit and Celsius inputs
                        temp_str = str(temp_input)
                        
                        if "F" in temp_str:
                            # Already in Fahrenheit, just clean it up
                            temp_number = float(temp_str.replace("F", "").replace("°", "").replace("\\u00b0", "").strip())
                            temperature_f = f"{int(temp_number)} F"
                        elif "C" in temp_str:
                            # Convert from Celsius to Fahrenheit
                            temp_number = float(temp_str.replace("°C", "").replace("C", "").replace("\\u00b0", "").strip())
                            fahrenheit = (temp_number * 9/5) + 32
                            temperature_f = f"{int(fahrenheit)} F"
                        else:
                            # Assume it's a plain number in Celsius
                            temp_number = float(temp_str.strip())
                            fahrenheit = (temp_number * 9/5) + 32
                            temperature_f = f"{int(fahrenheit)} F"
                    except (ValueError, TypeError):
                        temperature_f = ""
                else:
                    temperature_f = ""
                
                converted_environment = {
                    "weather": self.weather_code_to_text(environment.get("weather", "")),
                    "pressure": self.convert_pressure_to_inhg(environment.get("pressure", "")),
                    "temperature_f": temperature_f,
                    "wind": self.ms_to_mph(environment.get("wind", "")),
                    "humidity": environment.get("humidity", "")
                }
                
                # Create monitor display structure
                monitor_match = {
                    "timestamp": timestamp,
                    "match_info": {
                        "match_id": match_details.get("id", ""),
                        "competition_id": match_details.get("competition_id", ""),
                        "competition_name": match_details.get("competition_name", ""),
                        "home_team": match_details.get("home_team_name", ""),
                        "away_team": match_details.get("away_team_name", ""),
                        "status": self.format_status_display(match_details.get("status_id")),
                        "live_score": match.get("formatted_live_score", "")
                    },
                    "corners": {
                        "home": home_corners,
                        "away": away_corners,
                        "total": home_corners + away_corners
                    },
                    "odds": match.get("converted_odds", {}),
                    "environment": converted_environment,
                    "incidents": live_data.get("incidents", [])
                }
                
                monitor_matches.append(monitor_match)
            
            return monitor_matches
            
        except Exception as e:
            print(f"Error extracting monitor display data: {e}")
            return []
    
    def process_conversion_data(self, conversion_data_path):
        """Process conversion data and create monitor central display format"""
        
        # Read latest conversion from pretty_print_conversion.json (last line)
        with open(conversion_data_path, 'r') as f:
            lines = f.readlines()
        
        # Get the latest conversion data (last line)
        if not lines:
            return {"error": "No valid data in pretty_print_conversion.json"}
        
        try:
            latest_conversion = json.loads(lines[-1].strip())
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in latest conversion"}
        
        # Extract and format data according to monitor central roadmap
        monitor_matches = self.extract_monitor_display_data(latest_conversion)
        
        # Extract footer data from the conversion data
        footer_data = latest_conversion.get("CONVERSION_FOOTER", {})
        
        # Create final monitor data structure
        monitor_data = {
            "monitor_central_display": monitor_matches,
            "total_matches": len(monitor_matches),
            "generated_at": latest_conversion.get("CONVERTED_DATA", {}).get("SOURCE_PRETTY_PRINT_HEADER", {}).get("nyc_timestamp", ""),
            "MONITOR_FOOTER": {
                "random_fetch_id": footer_data.get("random_fetch_id", ""),
                "nyc_timestamp": footer_data.get("nyc_timestamp", ""),
                "pipeline_completion_time_seconds": footer_data.get("pipeline_completion_time_seconds", ""),
                "conversion_completion_time_seconds": footer_data.get("conversion_completion_time_seconds", ""),
                "fetch_end": "=== MONITOR CENTRAL DATA END ===",
                "total_matches": footer_data.get("total_matches", 0),
                "matches_in_play": footer_data.get("matches_in_play", 0),
                "match_status_breakdown": footer_data.get("match_status_breakdown", []),
                "total_matches_with_odds": footer_data.get("total_matches_with_odds", 0)
            }
        }
        
        # Log the monitor data
        self.logger.log_fetch(monitor_data)
        
        return monitor_data

# Initialize the processor
monitor_central_processor = MonitorCentralProcessor()

# Main execution
if __name__ == "__main__":
    import sys
    
    # Check for single-run mode (called by pretty_print_conversion.py)
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        # Single execution mode - just do one pass-through and exit
        try:
            result = monitor_central_processor.process_conversion_data("../5_pretty_print_conversion/pretty_print_conversion.json")
            print(f"Single monitor-central completed! Logged to: monitor_central.json")
            
            # Call the next stage in pipeline: alert_3ou_half.py
            import subprocess
            try:
                alert_script_path = os.path.join(os.path.dirname(__file__), '..', '7_alert_3ou_half', 'alert_3ou_half.py')
                subprocess.run([sys.executable, alert_script_path, "--single-run"], 
                              cwd=os.path.join(os.path.dirname(__file__), '..', '7_alert_3ou_half'),
                              check=False)
                print("Pipeline completed: alert_3ou_half.py executed successfully")
            except Exception as e:
                print(f"Error calling alert_3ou_half.py: {e}")
                
        except Exception as e:
            print(f"Single monitor-central failed: {e}")
        sys.exit(0)
    
    # Continuous mode (if run standalone)
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous monitor-central...")
        running = False
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_monitor_central():
        global running
        monitor_count = 0
        
        print("Starting Monitor Central Continuous Pass-Through...")
        print("Processing every 60 seconds from pretty_print_conversion.json")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            monitor_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Monitor #{monitor_count}] Starting pass-through...")
                
                # Perform the pass-through
                result = monitor_central_processor.process_conversion_data("../5_pretty_print_conversion/pretty_print_conversion.json")
                
                # Calculate duration
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"[Monitor #{monitor_count}] Completed in {duration:.2f} seconds")
                print(f"[Monitor #{monitor_count}] Logged to: monitor_central.json")
                
                # Calculate wait time (60 seconds total cycle time)
                target_interval = 60
                wait_time = max(0, target_interval - duration)
                
                if wait_time > 0:
                    print(f"[Monitor #{monitor_count}] Waiting {wait_time:.2f} seconds...")
                    
                    # Wait in small increments to allow for graceful shutdown
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        time.sleep(0.5)
                else:
                    print(f"[Monitor #{monitor_count}] Starting next pass-through immediately")
                
            except Exception as e:
                print(f"[Monitor #{monitor_count}] Error occurred: {e}")
                print(f"[Monitor #{monitor_count}] Waiting 60 seconds before retry...")
                
                # Wait before retry
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    time.sleep(0.5)
        
        print("\nContinuous monitor-central stopped. Goodbye!")
    
    # Run the continuous monitor-central
    try:
        continuous_monitor_central()
    except KeyboardInterrupt:
        print("\nShutdown complete.")