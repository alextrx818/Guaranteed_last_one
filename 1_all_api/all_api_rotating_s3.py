#!/usr/bin/env python3
"""
Complete Logging System for all_api.py
Handles ALL logging responsibilities:
- Local file logging for pipeline (all_api.json)
- Fetch ID tracking 
- S3 uploads with daily rotation
- 10-fetch local rotation

Called by all_api.py via subprocess with data passed as JSON argument
"""

import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import pytz
import os
import sys
import random
import string

class AllApiCompleteLogger:
    def __init__(self, bucket_name="sports-json-logs-all", folder_name="all_api_rotating_logs", max_fetches=10):
        self.bucket_name = bucket_name
        self.folder_name = folder_name
        self.max_fetches = max_fetches
        self.fetch_count = 0
        self.s3_client = self.setup_s3_client()
        
        # Daily match counting and rotation tracking
        self.current_date = None
        self.daily_match_count = 0
        self.daily_upload_count = 0
        self.first_upload_today = None
        self.daily_fetch_count = 0
        
        # Load persisted daily state
        self.load_daily_state()
        
        print(f"🚀 All API Complete Logger Started")
        print(f"📁 S3 Bucket: {self.bucket_name}")
        print(f"📂 S3 Folder: {self.folder_name}")
        print(f"🔄 Local Rotation: Every {self.max_fetches} fetches")
        print(f"📊 Daily Fetch Counter: {self.daily_fetch_count}")
    
    def setup_s3_client(self):
        """Setup Linode Object Storage client with Chicago region"""
        try:
            return boto3.client('s3',
                endpoint_url='https://us-ord-1.linodeobjects.com',
                aws_access_key_id='RG24F9TQ2XZ3Z0Q7T9S1',
                aws_secret_access_key='Iuj7L0zE5s2YDh2kGnyIp7FHibGZiH9zaXtWlhEz',
                region_name='us-ord-1'
            )
        except Exception as e:
            print(f"❌ Failed to setup S3 client: {e}")
            return None
    
    def generate_random_id(self, length=12):
        """Generate random alphanumeric ID for fetch tracking"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def get_nyc_timestamp(self):
        """Get current NYC timezone timestamp in MM/DD/YYYY format with AM/PM"""
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        return nyc_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
    def get_daily_s3_key(self):
        """Generate S3 key for today's daily file"""
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        date_str = nyc_time.strftime("%Y-%m-%d")
        return f"{self.folder_name}/all_api_json_log_{date_str}.json"
    
    def load_daily_state(self):
        """Load persistent daily fetch count from state file"""
        state_file = 'all_api_daily_fetch_state.json'
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Check if it's the same date
                nyc_tz = pytz.timezone('America/New_York')
                today = datetime.now(nyc_tz).date().isoformat()
                
                if state.get('date') == today:
                    # Same day - restore count
                    self.daily_fetch_count = state.get('daily_fetch_count', 0)
                    self.current_date = datetime.now(nyc_tz).date()
                    print(f"📊 Restored daily fetch count: {self.daily_fetch_count}")
                else:
                    # New day - reset to 0
                    self.daily_fetch_count = 0
                    self.current_date = datetime.now(nyc_tz).date()
                    print(f"📅 New day detected - reset fetch count to 0")
                    self.save_daily_state()  # Save the reset state
            else:
                # No state file - first run
                nyc_tz = pytz.timezone('America/New_York')
                self.current_date = datetime.now(nyc_tz).date()
                self.daily_fetch_count = 0
                print(f"🆕 First run - initialized fetch count to 0")
                self.save_daily_state()
        except Exception as e:
            print(f"⚠️ Error loading daily state: {e}")
            # Fallback to 0 if error
            nyc_tz = pytz.timezone('America/New_York')
            self.current_date = datetime.now(nyc_tz).date()
            self.daily_fetch_count = 0
    
    def save_daily_state(self):
        """Save current daily fetch count to state file"""
        state_file = 'all_api_daily_fetch_state.json'
        try:
            state = {
                'date': self.current_date.isoformat() if self.current_date else None,
                'daily_fetch_count': self.daily_fetch_count,
                'last_updated': self.get_nyc_timestamp()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving daily state: {e}")
    
    def is_new_day(self):
        """Detect midnight crossover and reset daily counters"""
        nyc_tz = pytz.timezone('America/New_York')
        current_date = datetime.now(nyc_tz).date()
        
        if self.current_date is None:
            # First run - initialize with current date
            self.current_date = current_date
            self.daily_match_count = 0
            self.daily_upload_count = 0
            self.first_upload_today = None
            print(f"📅 Initialized daily tracking for: {current_date}")
            return False
        
        if current_date > self.current_date:
            # New day detected - reset all counters
            old_date = self.current_date
            self.current_date = current_date
            self.daily_match_count = 0
            self.daily_upload_count = 0
            self.first_upload_today = None
            self.daily_fetch_count = 0
            print(f"🌅 NEW DAY DETECTED: {old_date} → {current_date}")
            print(f"🔄 Daily counters reset - Starting fresh count")
            return True
        
        return False
    
    def check_daily_file_exists(self, s3_key):
        """Check if daily file already exists in S3 to prevent duplicates"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True  # File exists
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return False  # File doesn't exist
            else:
                print(f"⚠️ Error checking file existence: {e}")
                return False  # Assume doesn't exist on error
    
    def count_matches_in_upload(self, fetch_data):
        """Count total matches across all fetches in current upload"""
        total_matches = 0
        try:
            for fetch in fetch_data:
                if isinstance(fetch, dict) and "FETCH_FOOTER" in fetch:
                    matches = fetch["FETCH_FOOTER"].get("total_matches", 0)
                    total_matches += matches
            return total_matches
        except Exception as e:
            print(f"⚠️ Error counting matches: {e}")
            return 0
    
    def get_daily_metadata(self, matches_in_upload):
        """Generate metadata for daily file"""
        timestamp = self.get_nyc_timestamp()
        
        # Update daily counters
        self.daily_match_count += matches_in_upload
        self.daily_upload_count += 1
        
        if self.first_upload_today is None:
            self.first_upload_today = timestamp
        
        return {
            "date": self.current_date.strftime("%Y-%m-%d"),
            "total_uploads_today": self.daily_upload_count,
            "total_matches_today": self.daily_match_count,
            "first_upload_today": self.first_upload_today,
            "last_upload": timestamp,
            "matches_in_this_upload": matches_in_upload
        }
    
    def test_s3_connection(self):
        """Test connection to Linode Object Storage"""
        print(f"🧪 Testing connection to Linode Object Storage...")
        print(f"📍 Endpoint: https://us-ord-1.linodeobjects.com")
        print(f"📁 Bucket: {self.bucket_name}")
        
        if not self.s3_client:
            print(f"❌ S3 client not initialized")
            return False
        
        try:
            # Test 1: List bucket to verify access
            print(f"🔍 Test 1: Checking bucket access...")
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket access confirmed")
            
            # Test 2: Test upload a small file
            print(f"🔍 Test 2: Testing file upload...")
            test_key = f"{self.folder_name}/connection_test.json"
            test_data = {
                "test": "connection successful",
                "timestamp": self.get_nyc_timestamp(),
                "bucket": self.bucket_name,
                "endpoint": "us-ord-1.linodeobjects.com"
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=json.dumps(test_data, indent=2),
                ContentType='application/json'
            )
            print(f"✅ Test file uploaded: {test_key}")
            
            # Test 3: Test download the file we just uploaded
            print(f"🔍 Test 3: Testing file download...")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=test_key)
            downloaded_data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"✅ Test file downloaded and parsed successfully")
            
            # Test 4: Clean up test file
            print(f"🔍 Test 4: Cleaning up test file...")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            print(f"✅ Test file deleted")
            
            print(f"🎉 ALL TESTS PASSED - Linode S3 connection is working!")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ AWS Error: {error_code} - {error_message}")
            return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def log_fetch_id_tracking(self, fetch_id):
        """Log fetch ID with timestamp for pipeline tracking"""
        tracking_entry = {
            "fetch_id": fetch_id,
            "created_at": self.get_nyc_timestamp(),
            "status": "created",
            "merge.py": "",
            "pretty_print.py": "",
            "pretty_print_conversion.py": "",
            "monitor_central.py": "",
            "alert_3ou_half.py": "",
            "alert_underdog_0half.py": ""
        }
        
        # Append to tracking log
        with open('all_api_fetch_id_tracking.json', 'a') as f:
            json.dump(tracking_entry, f, indent=2)
            f.write('\n')
    
    def count_current_fetches(self):
        """Count current fetches in all_api.json to determine fetch number"""
        try:
            if not os.path.exists('all_api.json'):
                return 0
            
            with open('all_api.json', 'r') as f:
                content = f.read()
            
            # Count fetch start markers
            fetch_count = content.count('=== FETCH START:')
            return fetch_count
            
        except Exception as e:
            print(f"⚠️ Error counting fetches: {e}")
            return 0
    
    def create_log_entry(self, raw_data, pipeline_duration=None, match_stats=None):
        """Create structured log entry"""
        fetch_id = self.generate_random_id()
        nyc_timestamp = self.get_nyc_timestamp()
        
        # Check for new day and increment daily fetch counter
        self.is_new_day()
        self.daily_fetch_count += 1
        fetch_number = self.daily_fetch_count
        
        # Save state after incrementing fetch count
        self.save_daily_state()
        
        # Log fetch ID tracking
        self.log_fetch_id_tracking(fetch_id)
        
        print(f"📊 Fetch #{fetch_number} | ID: {fetch_id}")
        
        footer_data = {
            "fetch_number": fetch_number,
            "random_fetch_id": fetch_id,
            "nyc_timestamp": nyc_timestamp,
            "pipeline_completion_time_seconds": round(pipeline_duration, 3) if pipeline_duration else None,
            "fetch_end": "=== RAW API DATA END ==="
        }
        
        # Add match statistics to footer
        if match_stats:
            footer_data["total_matches"] = match_stats["total_matches"]
            footer_data["matches_in_play"] = match_stats["matches_in_play"]
            footer_data["match_status_breakdown"] = match_stats["status_breakdown"]
        
        log_entry = {
            "FETCH_HEADER": {
                "fetch_number": fetch_number,
                "random_fetch_id": fetch_id,
                "nyc_timestamp": nyc_timestamp,
                "fetch_start": "=== RAW API DATA START ==="
            },
            "RAW_API_DATA": raw_data,
            "FETCH_FOOTER": footer_data
        }
        
        return log_entry, fetch_id, nyc_timestamp
    
    def write_to_local_file(self, log_entry, fetch_id, nyc_timestamp):
        """Write to local all_api.json file for pipeline"""
        current_fetch_count = self.count_current_fetches()
        
        # If this is the first fetch of a new cycle, overwrite the file
        if current_fetch_count == 0:
            mode = 'w'
            print(f"🔄 Starting new fetch cycle - overwriting all_api.json")
        else:
            mode = 'a'
            
        with open('all_api.json', mode) as f:
            fetch_number = log_entry.get('FETCH_HEADER', {}).get('fetch_number', 'unknown')
            f.write(f'=== FETCH START: #{fetch_number} | {fetch_id} | {nyc_timestamp} ===\n')
            json.dump(log_entry, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: #{fetch_number} | {fetch_id} | {nyc_timestamp} ===\n')
    
    def check_local_rotation(self):
        """Check if local rotation is needed (every 25 fetches)"""
        current_fetch_count = self.count_current_fetches()
        
        if current_fetch_count >= self.max_fetches:
            print(f"🔄 Local rotation triggered: {current_fetch_count} fetches reached")
            return True
        return False
    
    def perform_local_rotation(self):
        """Perform local file rotation - upload to S3 but KEEP local file for monitoring"""
        print(f"📤 Starting local rotation and S3 upload...")
        
        # Read current all_api.json content
        try:
            with open('all_api.json', 'r') as f:
                content = f.read().strip()
            
            if content:
                # Upload bookended format to S3
                self.upload_to_s3(content)
                
                # KEEP the local file for monitoring - DO NOT clear it
                fetch_count = content.count('=== FETCH START:')
                print(f"✅ Local rotation complete: all_api.json uploaded to S3 and kept for monitoring")
                print(f"📁 Local file preserved at: all_api.json ({fetch_count} fetches)")
            else:
                print(f"ℹ️ all_api.json was already empty")
                
        except Exception as e:
            print(f"❌ Error during local rotation: {e}")
    
    def reset_fetch_counter(self):
        """Reset fetch counter after rotation while keeping file for monitoring"""
        print(f"🔄 Resetting fetch counter - next 10 fetches will overwrite current file")
        # The file stays for monitoring, but next fetches will overwrite it
        pass
    
    def parse_bookended_format(self, content):
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
                    print(f"⚠️ Skipping malformed JSON in section {i}: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️ Error parsing section {i}: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ Error parsing bookended format: {e}")
        
        return parsed_entries
    
    def upload_to_s3(self, bookended_content):
        """Upload bookended format to S3 file"""
        if not self.s3_client:
            print("❌ S3 client not available - skipping upload")
            return False
        
        if not bookended_content:
            print("ℹ️ No data to upload to S3")
            return True
        
        # Check for new day and reset counters
        is_new_day = self.is_new_day()
        
        s3_key = self.get_daily_s3_key()
        timestamp = self.get_nyc_timestamp()
        
        try:
            print(f"📡 Uploading to daily file: {s3_key}")
            
            # Check if daily file exists
            daily_file_exists = False
            existing_content = ""
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                existing_content = response['Body'].read().decode('utf-8')
                daily_file_exists = True
                print(f"📄 Daily file exists - appending to it")
            except:
                daily_file_exists = False
                print(f"📄 Creating new daily file")
            
            # Prepare final content
            if daily_file_exists:
                # Append to existing file
                final_content = existing_content + "\n" + bookended_content
            else:
                # Create new file
                final_content = bookended_content
            
            # Count matches and fetches for reporting
            fetch_count = bookended_content.count('=== FETCH START:')
            match_count = bookended_content.count('"total_matches"')
            
            # Update daily counters
            self.daily_match_count += match_count
            self.daily_upload_count += 1
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=final_content,
                ContentType='text/plain',
                Metadata={
                    'upload-timestamp': timestamp,
                    'fetches-count': str(fetch_count)
                }
            )
            
            print(f"✅ S3 upload successful: s3://{self.bucket_name}/{s3_key}")
            print(f"📊 Upload #{self.daily_upload_count} for {self.current_date.strftime('%Y-%m-%d')}")
            print(f"🎯 Daily match count: {self.daily_match_count} total matches")
            print(f"📈 This upload: {match_count} matches, {fetch_count} fetches")
            
            return True
            
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
            return False
    
    def process_fetch_data(self, raw_data, pipeline_duration=None, match_stats=None):
        """Main method to process and log fetch data"""
        print(f"📝 Processing fetch data...")
        
        # Create log entry
        log_entry, fetch_id, nyc_timestamp = self.create_log_entry(raw_data, pipeline_duration, match_stats)
        
        # Write to local file for pipeline
        self.write_to_local_file(log_entry, fetch_id, nyc_timestamp)
        print(f"✅ Logged to local all_api.json: {fetch_id}")
        
        # Check if local rotation is needed
        if self.check_local_rotation():
            self.perform_local_rotation()
            # Clear the local file after S3 upload to start fresh cycle
            open('all_api.json', 'w').close()
            print(f"🔄 Local file cleared after S3 upload - starting fresh cycle for next 25 fetches")
        
        return True

def main():
    """Main execution - called by all_api.py as subprocess"""
    print("=" * 60)
    print("🚀 ALL_API COMPLETE LOGGER STARTED")
    print("=" * 60)
    
    try:
        # Read data from command line arguments (passed as JSON)
        if len(sys.argv) < 2:
            print("❌ Error: No data provided")
            print("Usage: python all_api_rotating_s3.py '<json_data>'")
            sys.exit(1)
        
        # Read JSON data from temporary file
        try:
            temp_file_path = sys.argv[1]
            with open(temp_file_path, 'r') as f:
                fetch_data = json.load(f)
            
            raw_data = fetch_data.get('raw_data')
            pipeline_duration = fetch_data.get('pipeline_duration')
            match_stats = fetch_data.get('match_stats')
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"❌ Error reading JSON data: {e}")
            sys.exit(1)
        
        # Initialize logger
        logger = AllApiCompleteLogger()
        
        # Process the fetch data
        success = logger.process_fetch_data(raw_data, pipeline_duration, match_stats)
        
        print("=" * 60)
        if success:
            print("✅ ALL_API LOGGING COMPLETED SUCCESSFULLY")
            print("=" * 60)
            sys.exit(0)
        else:
            print("❌ ALL_API LOGGING FAILED")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 CRITICAL ERROR in complete logger: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()