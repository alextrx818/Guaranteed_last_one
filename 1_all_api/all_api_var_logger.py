#!/usr/bin/env python3

import json
import os
from datetime import datetime
import pytz

def get_nyc_timestamp():
    """Get current NYC timestamp in EDT format"""
    nyc_tz = pytz.timezone('America/New_York')
    return datetime.now(nyc_tz).strftime('%m/%d/%Y %I:%M:%S %p %Z')

def pure_catch_all_var_filter():
    """
    Pure catch-all pass-through of all_api.json with VAR-only filtering
    Processes ALL fetches but filters out everything except VAR incidents (type 28)
    """
    
    # File paths
    all_api_file = os.path.join(os.path.dirname(__file__), 'all_api.json')
    var_logger_file = os.path.join(os.path.dirname(__file__), 'all_api_var_logger.json')
    
    print(f"[VAR Logger] Starting pure catch-all with VAR-only filter")
    print(f"[VAR Logger] Reading from: {all_api_file}")
    print(f"[VAR Logger] Writing to: {var_logger_file}")
    
    if not os.path.exists(all_api_file):
        print(f"[VAR Logger] Error: {all_api_file} not found")
        return
    
    try:
        # Read the entire all_api.json file
        with open(all_api_file, 'r') as f:
            all_api_data = json.load(f)
        
        print(f"[VAR Logger] Loaded {len(all_api_data)} total fetch(es) from all_api.json")
        
        # Process ALL fetches and filter for VAR incidents only
        var_filtered_data = []
        total_var_incidents = 0
        
        for fetch in all_api_data:
            # Get fetch info
            fetch_header = fetch.get('FETCH_HEADER', {})
            fetch_number = fetch_header.get('fetch_number', 'unknown')
            fetch_timestamp = fetch_header.get('nyc_timestamp', 'unknown')
            
            # Extract matches from RAW_API_DATA
            raw_api_data = fetch.get('RAW_API_DATA', {})
            live_matches = raw_api_data.get('live_matches', {})
            matches = live_matches.get('results', [])
            
            # Filter for VAR incidents in this fetch
            fetch_var_incidents = []
            
            for match in matches:
                match_id = match.get('id', 'unknown')
                incidents = match.get('incidents', [])
                
                # Find VAR incidents (type 28)
                var_incidents_in_match = []
                for incident in incidents:
                    if incident.get('type') == 28:
                        var_incidents_in_match.append(incident)
                        total_var_incidents += 1
                
                # If this match has VAR incidents, add it to the filtered data
                if var_incidents_in_match:
                    fetch_var_incidents.append({
                        'match_id': match_id,
                        'var_incidents': var_incidents_in_match
                    })
            
            # Create filtered fetch entry
            if fetch_var_incidents:
                var_filtered_data.append({
                    'FETCH_HEADER': fetch_header,
                    'VAR_INCIDENTS': fetch_var_incidents
                })
                print(f"[VAR Logger] Fetch #{fetch_number}: Found {len(fetch_var_incidents)} match(es) with VAR incidents")
            else:
                print(f"[VAR Logger] Fetch #{fetch_number}: No VAR incidents found")
        
        # Create final output structure
        output_data = {
            "VAR_LOGGER_HEADER": {
                "timestamp": get_nyc_timestamp(),
                "source_file": "all_api.json",
                "operation": "pure_catch_all_var_filter",
                "total_fetches_processed": len(all_api_data),
                "fetches_with_var_incidents": len(var_filtered_data),
                "total_var_incidents_found": total_var_incidents
            },
            "VAR_FILTERED_DATA": var_filtered_data
        }
        
        # Write to all_api_var_logger.json (overwrite completely)
        with open(var_logger_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"[VAR Logger] Successfully processed {len(all_api_data)} fetches")
        print(f"[VAR Logger] Found {total_var_incidents} VAR incidents across {len(var_filtered_data)} fetches")
        print(f"[VAR Logger] VAR-filtered data written to {var_logger_file}")
        
    except Exception as e:
        print(f"[VAR Logger] Error during catch-all VAR filtering: {str(e)}")

if __name__ == "__main__":
    pure_catch_all_var_filter()