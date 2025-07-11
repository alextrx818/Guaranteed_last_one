#!/usr/bin/env python3

import json
import os
import sys
import random
import string
import time
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, date
import pytz
import tempfile

class MonitorCentralRotatingS3Logger:
    def __init__(self, bucket_name="sports-json-logs-all", folder_name="monitor_central_rotating_logs", max_fetches=10):
        self.bucket_name = bucket_name
        self.folder_name = folder_name
        self.max_fetches = max_fetches
        self.local_fetch_count = 0
        
        # Initialize current date
        nyc_tz = pytz.timezone('America/New_York')
        self.current_date = datetime.now(nyc_tz).date()
        
        # S3 Configuration for Linode Object Storage (Chicago region)
        self.s3_client = boto3.client(
            's3',
            endpoint_url='https://us-ord-1.linodeobjects.com',
            aws_access_key_id='RG24F9TQ2XZ3Z0Q7T9S1',
            aws_secret_access_key='Iuj7L0zE5s2YDh2kGnyIp7FHibGZiH9zaXtWlhEz',
            region_name='us-ord-1'
        )
        
        # Load local rotation count (separate from daily fetch count)
        self.load_rotation_state()
        print(f"[Monitor Central S3 Logger] Initialized - logs monitor data from monitor_central")
    
    def is_new_day(self):
        """Check if it's a new day and reset counters if needed"""
        nyc_tz = pytz.timezone('America/New_York')
        today = datetime.now(nyc_tz).date()
        
        if self.current_date != today:
            print(f"[Monitor Central S3 Logger] New day detected: {today}")
            self.current_date = today
            return True
        return False
    
    def load_rotation_state(self):
        """Load local rotation count (separate from daily fetch count)"""
        state_file = 'monitor_central_rotation_state.json'
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                self.local_fetch_count = state.get('local_fetch_count', 0)
                print(f"[Monitor Central S3 Logger] Restored rotation count: {self.local_fetch_count}")
            else:
                self.local_fetch_count = 0
                print(f"[Monitor Central S3 Logger] Starting fresh rotation count: 0")
        except Exception as e:
            print(f"[Monitor Central S3 Logger] Error loading rotation state: {e}")
            self.local_fetch_count = 0
    
    def save_rotation_state(self):
        """Save local rotation count"""
        state_file = 'monitor_central_rotation_state.json'
        try:
            state = {'local_fetch_count': self.local_fetch_count}
            with open(state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"[Monitor Central S3 Logger] Error saving rotation state: {e}")
    
    def create_log_entry(self, monitor_data, fetch_id, nyc_timestamp):
        """Create a single log entry with monitor data - PURE PASS-THROUGH"""
        
        # PURE PASS-THROUGH - use the exact fetch info provided (no extraction needed)
        # Monitor central is a catch-all pass-through, so preserve original fetch info exactly
        original_fetch_id = fetch_id
        original_timestamp = nyc_timestamp
        
        # Extract fetch number from the original conversion data that monitor_central processes
        # Monitor central processes data from pretty_print_conversion.json which has CONVERSION_HEADER
        fetch_number = "unknown"
        if isinstance(monitor_data, dict):
            # Monitor central processes the raw conversion data, so look for CONVERSION_HEADER
            # The data structure should be from pretty_print_conversion.json
            if "CONVERSION_HEADER" in monitor_data:
                header = monitor_data["CONVERSION_HEADER"]
                if "fetch_number" in header:
                    fetch_number = str(header["fetch_number"])
                if "random_fetch_id" in header:
                    original_fetch_id = header["random_fetch_id"]
                if "nyc_timestamp" in header:
                    original_timestamp = header["nyc_timestamp"]
            # Also check MONITOR_FOOTER for any override data
            elif "MONITOR_FOOTER" in monitor_data:
                footer = monitor_data["MONITOR_FOOTER"]
                if "random_fetch_id" in footer:
                    original_fetch_id = footer["random_fetch_id"]
                if "nyc_timestamp" in footer:
                    original_timestamp = footer["nyc_timestamp"]
        
        # Increment local rotation counter only (not fetch number!)
        self.local_fetch_count += 1
        
        # Save rotation state after incrementing
        self.save_rotation_state()
        
        print(f"[Monitor Central S3 Logger] Processing Fetch #{fetch_number} | ID: {original_fetch_id} (monitor data)")
        
        # Write to local monitor_central.json in bookended format - PRESERVE original fetch info
        with open('monitor_central.json', 'a') as f:
            f.write(f'=== FETCH START: #{fetch_number} | {original_fetch_id} | {original_timestamp} ===\n')
            json.dump(monitor_data, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: #{fetch_number} | {original_fetch_id} | {original_timestamp} ===\n')
        
        print(f"[Monitor Central S3 Logger] Added fetch #{fetch_number} to rotation ({self.local_fetch_count}/{self.max_fetches})")
        
        # Check if rotation is needed
        if self.local_fetch_count >= self.max_fetches:
            self.upload_to_s3_and_rotate()
    
    def read_bookended_format(self):
        """Read bookended format from monitor_central.json as raw text"""
        try:
            with open('monitor_central.json', 'r') as f:
                content = f.read().strip()
            return content
        except Exception as e:
            print(f"[Monitor Central S3 Logger] Error reading bookended format: {e}")
            return ""

    def upload_to_s3_and_rotate(self):
        """Upload bookended format to S3 and rotate local storage"""
        # Check for new day
        self.is_new_day()
        
        # Read bookended format from local file
        bookended_content = self.read_bookended_format()
        if not bookended_content:
            return
            
        try:
            # Create daily filename
            date_str = self.current_date.strftime('%Y-%m-%d')
            daily_filename = f"monitor_central_json_log_{date_str}.json"
            s3_key = f"{self.folder_name}/{daily_filename}"
            
            # Check if daily file exists
            daily_file_exists = False
            existing_content = ""
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                existing_content = response['Body'].read().decode('utf-8')
                daily_file_exists = True
            except ClientError:
                daily_file_exists = False
            
            # Prepare final content
            if daily_file_exists:
                # Append to existing file
                final_content = existing_content + "\n" + bookended_content
            else:
                # Create new file
                final_content = bookended_content
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=final_content,
                ContentType='text/plain'
            )
            
            # Count fetches for reporting
            fetch_count = bookended_content.count('=== FETCH START:')
            print(f"[Monitor Central S3 Logger] Successfully uploaded {fetch_count} fetches to S3: {s3_key}")
            
            # Clear local data after successful upload
            self.local_fetch_count = 0
            
            # Save rotation state after reset
            self.save_rotation_state()
            
            # Clear monitor_central.json after successful S3 upload
            with open('monitor_central.json', 'w') as f:
                pass
            
            print(f"[Monitor Central S3 Logger] Rotation complete - local files cleared")
            
        except Exception as e:
            print(f"[Monitor Central S3 Logger] Error uploading to S3: {e}")
            # Keep local data if S3 upload fails

def main():
    """Main function to handle external script calls"""
    if len(sys.argv) != 2:
        print("Usage: python monitor_central_rotating_s3.py <temp_file_path>")
        sys.exit(1)
    
    temp_file_path = sys.argv[1]
    
    try:
        # Read log data from temp file
        with open(temp_file_path, 'r') as f:
            log_data = json.load(f)
        
        # Extract the data from the temp file
        monitor_data = log_data.get("monitor_data")
        fetch_id = log_data.get("fetch_id")
        nyc_timestamp = log_data.get("nyc_timestamp")
        
        # Create logger and process data
        logger = MonitorCentralRotatingS3Logger()
        logger.create_log_entry(monitor_data, fetch_id, nyc_timestamp)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"[Monitor Central S3 Logger] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()