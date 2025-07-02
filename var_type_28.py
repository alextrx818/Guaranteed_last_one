#!/usr/bin/env python3
"""
VAR Type 28 Scanner
Scans all_api.json for VAR incidents (type 28) and logs them to a JSON file.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

def scan_for_var_type_28(all_api_path: str) -> List[Dict[str, Any]]:
    """
    Scan all_api.json for VAR incidents (type 28).
    
    Args:
        all_api_path: Path to all_api.json file
        
    Returns:
        List of matches with VAR type 28 incidents
    """
    var_matches = []
    
    try:
        with open(all_api_path, 'r') as f:
            data = json.load(f)
        
        # Navigate to the live matches results
        if isinstance(data, list) and len(data) > 0:
            raw_api_data = data[0].get('RAW_API_DATA', {})
            live_matches = raw_api_data.get('live_matches', {})
            results = live_matches.get('results', [])
            
            # Scan each match for VAR incidents
            for match in results:
                match_id = match.get('id', 'unknown')
                incidents = match.get('incidents', [])
                
                # Check for type 28 incidents
                var_incidents = [inc for inc in incidents if inc.get('type') == 28]
                
                if var_incidents:
                    var_match = {
                        'match_id': match_id,
                        'var_incidents': var_incidents,
                        'total_incidents': len(incidents),
                        'var_incident_count': len(var_incidents),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    var_matches.append(var_match)
                    
    except FileNotFoundError:
        print(f"Error: File {all_api_path} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {all_api_path}")
    except Exception as e:
        print(f"Error scanning file: {e}")
    
    return var_matches

def log_var_incidents(var_matches: List[Dict[str, Any]], output_path: str):
    """
    Log VAR incidents to a JSON file.
    
    Args:
        var_matches: List of matches with VAR incidents
        output_path: Path to output JSON file
    """
    log_entry = {
        'scan_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_matches_with_var': len(var_matches),
        'var_matches': var_matches
    }
    
    # Read existing log if it exists
    existing_log = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_log = json.load(f)
        except (json.JSONDecodeError, Exception):
            existing_log = []
    
    # Append new entry
    existing_log.append(log_entry)
    
    # Write back to file
    try:
        with open(output_path, 'w') as f:
            json.dump(existing_log, f, indent=2)
        print(f"VAR incidents logged to {output_path}")
        print(f"Found {len(var_matches)} matches with VAR type 28 incidents")
        
        # Print summary
        if var_matches:
            print("\nVAR Incidents Found:")
            for match in var_matches:
                print(f"  Match {match['match_id']}: {match['var_incident_count']} VAR incidents")
                for incident in match['var_incidents']:
                    print(f"    - Type: {incident.get('type')}, VAR Reason: {incident.get('var_reason')}, VAR Result: {incident.get('var_result')}")
        else:
            print("No VAR type 28 incidents found in current scan")
            
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")

def main():
    # Paths
    all_api_path = '/root/Guaranteed_last_one/1_all_api/all_api.json'
    output_path = '/root/Guaranteed_last_one/var_type_28_log.json'
    
    print("Scanning for VAR type 28 incidents...")
    print(f"Source: {all_api_path}")
    print(f"Output: {output_path}")
    print("-" * 50)
    
    # Scan for VAR incidents
    var_matches = scan_for_var_type_28(all_api_path)
    
    # Log results
    log_var_incidents(var_matches, output_path)

if __name__ == "__main__":
    main()