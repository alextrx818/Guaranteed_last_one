import json
import os
from datetime import datetime
import threading

class PersistentStateManager:
    def __init__(self, stage_name, max_fetches=50):
        self.stage_name = stage_name
        self.max_fetches = max_fetches
        self.state_file = f"{stage_name}_fetch_state.json"
        self.lock = threading.Lock()
    
    def load_state(self):
        """Load fetch count and accumulated data from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('fetch_count', 0), state.get('accumulated_data', [])
        except Exception as e:
            print(f"Warning: Could not load state for {self.stage_name}: {e}")
        return 0, []
    
    def save_state(self, fetch_count, accumulated_data):
        """Save fetch count and accumulated data to file"""
        try:
            with self.lock:
                state = {
                    'fetch_count': fetch_count,
                    'accumulated_data': accumulated_data,
                    'last_updated': datetime.now().isoformat()
                }
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state for {self.stage_name}: {e}")
    
    def should_rotate(self, fetch_count):
        """Check if rotation should occur"""
        return fetch_count >= self.max_fetches
    
    def reset_state(self):
        """Reset state after rotation"""
        self.save_state(0, [])