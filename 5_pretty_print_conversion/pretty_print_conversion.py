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

class PrettyPrintConversionLogger:
    def __init__(self, log_dir="pretty_conversion_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.state_manager = PersistentStateManager("pretty_print_conversion", max_fetches)
        self.fetch_count, self.accumulated_data = self.state_manager.load_state()
        self.setup_logging()
    
    def setup_logging(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"pretty_conversion_log_{timestamp}.json"
        self.log_path = os.path.join(self.log_dir, log_filename)
        
        self.logger = logging.getLogger('pretty_conversion_logger')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        handler = logging.FileHandler(self.log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_fetch(self, conversion_data):
        """Pure catch-all pass-through logging with persistent state"""
        self.fetch_count += 1
        
        # Pure pass-through - use the data exactly as received from pretty_print.json
        log_entry = conversion_data
        
        # Save state after each fetch
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Write to rotating log
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Append to main pretty_print_conversion.json file
        with open('pretty_print_conversion.json', 'a') as f:
            json.dump(log_entry, f, indent=2)
            f.write('\n')
        
        # Check for rotation
        if self.state_manager.should_rotate(self.fetch_count):
            self.rotate_log()
    
    def rotate_log(self):
        # Reset state
        self.state_manager.reset_state()
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
        # Clear the main pretty_print_conversion.json file
        open('pretty_print_conversion.json', 'w').close()

class PrettyPrintConversionProcessor:
    def __init__(self):
        self.logger = PrettyPrintConversionLogger()
    
    def convert_european_to_american(self, decimal_odds):
        """Convert European (decimal) odds to American format"""
        try:
            decimal_odds = float(decimal_odds)
            
            if decimal_odds <= 1.0:
                return "+100"  # Even money
            elif decimal_odds >= 2.0:
                # Underdog: +((decimal - 1) × 100)
                american = int((decimal_odds - 1) * 100)
                return f"+{american}"
            else:
                # Favorite: -(100 / (decimal - 1))
                american = int(100 / (decimal_odds - 1))
                return f"-{american}"
        except (ValueError, ZeroDivisionError):
            return str(decimal_odds)  # Return original on error
    
    def convert_hongkong_to_american(self, hk_odds):
        """Convert Hong Kong odds to American format"""
        try:
            hk_odds = float(hk_odds)
            # First add 1 to get decimal odds
            decimal_odds = hk_odds + 1
            
            if decimal_odds >= 2.0:
                # Underdog: +((decimal - 1) × 100)
                american = int((decimal_odds - 1) * 100)
                return f"+{american}"
            else:
                # Favorite: -(100 / (decimal - 1))
                american = int(100 / (decimal_odds - 1))
                return f"-{american}"
        except (ValueError, ZeroDivisionError):
            return str(hk_odds)  # Return original on error

    def celsius_to_fahrenheit(self, celsius_str):
        """Convert Celsius to Fahrenheit: '19°C' → '66°F'"""
        try:
            # Extract numeric value from "XX°C" format
            if isinstance(celsius_str, str) and '°C' in celsius_str:
                celsius_value = float(celsius_str.replace('°C', ''))
                # Formula: (C × 9/5) + 32 = F
                fahrenheit = (celsius_value * 9/5) + 32
                # Return simple format without degree symbol to avoid Unicode issues
                return f"{int(fahrenheit)}F"
            return celsius_str  # Return original if not in expected format
        except (ValueError, TypeError):
            return celsius_str  # Return original on error

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
        except (ValueError, TypeError):
            return "Unknown"

    def ms_to_mph(self, ms_str):
        """Convert m/s to mph with Beaufort classification: '6.8m/s' → '15mph (Moderate Breeze)'"""
        try:
            # Extract numeric value from "X.Xm/s" format
            if isinstance(ms_str, str) and 'm/s' in ms_str:
                ms_value = float(ms_str.replace('m/s', ''))
                # Conversion formula: m/s × 2.237 = mph
                mph = ms_value * 2.237
                mph_rounded = int(mph)
                classification = self.mph_to_wind_classification(mph)
                return f"{mph_rounded}mph ({classification})"
            return ms_str  # Return original if not in expected format
        except (ValueError, TypeError):
            return ms_str  # Return original on error

    def weather_code_to_text(self, weather_code):
        """Convert numeric weather code to natural language"""
        try:
            code = int(weather_code)
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
            return weather_mapping.get(code, f"Unknown ({code})")
        except (ValueError, TypeError):
            return f"Unknown ({weather_code})"

    def convert_environment_data(self, environment):
        """Convert all environment data to user-friendly formats"""
        if not isinstance(environment, dict):
            return environment
        
        converted_env = environment.copy()
        
        # Convert temperature: Celsius → Fahrenheit
        if 'temperature' in converted_env:
            converted_env['temperature'] = self.celsius_to_fahrenheit(converted_env['temperature'])
        
        # Convert wind speed: m/s → mph with Beaufort classification
        if 'wind' in converted_env:
            converted_env['wind'] = self.ms_to_mph(converted_env['wind'])
        
        # Convert weather code: numeric → natural language
        if 'weather' in converted_env:
            converted_env['weather'] = self.weather_code_to_text(converted_env['weather'])
        
        # Keep pressure and humidity unchanged (already in standard units)
        
        return converted_env

    def convert_odds_array(self, odds_array, market_type):
        """Convert odds array with American odds conversion based on market type"""
        if not isinstance(odds_array, list) or len(odds_array) < 5:
            return None
        
        try:
            # Make a copy to avoid modifying original
            converted_array = odds_array.copy()
            
            # Convert odds based on market type
            if market_type == "MoneyLine":
                # Convert European to American for fields [2], [3], [4]
                converted_array[2] = self.convert_european_to_american(odds_array[2])
                converted_array[3] = self.convert_european_to_american(odds_array[3])
                converted_array[4] = self.convert_european_to_american(odds_array[4])
            elif market_type in ["Spread", "O/U", "Corners"]:
                # Convert Hong Kong to American for fields [2] and [4], leave [3] unchanged
                converted_array[2] = self.convert_hongkong_to_american(odds_array[2])
                converted_array[4] = self.convert_hongkong_to_american(odds_array[4])
                # Field [3] (line/handicap/total) stays unchanged
            
            # Extract converted fields
            timestamp = converted_array[0]  # Filter out
            minute = converted_array[1]
            field3 = converted_array[2] 
            field4 = converted_array[3]
            field5 = converted_array[4]
            
            # Return structured format with converted American odds
            if market_type == "Spread":
                return {
                    "time_of_match": minute,
                    "Home": field3,      # American odds
                    "Spread": field4,    # Line unchanged
                    "Away": field5       # American odds
                }
            elif market_type == "MoneyLine":
                return {
                    "time_of_match": minute,
                    "Home": field3,      # American odds
                    "Tie": field4,       # American odds
                    "Away": field5       # American odds
                }
            elif market_type == "O/U":
                return {
                    "time_of_match": minute,
                    "Over": field3,      # American odds
                    "Total": field4,     # Total unchanged
                    "Under": field5      # American odds
                }
            elif market_type == "Corners":
                return {
                    "time_of_match": minute,
                    "Over": field3,      # American odds
                    "Total": field4,     # Total unchanged
                    "Under": field5      # American odds
                }
            else:
                return None
        except Exception as e:
            # On any error, return None to filter out problematic arrays
            return None
    
    def filter_best_time_match(self, odds_arrays):
        """Filter to get the best time match - prefer minute 3, then next closest up to 10"""
        if not isinstance(odds_arrays, list):
            return []
        
        # Convert and organize by minute
        minute_map = {}
        for odds_array in odds_arrays:
            if isinstance(odds_array, list) and len(odds_array) >= 5:
                minute = odds_array[1]  # Field 2 is the minute
                
                # Handle minute filtering
                if minute == "":
                    minute_key = "prematch"
                elif isinstance(minute, str) and minute.isdigit():
                    minute_num = int(minute)
                    if minute_num <= 10:  # Only consider minutes 0-10
                        minute_key = minute_num
                    else:
                        continue  # Skip minutes > 10
                else:
                    continue  # Skip invalid minute values
                
                # Keep the most recent entry for each minute
                minute_map[minute_key] = odds_array
        
        # Find the best minute - prefer 3, then next closest
        target_minute = 3
        best_minute = None
        
        # Check if minute 3 exists
        if target_minute in minute_map:
            best_minute = target_minute
        else:
            # Find the next closest minute (prefer higher, but not exceeding 10)
            available_minutes = [m for m in minute_map.keys() if isinstance(m, int)]
            if available_minutes:
                # Sort and find the closest to 3
                available_minutes.sort()
                
                # Find next higher minute after 3
                higher_minutes = [m for m in available_minutes if m > target_minute]
                if higher_minutes:
                    best_minute = higher_minutes[0]  # Take the smallest higher minute
                else:
                    # If no higher minute, take the highest available
                    best_minute = max(available_minutes)
        
        # If no numeric minute found, check for prematch
        if best_minute is None and "prematch" in minute_map:
            best_minute = "prematch"
        
        # Return the best match or empty list
        if best_minute is not None:
            return [minute_map[best_minute]]
        else:
            return []

    def convert_match_odds(self, match_odds):
        """Convert odds data for a match"""
        if not match_odds or not isinstance(match_odds, dict):
            return None
        
        converted_odds = {}
        
        # Process Bet365 odds (company_id "2")
        if "2" in match_odds:
            bet365_odds = match_odds["2"]
            
            # Process each market type
            for market_name, odds_arrays in bet365_odds.items():
                if market_name in ["Spread", "MoneyLine", "O/U", "Corners"]:
                    # Filter to best time match first
                    filtered_arrays = self.filter_best_time_match(odds_arrays)
                    
                    converted_market = []
                    for odds_array in filtered_arrays:
                        converted_array = self.convert_odds_array(odds_array, market_name)
                        if converted_array:
                            converted_market.append(converted_array)
                    
                    if converted_market:
                        converted_odds[market_name] = converted_market
        
        return converted_odds if converted_odds else None
    
    def process_pretty_print_data(self, pretty_print_data_path):
        """Convert pretty_print.json data with field transformations"""
        
        # Read latest pretty_print from pretty_print.json (last line)
        with open(pretty_print_data_path, 'r') as f:
            lines = f.readlines()
        
        # Get the latest pretty_print data (last line)
        if not lines:
            return {"error": "No valid data in pretty_print.json"}
        
        try:
            latest_pretty_print = json.loads(lines[-1].strip())
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in latest pretty_print"}
        
        # Create conversion data structure
        conversion_data = {
            "CONVERSION_HEADER": latest_pretty_print.get("FETCH_HEADER", {}),
            "CONVERTED_DATA": {
                "SOURCE_PRETTY_PRINT_HEADER": latest_pretty_print.get("FETCH_HEADER", {}),
                "MATCHES_WITH_CONVERTED_ODDS": []
            }
        }
        
        # Process matches and convert odds
        merged_data = latest_pretty_print.get("MERGED_DATA", {})
        match_centric_data = merged_data.get("MERGED_MATCH_CENTRIC_DATA", {})
        matches = match_centric_data.get("matches", [])
        
        # Get odds data from raw API data
        raw_api_data = merged_data.get("SOURCE_RAW_API_DATA", {})
        match_odds_data = raw_api_data.get("match_odds", [])
        
        for i, match in enumerate(matches):
            match_id = match.get("match_id")
            
            # Find corresponding odds for this match
            match_odds = None
            if i < len(match_odds_data):
                odds_results = match_odds_data[i].get("results", {})
                match_odds = self.convert_match_odds(odds_results)
            
            # Create formatted live score string
            live_data = match.get("live_data", {})
            parsed_score = live_data.get("parsed_score", {})
            home_detailed = parsed_score.get("home_detailed", {})
            away_detailed = parsed_score.get("away_detailed", {})
            
            # Extract scores
            home_regular = home_detailed.get("score_regular", 0)
            away_regular = away_detailed.get("score_regular", 0)
            home_halftime = home_detailed.get("score_halftime", 0)
            away_halftime = away_detailed.get("score_halftime", 0)
            
            # Format: Live Score: 2-1 (HT: 1-1)
            formatted_live_score = f"Live Score: {home_regular}-{away_regular} (HT: {home_halftime}-{away_halftime})"
            
            # Get the raw match details that include environment data
            raw_api_data = merged_data.get("SOURCE_RAW_API_DATA", {})
            match_details_data = raw_api_data.get("match_details", [])
            raw_match_details = None
            if i < len(match_details_data):
                raw_match_details = match_details_data[i].get("results", [])
                if raw_match_details and len(raw_match_details) > 0:
                    raw_match_details = raw_match_details[0].copy()  # Get first result
                    
                    # Convert environment data if present
                    if 'environment' in raw_match_details:
                        raw_match_details['environment'] = self.convert_environment_data(raw_match_details['environment'])
            
            # Extract corner data for easy access
            home_corners = home_detailed.get("corners", 0)
            away_corners = away_detailed.get("corners", 0)
            
            # Include all matches regardless of odds data - flow through everything including environment
            converted_match = {
                "match_id": match_id,
                "formatted_live_score": formatted_live_score,      # Combined score display
                "Home Corners": home_corners,                     # Extracted home team corners
                "Away Corners": away_corners,                     # Extracted away team corners
                "live_data": match.get("live_data", {}),          # Flow through live score data
                "match_details": match.get("match_details", {}),   # Flow through parsed match details
                "raw_match_details": raw_match_details,           # Flow through raw match details (includes environment/weather)
                "home_team": match.get("home_team", {}),
                "away_team": match.get("away_team", {}), 
                "competition": match.get("competition", {}),
                "converted_odds": match_odds if match_odds else None
            }
            
            conversion_data["CONVERTED_DATA"]["MATCHES_WITH_CONVERTED_ODDS"].append(converted_match)
        
        # Add detailed footer (catch-all flow-through from pipeline)
        source_footer = merged_data.get("SOURCE_ALL_API_FOOTER", {})
        
        conversion_data["CONVERSION_FOOTER"] = {
            "random_fetch_id": latest_pretty_print.get("FETCH_HEADER", {}).get("random_fetch_id"),
            "nyc_timestamp": datetime.now(pytz.timezone('America/New_York')).strftime("%m/%d/%Y %I:%M:%S %p %Z"),
            "conversion_completion_time_seconds": 0.001,
            "fetch_end": "=== CONVERSION DATA END ===",
            "total_matches_with_odds": len(conversion_data["CONVERTED_DATA"]["MATCHES_WITH_CONVERTED_ODDS"]),
            # Flow-through detailed pipeline stats
            "pipeline_completion_time_seconds": source_footer.get("pipeline_completion_time_seconds", 0),
            "total_matches": source_footer.get("total_matches", 0),
            "matches_in_play": source_footer.get("matches_in_play", 0),
            "match_status_breakdown": source_footer.get("match_status_breakdown", [])
        }
        
        # Log the conversion data
        self.logger.log_fetch(conversion_data)
        
        # Trigger monitor_central.py after conversion completes
        self.trigger_monitor_central()
        
        return conversion_data
    
    def trigger_monitor_central(self):
        """Trigger monitor_central.py to process the latest pretty_print_conversion.json data"""
        try:
            import subprocess
            import sys
            
            # Run monitor_central.py as a subprocess to process the latest data
            monitor_central_script_path = os.path.join(os.path.dirname(__file__), '..', '6_monitor_central', 'monitor_central.py')
            
            # Execute monitor_central.py with the current pretty_print_conversion.json
            subprocess.run([sys.executable, monitor_central_script_path, '--single-run'], 
                          cwd=os.path.join(os.path.dirname(__file__), '..', '6_monitor_central'),
                          check=False)  # Don't raise exception if monitor_central fails
            
        except Exception as e:
            print(f"Warning: Could not trigger monitor_central process: {e}")
            # Continue normal operation even if monitor_central fails

# Initialize the processor
pretty_conversion_processor = PrettyPrintConversionProcessor()

# Main execution
if __name__ == "__main__":
    import sys
    
    # Check for single-run mode (called by pretty_print.py)
    single_run_mode = '--single-run' in sys.argv
    
    if single_run_mode:
        # Single execution mode - just do one pass-through and exit
        try:
            result = pretty_conversion_processor.process_pretty_print_data("../4_pretty_print/pretty_print.json")
            print(f"Single pretty-conversion completed! Logged to: {pretty_conversion_processor.logger.log_path}")
        except Exception as e:
            print(f"Single pretty-conversion failed: {e}")
        sys.exit(0)
    
    # Continuous mode (if run standalone)
    running = True
    
    def signal_handler(sig, frame):
        global running
        print("\nReceived shutdown signal. Stopping continuous pretty-conversion...")
        running = False
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def continuous_pretty_conversion():
        global running
        conversion_count = 0
        
        print("Starting Pretty Print Conversion Continuous Pass-Through...")
        print("Processing every 60 seconds from pretty_print.json")
        print("Press Ctrl+C to stop gracefully")
        print("-" * 60)
        
        while running:
            conversion_count += 1
            start_time = time.time()
            
            try:
                print(f"\n[Conversion #{conversion_count}] Starting pass-through...")
                
                # Perform the pass-through
                result = pretty_conversion_processor.process_pretty_print_data("../4_pretty_print/pretty_print.json")
                
                # Calculate duration
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"[Conversion #{conversion_count}] Completed in {duration:.2f} seconds")
                print(f"[Conversion #{conversion_count}] Logged to: {pretty_conversion_processor.logger.log_path}")
                
                # Calculate wait time (60 seconds total cycle time)
                target_interval = 60
                wait_time = max(0, target_interval - duration)
                
                if wait_time > 0:
                    print(f"[Conversion #{conversion_count}] Waiting {wait_time:.2f} seconds...")
                    
                    # Wait in small increments to allow for graceful shutdown
                    wait_start = time.time()
                    while running and (time.time() - wait_start) < wait_time:
                        time.sleep(0.5)
                else:
                    print(f"[Conversion #{conversion_count}] Starting next pass-through immediately")
                
            except Exception as e:
                print(f"[Conversion #{conversion_count}] Error occurred: {e}")
                print(f"[Conversion #{conversion_count}] Waiting 60 seconds before retry...")
                
                # Wait before retry
                wait_start = time.time()
                while running and (time.time() - wait_start) < 60:
                    time.sleep(0.5)
        
        print("\nContinuous pretty-conversion stopped. Goodbye!")
    
    # Run the continuous pretty-conversion
    try:
        continuous_pretty_conversion()
    except KeyboardInterrupt:
        print("\nShutdown complete.")