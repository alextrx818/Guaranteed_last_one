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

class PrettyPrintConversionRotatingS3Logger:
    def __init__(self, bucket_name="sports-json-logs-all", folder_name="pretty_print_conversion_rotating_logs", max_fetches=10):
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
        print(f"[Pretty Print Conversion S3 Logger] Initialized - logs converted data from pretty_print_conversion")
    
    def is_new_day(self):
        """Check if it's a new day and reset counters if needed"""
        nyc_tz = pytz.timezone('America/New_York')
        today = datetime.now(nyc_tz).date()
        
        if self.current_date != today:
            print(f"[Pretty Print Conversion S3 Logger] New day detected: {today}")
            self.current_date = today
            return True
        return False
    
    def load_rotation_state(self):
        """Load local rotation count from state file"""
        state_file = 'pretty_print_conversion_rotation_state.json'
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.local_fetch_count = state.get('local_fetch_count', 0)
                    print(f"[Pretty Print Conversion S3 Logger] Restored rotation count: {self.local_fetch_count}")
            else:
                self.local_fetch_count = 0
                print(f"[Pretty Print Conversion S3 Logger] Starting fresh rotation count: {self.local_fetch_count}")
        except Exception as e:
            print(f"[Pretty Print Conversion S3 Logger] Error loading rotation state: {e}")
            self.local_fetch_count = 0
    
    def save_rotation_state(self):
        """Save current rotation count to state file"""
        state_file = 'pretty_print_conversion_rotation_state.json'
        try:
            state = {'local_fetch_count': self.local_fetch_count}
            with open(state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"[Pretty Print Conversion S3 Logger] Error saving rotation state: {e}")
    
    def create_log_entry(self, conversion_data, fetch_id, nyc_timestamp):
        """Create a single log entry with conversion data - EXTRACT fetch info from conversion data"""
        
        # EXTRACT fetch info from conversion data (READ-ONLY)
        # The conversion data should contain the original fetch header information
        fetch_number = "unknown"
        original_fetch_id = fetch_id  # Use the provided fetch_id
        original_timestamp = nyc_timestamp  # Use the provided timestamp
        
        # Try to extract fetch number from conversion data if available
        if isinstance(conversion_data, dict):
            # Look for fetch info in various possible locations
            if "CONVERSION_HEADER" in conversion_data:
                fetch_number = conversion_data["CONVERSION_HEADER"].get("fetch_number", "unknown")
            elif "FETCH_HEADER" in conversion_data:
                fetch_number = conversion_data["FETCH_HEADER"].get("fetch_number", "unknown")
            elif "CONVERTED_DATA" in conversion_data and "SOURCE_PRETTY_PRINT_HEADER" in conversion_data["CONVERTED_DATA"]:
                fetch_number = conversion_data["CONVERTED_DATA"]["SOURCE_PRETTY_PRINT_HEADER"].get("fetch_number", "unknown")
            elif "SOURCE_ALL_API_HEADER" in conversion_data:
                fetch_number = conversion_data["SOURCE_ALL_API_HEADER"].get("fetch_number", "unknown")
        
        # Increment local rotation counter only (not fetch number!)
        self.local_fetch_count += 1
        
        # Save rotation state after incrementing
        self.save_rotation_state()
        
        print(f"[Pretty Print Conversion S3 Logger] Processing Fetch #{fetch_number} | ID: {original_fetch_id} (conversion data)")
        
        # Write to local pretty_print_conversion.json in bookended format - PRESERVE original fetch info
        with open('pretty_print_conversion.json', 'a') as f:
            f.write(f'=== FETCH START: #{fetch_number} | {original_fetch_id} | {original_timestamp} ===\n')
            json.dump(conversion_data, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: #{fetch_number} | {original_fetch_id} | {original_timestamp} ===\n')
        
        print(f"[Pretty Print Conversion S3 Logger] Added fetch #{fetch_number} to rotation ({self.local_fetch_count}/{self.max_fetches})")
        
        # Check if rotation is needed
        if self.local_fetch_count >= self.max_fetches:
            self.upload_to_s3_and_rotate()
    
    def read_bookended_format(self):
        """Read bookended format from pretty_print_conversion.json as raw text"""
        try:
            with open('pretty_print_conversion.json', 'r') as f:
                content = f.read().strip()
            return content
        except FileNotFoundError:
            return ""
        except Exception as e:
            print(f"[Pretty Print Conversion S3 Logger] Error reading local file: {e}")
            return ""
    
    def upload_to_s3_and_rotate(self):
        """Upload current log to S3 and rotate local files"""
        try:
            # Check if it's a new day
            if self.is_new_day():
                print(f"[Pretty Print Conversion S3 Logger] New day detected, creating fresh S3 file")
            
            # Read bookended format content
            bookended_content = self.read_bookended_format()
            
            if not bookended_content:
                print(f"[Pretty Print Conversion S3 Logger] No content to upload")
                return
            
            # Generate S3 key with date
            date_str = self.current_date.strftime("%Y-%m-%d")
            s3_key = f"{self.folder_name}/pretty_print_conversion_rotating_logs_{date_str}.txt"
            
            # Upload to S3 (append mode - check if file exists and append)
            try:
                # Try to get existing content
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                existing_content = response['Body'].read().decode('utf-8')
                combined_content = existing_content + "\n" + bookended_content
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    # File doesn't exist, use new content
                    combined_content = bookended_content
                else:
                    raise
            
            # Upload combined content
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=combined_content.encode('utf-8'),
                ContentType='text/plain'
            )
            
            print(f"[Pretty Print Conversion S3 Logger] Uploaded {len(bookended_content)} chars to S3: {s3_key}")
            
            # Reset local rotation counter
            self.local_fetch_count = 0
            self.save_rotation_state()
            
            # Clear local file
            with open('pretty_print_conversion.json', 'w') as f:
                f.write("")
            
            print(f"[Pretty Print Conversion S3 Logger] Rotation complete - local files cleared")
            
        except Exception as e:
            print(f"[Pretty Print Conversion S3 Logger] Error uploading to S3: {e}")
            # Keep local data if S3 upload fails

def main():
    """Main function to handle external script calls"""
    if len(sys.argv) != 2:
        print("Usage: python pretty_print_conversion_rotating_s3.py <temp_file_path>")
        sys.exit(1)
    
    temp_file_path = sys.argv[1]
    
    try:
        # Read log data from temp file
        with open(temp_file_path, 'r') as f:
            log_data = json.load(f)
        
        # Extract the data from the temp file
        conversion_data = log_data.get("conversion_data")
        fetch_id = log_data.get("fetch_id")
        nyc_timestamp = log_data.get("nyc_timestamp")
        
        # Create logger and process data
        logger = PrettyPrintConversionRotatingS3Logger()
        logger.create_log_entry(conversion_data, fetch_id, nyc_timestamp)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"[Pretty Print Conversion S3 Logger] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()