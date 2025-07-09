#!/usr/bin/env python3
"""
Mirror script for all_api.json - shows last 2,000 lines
Creates all_api_mirror.json with recent entries for easier monitoring
"""

import json
import os
from datetime import datetime

def create_mirror():
    """Read last entries from all_api.json and create mirror file"""
    
    all_api_path = '/root/Guaranteed_last_one/1_all_api/all_api.json'
    mirror_path = '/root/Guaranteed_last_one/1_all_api/all_api_mirror.json'
    
    if not os.path.exists(all_api_path):
        print(f"Source file {all_api_path} not found")
        return
    
    try:
        # Load the entire JSON array
        with open(all_api_path, 'r') as f:
            all_data = json.load(f)
        
        # Get last 1000 entries for monitoring
        recent_entries = all_data[-1000:] if len(all_data) > 1000 else all_data
        
        mirror_data = recent_entries
        
        # Write mirror file with metadata
        mirror_content = {
            "mirror_info": {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source_file": "all_api.json",
                "total_lines_in_source": len(lines),
                "lines_in_mirror": len(mirror_data),
                "showing_last_n_lines": min(2000, len(lines))
            },
            "recent_entries": mirror_data
        }
        
        with open(mirror_path, 'w') as f:
            json.dump(mirror_content, f, indent=2)
        
        print(f"Mirror created: {mirror_path}")
        print(f"Source file has {len(lines)} total lines")
        print(f"Mirror contains last {len(mirror_data)} entries")
        
    except Exception as e:
        print(f"Error creating mirror: {e}")

if __name__ == "__main__":
    create_mirror()