#!/usr/bin/env python3

import json
import os
from datetime import datetime
import pytz

def get_nyc_timestamp():
    """Get current NYC timestamp in EDT format"""
    nyc_tz = pytz.timezone('America/New_York')
    return datetime.now(nyc_tz).strftime('%m/%d/%Y %I:%M:%S %p %Z')

def parse_bookended_format(content):
    """Parse bookended format from all_api.json into structured data"""
    parsed_entries = []
    
    try:
        # Split by fetch start markers
        sections = content.split('=== FETCH START:')
        
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            try:
                # Find the JSON content between start and end markers
                json_start = section.find('\n{')
                
                # Find the corresponding end marker
                end_marker_pos = section.find('=== FETCH END:')
                if end_marker_pos != -1:
                    # JSON ends before the end marker
                    json_content = section[json_start:end_marker_pos].strip()
                    # Find the last closing brace
                    last_brace = json_content.rfind('}')
                    if last_brace != -1:
                        json_content = json_content[:last_brace + 1]
                else:
                    # No end marker found, take everything after json_start
                    json_content = section[json_start:].strip()
                
                if json_start != -1 and json_content:
                    entry = json.loads(json_content)
                    parsed_entries.append(entry)
                    
            except json.JSONDecodeError as e:
                print(f"[VAR Logger] Skipping malformed JSON in section {i}: {e}")
                continue
            except Exception as e:
                print(f"[VAR Logger] Error parsing section {i}: {e}")
                continue
    
    except Exception as e:
        print(f"[VAR Logger] Error parsing bookended format: {e}")
    
    return parsed_entries

def load_existing_var_incidents(var_logger_file):
    """Load existing VAR incidents to check for duplicates"""
    existing_incidents = set()
    
    if os.path.exists(var_logger_file):
        try:
            with open(var_logger_file, 'r') as f:
                existing_data = json.load(f)
            
            # Extract incident signatures from existing data
            var_data = existing_data.get('VAR_FILTERED_DATA', [])
            for incident_entry in var_data:
                # New format - each entry is an individual incident
                if 'var_incident' in incident_entry:
                    match_id = incident_entry.get('match_id')
                    incident = incident_entry.get('var_incident', {})
                    signature = f"{match_id}_{incident.get('player_id')}_{incident.get('time')}_{incident.get('var_reason')}_{incident.get('var_result')}"
                    existing_incidents.add(signature)
            
            print(f"[VAR Logger] Loaded {len(existing_incidents)} existing VAR incidents to avoid duplicates")
        except Exception as e:
            print(f"[VAR Logger] Error loading existing incidents: {e}")
    
    return existing_incidents

def load_processed_fetch_ids():
    """Load list of fetch IDs that have already been processed by VAR logger"""
    processed_file = '/root/Guaranteed_last_one/1_all_api/var_processed_fetch_ids.json'
    processed_ids = set()
    
    if os.path.exists(processed_file):
        try:
            with open(processed_file, 'r') as f:
                data = json.load(f)
            processed_ids = set(data.get('processed_fetch_ids', []))
            print(f"[VAR Logger] Loaded {len(processed_ids)} processed fetch IDs")
        except Exception as e:
            print(f"[VAR Logger] Error loading processed fetch IDs: {e}")
    
    return processed_ids

