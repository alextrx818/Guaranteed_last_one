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

class PrettyPrintRotatingS3Logger:
    def __init__(self, bucket_name="sports-json-logs-all", folder_name="pretty_print_rotating_logs", max_fetches=10):
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
        print(f"[Pretty Print S3 Logger] Initialized - logs cleaned data from pretty_print")
    
    def is_new_day(self):
        """Check if it's a new day and reset counters if needed"""
        nyc_tz = pytz.timezone('America/New_York')
        today = datetime.now(nyc_tz).date()
        
        if self.current_date != today:
            print(f"[Pretty Print S3 Logger] New day detected: {today}")
            self.current_date = today
            return True
        return False
    
    def load_rotation_state(self):
        """Load local rotation count (separate from daily fetch count)"""
        state_file = 'pretty_print_rotation_state.json'
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                self.local_fetch_count = state.get('local_fetch_count', 0)
                print(f"[Pretty Print S3 Logger] Restored rotation count: {self.local_fetch_count}")
            else:
                self.local_fetch_count = 0
                print(f"[Pretty Print S3 Logger] Starting fresh rotation count: 0")
        except Exception as e:
            print(f"[Pretty Print S3 Logger] Error loading rotation state: {e}")
            self.local_fetch_count = 0
    
    def save_rotation_state(self):
        """Save local rotation count"""
        state_file = 'pretty_print_rotation_state.json'
        try:
            state = {'local_fetch_count': self.local_fetch_count}
            with open(state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"[Pretty Print S3 Logger] Error saving rotation state: {e}")
    
    def create_log_entry(self, cleaned_data, fetch_id, nyc_timestamp):
        """Create a single log entry with cleaned data - EXTRACT fetch info from cleaned data"""
        
        # EXTRACT fetch info from cleaned data (READ-ONLY)
        # The cleaned data should contain the original fetch header information
        fetch_number = "unknown"
        original_fetch_id = fetch_id  # Use the provided fetch_id
        original_timestamp = nyc_timestamp  # Use the provided timestamp
        
        # Try to extract fetch number from cleaned data if available
        if isinstance(cleaned_data, dict):
            # Look for fetch info in various possible locations
            if "FETCH_HEADER" in cleaned_data:
                fetch_number = cleaned_data["FETCH_HEADER"].get("fetch_number", "unknown")
            elif "SOURCE_ALL_API_HEADER" in cleaned_data:
                fetch_number = cleaned_data["SOURCE_ALL_API_HEADER"].get("fetch_number", "unknown")
        
        # Increment local rotation counter only (not fetch number!)
        self.local_fetch_count += 1
        
        # Save rotation state after incrementing
        self.save_rotation_state()
        
        print(f"[Pretty Print S3 Logger] Processing Fetch #{fetch_number} | ID: {original_fetch_id} (cleaned data)")
        
        # Write to local pretty_print.json in bookended format - PRESERVE original fetch info
        with open('pretty_print.json', 'a') as f:
            f.write(f'=== FETCH START: #{fetch_number} | {original_fetch_id} | {original_timestamp} ===\n')
            json.dump(cleaned_data, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: #{fetch_number} | {original_fetch_id} | {original_timestamp} ===\n')
        
        print(f"[Pretty Print S3 Logger] Added fetch #{fetch_number} to rotation ({self.local_fetch_count}/{self.max_fetches})")
        
        # Check if rotation is needed
        if self.local_fetch_count >= self.max_fetches:
            self.upload_to_s3_and_rotate()
    
    def read_bookended_format(self):
        """Read bookended format from pretty_print.json as raw text"""
        try:
            with open('pretty_print.json', 'r') as f:
                content = f.read().strip()
            return content
        except Exception as e:
            print(f"[Pretty Print S3 Logger] Error reading bookended format: {e}")
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
            daily_filename = f"pretty_print_json_log_{date_str}.json"
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
            print(f"[Pretty Print S3 Logger] Successfully uploaded {fetch_count} fetches to S3: {s3_key}")
            
            # Clear local data after successful upload
            self.local_fetch_count = 0
            
            # Save rotation state after reset
            self.save_rotation_state()
            
            # Clear pretty_print.json after successful S3 upload
            with open('pretty_print.json', 'w') as f:
                pass
            
            print(f"[Pretty Print S3 Logger] Rotation complete - local files cleared")
            
        except Exception as e:
            print(f"[Pretty Print S3 Logger] Error uploading to S3: {e}")
            # Keep local data if S3 upload fails

def main():
    """Main function to handle external script calls"""
    if len(sys.argv) != 2:
        print("Usage: python pretty_print_rotating_s3.py <temp_file_path>")
        sys.exit(1)
    
    temp_file_path = sys.argv[1]
    
    try:
        # Read log data from temp file
        with open(temp_file_path, 'r') as f:
            log_data = json.load(f)
        
        # Extract the data from the temp file
        cleaned_data = log_data.get("cleaned_data")
        fetch_id = log_data.get("fetch_id")
        nyc_timestamp = log_data.get("nyc_timestamp")
        
        # Create logger and process data
        logger = PrettyPrintRotatingS3Logger()
        logger.create_log_entry(cleaned_data, fetch_id, nyc_timestamp)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"[Pretty Print S3 Logger] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()