def save_processed_fetch_ids(processed_ids):
    """Save list of processed fetch IDs"""
    processed_file = '/root/Guaranteed_last_one/1_all_api/var_processed_fetch_ids.json'
    try:
        data = {
            'last_updated': get_nyc_timestamp(),
            'processed_fetch_ids': list(processed_ids)
        }
        with open(processed_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[VAR Logger] Saved {len(processed_ids)} processed fetch IDs")
    except Exception as e:
        print(f"[VAR Logger] Error saving processed fetch IDs: {e}")

def is_incident_duplicate(incident, match_id, existing_incidents):
    """Check if a VAR incident is already logged"""
    signature = f"{match_id}_{incident.get('player_id')}_{incident.get('time')}_{incident.get('var_reason')}_{incident.get('var_result')}"
    return signature in existing_incidents

def pure_catch_all_var_filter():
    """
    Pure catch-all pass-through of all_api.json with VAR-only filtering
    Processes only NEW fetches and avoids duplicating previously logged VAR incidents
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
    
    # Load existing VAR incidents and processed fetch IDs to avoid duplicates
    existing_incidents = load_existing_var_incidents(var_logger_file)
    processed_fetch_ids = load_processed_fetch_ids()
    
    try:
        # Read and parse bookended format from all_api.json
        with open(all_api_file, 'r') as f:
            content = f.read().strip()
        
        if not content:
            print(f"[VAR Logger] all_api.json is empty")
            return
            
        # Parse bookended format (same logic as S3 script)
        all_api_data = parse_bookended_format(content)
        
        if not all_api_data:
            print(f"[VAR Logger] No valid data found in all_api.json")
            return
            
        print(f"[VAR Logger] Loaded {len(all_api_data)} total fetch(es) from all_api.json")
        
        # Filter for ONLY NEW fetches (not already processed)
        new_fetches = []
        for fetch in all_api_data:
            fetch_id = fetch.get('FETCH_HEADER', {}).get('random_fetch_id')
            if fetch_id and fetch_id not in processed_fetch_ids:
                new_fetches.append(fetch)
                print(f"[VAR Logger] NEW FETCH: {fetch_id}")
            else:
                print(f"[VAR Logger] ALREADY PROCESSED: {fetch_id}")
        
        if not new_fetches:
            print(f"[VAR Logger] No new fetches to process")
            return
            
        print(f"[VAR Logger] Processing {len(new_fetches)} NEW fetches")
        
        # Process ONLY NEW fetches for VAR incidents
        var_filtered_data = []
        total_var_incidents = 0
        new_incidents_count = 0
        new_processed_ids = set()
        
        for fetch in new_fetches:
            # Get fetch info
            fetch_header = fetch.get('FETCH_HEADER', {})
            fetch_number = fetch_header.get('fetch_number', 'unknown')
            fetch_timestamp = fetch_header.get('nyc_timestamp', 'unknown')
            fetch_id = fetch_header.get('random_fetch_id')
            
            # Mark this fetch as processed
            new_processed_ids.add(fetch_id)
            
            # Extract matches from RAW_API_DATA
            raw_api_data = fetch.get('RAW_API_DATA', {})
            live_matches = raw_api_data.get('live_matches', {})
            matches = live_matches.get('results', [])
            
            # Filter for NEW VAR incidents in this fetch
            fetch_var_incidents = []
            
            for match in matches:
                match_id = match.get('id', 'unknown')
                incidents = match.get('incidents', [])
                
                # Find NEW VAR incidents (type 28) that haven't been logged
                for incident in incidents:
                    if incident.get('type') == 28:
                        total_var_incidents += 1
                        # Check if this incident is new
                        if not is_incident_duplicate(incident, match_id, existing_incidents):
                            # Create individual VAR incident entry with timestamp
                            individual_var_incident = {
                                'var_incident_id': f"{match_id}_{incident.get('player_id')}_{incident.get('time')}",
                                'detected_timestamp': get_nyc_timestamp(),
                                'fetch_info': {
                                    'fetch_number': fetch_number,
                                    'fetch_id': fetch_header.get('random_fetch_id'),
                                    'fetch_timestamp': fetch_timestamp
                                },
                                'match_id': match_id,
                                'var_incident': incident
                            }
                            fetch_var_incidents.append(individual_var_incident)
                            new_incidents_count += 1
                            print(f"[VAR Logger] NEW VAR incident: {match_id} - {incident.get('player_name', 'Unknown')}")
                        else:
                            print(f"[VAR Logger] DUPLICATE VAR incident skipped: {match_id} - {incident.get('player_name', 'Unknown')}")
            
            # Add individual incidents directly to var_filtered_data
            if fetch_var_incidents:
                var_filtered_data.extend(fetch_var_incidents)
                print(f"[VAR Logger] Fetch #{fetch_number}: Found {len(fetch_var_incidents)} NEW VAR incidents")
            else:
                print(f"[VAR Logger] Fetch #{fetch_number}: No NEW VAR incidents found")
        
        # Only proceed if there are NEW incidents to log
        if new_incidents_count > 0:
            # Load existing data to append to
            if os.path.exists(var_logger_file):
                try:
                    with open(var_logger_file, 'r') as f:
                        existing_data = json.load(f)
                    existing_var_data = existing_data.get('VAR_FILTERED_DATA', [])
                except:
                    existing_var_data = []
            else:
                existing_var_data = []
            
            # Append new incidents to existing data
            all_var_data = existing_var_data + var_filtered_data
            
            # Create final output structure
            output_data = {
                "VAR_LOGGER_HEADER": {
                    "timestamp": get_nyc_timestamp(),
                    "source_file": "all_api.json",
                    "operation": "pure_catch_all_var_filter",
                    "total_fetches_processed": len(all_api_data),
                    "new_incidents_this_run": new_incidents_count,
                    "total_incidents_in_file": len(all_var_data)
                },
                "VAR_FILTERED_DATA": all_var_data
            }
            
            # Write complete data back to file
            with open(var_logger_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"[VAR Logger] Successfully processed {len(new_fetches)} NEW fetches")
            print(f"[VAR Logger] Found {new_incidents_count} NEW VAR incidents")
            print(f"[VAR Logger] Updated VAR log written to {var_logger_file}")
        else:
            print(f"[VAR Logger] No new VAR incidents found - file unchanged")
        
        # Save processed fetch IDs (regardless of whether incidents were found)
        if new_processed_ids:
            updated_processed_ids = processed_fetch_ids.union(new_processed_ids)
            save_processed_fetch_ids(updated_processed_ids)
            print(f"[VAR Logger] Marked {len(new_processed_ids)} fetch IDs as processed")
        
    except Exception as e:
        print(f"[VAR Logger] Error during catch-all VAR filtering: {str(e)}")

if __name__ == "__main__":
    pure_catch_all_var_filter()