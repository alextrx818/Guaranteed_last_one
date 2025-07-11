# Linode S3 Bucket Logging System - Standard Operating Procedure
**Document Created**: July 10, 2025  
**System**: Sports Betting Data Pipeline Logging  
**Purpose**: Comprehensive roadmap for implementing S3-based logging with daily rotation and match counting

---

## EXECUTIVE SUMMARY

This document provides a complete roadmap for implementing a standardized logging system that uploads data to Linode Object Storage with daily file rotation, 10-fetch local rotation, and accurate daily match counting. The system is designed for production use with zero-maintenance operation and complete data retention.

---

## SYSTEM OVERVIEW

### Core Components:
1. **Local Logging**: 10 fetches accumulate in `all_api.json` (visible in VS Code)
2. **S3 Upload System**: Every 10 fetches upload to Linode Object Storage
3. **Daily File Rotation**: One S3 file per day with automatic midnight rotation
4. **Match Counting**: Accurate daily match counter that resets at midnight
5. **Duplicate Prevention**: File existence checks prevent duplicate daily files

### Data Flow:
```
API Fetch → all_api.json (local, 10 fetches) → S3 Upload → Daily File Append → Match Counter Update
```

---

## PREREQUISITES

### 1. Linode Object Storage Setup
- **Account**: Active Linode account with Object Storage enabled
- **Bucket**: Created and accessible
- **Access Keys**: Generated with appropriate permissions

### 2. Required Information
- **Bucket Name**: `sports-json-logs-all`
- **Region**: `us-ord-1` (Chicago)
- **Endpoint**: `https://us-ord-1.linodeobjects.com`
- **Access Key**: Your generated access key
- **Secret Key**: Your generated secret key
- **Folder Structure**: `all_api_rotating_logs/` (auto-created)

### 3. Python Dependencies
```bash
pip install boto3 pytz
```

---

## IMPLEMENTATION ROADMAP

### Phase 1: Linode Credentials Configuration

#### Step 1.1: Obtain Linode Object Storage Credentials
1. Log into [cloud.linode.com](https://cloud.linode.com)
2. Navigate to **Object Storage** in left sidebar
3. Click **Access Keys** tab
4. Click **Create Access Key**
5. Set label: "Sports JSON Logs Access"
6. Choose access level:
   - **Limited Access**: Select your specific bucket
   - **Full Access**: For testing simplicity
7. Click **Create Access Key**
8. **CRITICAL**: Save both Access Key and Secret Key immediately
9. Note the bucket endpoint URL

#### Step 1.2: Verify Bucket Configuration
1. Confirm bucket name: `sports-json-logs-all`
2. Confirm region: `us-ord-1` (Chicago)
3. Confirm endpoint: `https://us-ord-1.linodeobjects.com`
4. Test bucket accessibility via Linode web interface

### Phase 2: Script Configuration

#### Step 2.1: Update all_api_rotating_s3.py
```python
# Update these configuration values:
bucket_name = "sports-json-logs-all"
endpoint_url = "https://us-ord-1.linodeobjects.com"
aws_access_key_id = "YOUR_ACCESS_KEY"
aws_secret_access_key = "YOUR_SECRET_KEY"
region_name = "us-ord-1"
folder_name = "all_api_rotating_logs"
max_fetches = 10
```

#### Step 2.2: Add Required Functionality
1. **Connection Testing**: Verify S3 credentials and access
2. **File Existence Checking**: Prevent duplicate daily files
3. **Daily Match Counting**: Track matches per day with midnight reset
4. **Midnight Detection**: Automatic new file creation at midnight EST
5. **Duplicate Prevention**: Robust checks for existing files
6. **Error Handling**: Comprehensive error recovery

### Phase 3: Core System Implementation

#### Step 3.1: Local File Management
- **Purpose**: Allow inspection of 10 fetches before rotation
- **Location**: `/root/Guaranteed_last_one/1_all_api/all_api.json`
- **Access**: Open in VS Code to inspect accumulated fetches
- **Behavior**: Grows to 10 fetches, then cleared after S3 upload

#### Step 3.2: S3 Upload Logic
- **Trigger**: Every 10 fetches accumulated locally
- **Process**: Read local file → Parse JSON → Upload to S3 → Clear local file
- **Target**: Daily file in S3 bucket
- **Append Mode**: Multiple uploads per day append to same file

#### Step 3.3: Daily File Rotation
- **File Naming**: `all_api_json_log_YYYY-MM-DD.json`
- **Examples**: 
  - `all_api_json_log_2025-07-10.json`
  - `all_api_json_log_2025-07-11.json`
- **Creation**: One file per day, no duplicates
- **Timezone**: EST/EDT (America/New_York)
- **Midnight Detection**: Automatic new file at 12:00 AM EST

#### Step 3.4: Match Counting System
- **Purpose**: Track total matches processed per day
- **Reset**: Every midnight EST (new day = count starts at 1)
- **Accuracy**: Counts actual matches from API data
- **Storage**: Included in S3 file metadata
- **Display**: Shown in logs and file headers

---

## DETAILED TECHNICAL SPECIFICATIONS

### File Structure in S3
```
sports-json-logs-all/
└── all_api_rotating_logs/
    ├── all_api_json_log_2025-07-10.json
    ├── all_api_json_log_2025-07-11.json
    ├── all_api_json_log_2025-07-12.json
    └── ...
```

### Daily File Content Structure
```json
{
  "daily_metadata": {
    "date": "2025-07-10",
    "total_uploads": 24,
    "total_matches_today": 1440,
    "first_upload": "07/10/2025 12:01:00 AM EDT",
    "last_upload": "07/10/2025 11:59:45 PM EDT"
  },
  "uploads": [
    {
      "upload_sequence": 1,
      "upload_timestamp": "07/10/2025 12:01:00 AM EDT",
      "matches_in_upload": 60,
      "fetch_data": [
        { "FETCH_HEADER": {...}, "RAW_API_DATA": {...}, "FETCH_FOOTER": {...} },
        { "FETCH_HEADER": {...}, "RAW_API_DATA": {...}, "FETCH_FOOTER": {...} },
        ...10 fetches...
      ]
    },
    {
      "upload_sequence": 2,
      "upload_timestamp": "07/10/2025 12:11:00 AM EDT",
      "matches_in_upload": 58,
      "fetch_data": [...]
    }
    ...continues for entire day...
  ]
}
```

### Match Counting Logic
```python
def count_matches_in_upload(self, fetch_data):
    """Count total matches across all fetches in upload"""
    total_matches = 0
    for fetch in fetch_data:
        if "FETCH_FOOTER" in fetch:
            total_matches += fetch["FETCH_FOOTER"].get("total_matches", 0)
    return total_matches

def update_daily_match_count(self, new_matches):
    """Update running daily match count"""
    self.daily_match_count += new_matches
    return self.daily_match_count
```

### Midnight Detection Logic
```python
def is_new_day(self):
    """Detect midnight crossover in EST timezone"""
    nyc_tz = pytz.timezone('America/New_York')
    current_date = datetime.now(nyc_tz).date()
    
    if self.current_date is None:
        self.current_date = current_date
        return False
    
    if current_date > self.current_date:
        self.current_date = current_date
        self.daily_match_count = 0  # Reset counter
        return True
    
    return False
```

### File Existence Check
```python
def check_daily_file_exists(self, s3_key):
    """Prevent duplicate daily file creation"""
    try:
        self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
        return True  # File exists
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return False  # File doesn't exist, safe to create
        else:
            raise e  # Handle other errors
```

---

## OPERATION PROCEDURES

### Daily Operation Flow

#### Startup (First Run of Day):
1. **Initialize**: Load previous state (if any)
2. **Date Check**: Determine current date in EST
3. **File Check**: Verify if today's S3 file exists
4. **Counter Reset**: If new day, reset match counter to 0
5. **Ready State**: System ready for first 10-fetch cycle

#### Normal Operation (Every 10 Fetches):
1. **Local Accumulation**: 10 fetches accumulate in `all_api.json`
2. **Rotation Trigger**: 10th fetch triggers upload process
3. **File Read**: Read and parse `all_api.json` content
4. **Match Counting**: Count matches in current upload
5. **S3 Upload**: Append to today's daily file
6. **Local Clear**: Clear `all_api.json` for next cycle
7. **Counter Update**: Update daily match count

#### Midnight Transition:
1. **Date Detection**: System detects new day at midnight EST
2. **New File**: Next upload creates new daily file
3. **Counter Reset**: Daily match count resets to 0
4. **Continuation**: Normal 10-fetch cycles resume

### Error Handling Procedures

#### S3 Connection Failures:
- **Action**: Log error, continue local accumulation
- **Recovery**: Retry on next rotation cycle
- **Fallback**: Local files preserved for manual recovery

#### File Upload Failures:
- **Action**: Preserve local data, log detailed error
- **Recovery**: Automatic retry on next cycle
- **Escalation**: Multiple failures trigger warning logs

#### Duplicate File Detection:
- **Action**: Append to existing file (normal behavior)
- **Verification**: Confirm file content integrity
- **Logging**: Record successful append operation

---

## MONITORING AND MAINTENANCE

### Key Metrics to Monitor
1. **Upload Success Rate**: Percentage of successful S3 uploads
2. **Daily File Count**: Should be exactly 1 per day
3. **Match Count Accuracy**: Verify counts match expected volumes
4. **File Size Growth**: Monitor daily file sizes for anomalies
5. **Error Frequency**: Track and investigate recurring errors

### Log Files to Check
- **Console Output**: Real-time operation status
- **Error Logs**: S3 upload failures and connection issues
- **Match Count Logs**: Daily counter values and resets
- **File Creation Logs**: New daily file creation events

### Maintenance Tasks
- **Weekly**: Verify S3 bucket organization and file integrity
- **Monthly**: Review daily file sizes and match count trends
- **Quarterly**: Test disaster recovery and backup procedures
- **Annually**: Review and update access credentials

---

## DISASTER RECOVERY

### Backup Procedures
1. **Local Backup**: Keep local copies of recent rotations
2. **S3 Versioning**: Enable S3 object versioning if needed
3. **Cross-Region**: Consider cross-region replication for critical data
4. **Export Capability**: Ability to download and restore S3 data

### Recovery Scenarios

#### Lost S3 Connection:
1. **Immediate**: Local files continue accumulating
2. **Recovery**: Restore connection and bulk upload accumulated data
3. **Verification**: Confirm all data uploaded correctly

#### Corrupted Daily File:
1. **Detection**: File integrity checks during upload
2. **Recovery**: Restore from local accumulated data
3. **Prevention**: Implement file versioning

#### Complete System Failure:
1. **Local Data**: Recover from `all_api.json` and recent logs
2. **S3 Data**: Download recent daily files for reconstruction
3. **Counter Recovery**: Recalculate match counts from recovered data

---

## TESTING PROCEDURES

### Pre-Deployment Testing

#### Unit Tests:
1. **Connection Test**: Verify S3 credentials and bucket access
2. **Upload Test**: Test file upload and download operations
3. **Rotation Test**: Verify 10-fetch rotation behavior
4. **Counter Test**: Verify match counting accuracy
5. **Midnight Test**: Test new day detection and file creation

#### Integration Tests:
1. **Full Cycle Test**: Complete 10-fetch to S3 upload cycle
2. **Daily Transition Test**: Test midnight crossover behavior
3. **Error Recovery Test**: Test handling of various error conditions
4. **Duplicate Prevention Test**: Verify no duplicate files created

#### Load Tests:
1. **High Volume Test**: Test with large numbers of fetches
2. **Extended Operation Test**: 24-hour continuous operation
3. **Multiple Day Test**: Test operation across multiple day boundaries

### Production Validation

#### Daily Checks:
- Verify new daily file created at midnight
- Confirm match counts are reasonable
- Check for any error messages in logs

#### Weekly Checks:
- Review S3 bucket organization
- Verify file sizes are growing appropriately
- Confirm no duplicate daily files exist

---

## TROUBLESHOOTING GUIDE

### Common Issues and Solutions

#### "NoSuchBucket" Error:
- **Cause**: Incorrect bucket name or region
- **Solution**: Verify bucket name and endpoint URL
- **Check**: Confirm bucket exists in Linode console

#### "AccessDenied" Error:
- **Cause**: Invalid credentials or insufficient permissions
- **Solution**: Regenerate access keys with proper permissions
- **Check**: Test credentials with connection test script

#### "NoSuchKey" on Existing File:
- **Cause**: File path or naming issue
- **Solution**: Verify folder structure and file naming convention
- **Check**: Browse S3 bucket to confirm file locations

#### Match Count Discrepancies:
- **Cause**: Parsing errors or missing data
- **Solution**: Review match counting logic and data structure
- **Check**: Manually verify counts against raw data

#### Midnight Transition Issues:
- **Cause**: Timezone configuration or date detection logic
- **Solution**: Verify pytz timezone settings and date comparison
- **Check**: Test midnight transition with manual date changes

---

## PERFORMANCE OPTIMIZATION

### Efficiency Improvements
1. **Batch Operations**: Group multiple operations where possible
2. **Connection Pooling**: Reuse S3 connections across uploads
3. **Compression**: Consider compressing large daily files
4. **Indexing**: Add metadata for faster file searches

### Scalability Considerations
1. **File Size Limits**: Monitor daily file sizes, implement splitting if needed
2. **Upload Frequency**: Adjust 10-fetch limit based on data volume
3. **Storage Costs**: Monitor S3 storage costs and implement lifecycle policies
4. **Network Bandwidth**: Consider upload timing to minimize impact

---

## SECURITY CONSIDERATIONS

### Access Control
1. **Credential Storage**: Store access keys securely (environment variables)
2. **Minimum Permissions**: Grant least-privilege access to S3 resources
3. **Regular Rotation**: Rotate access keys quarterly
4. **Audit Logging**: Enable S3 access logging for security monitoring

### Data Protection
1. **Encryption**: Use S3 server-side encryption for stored data
2. **Network Security**: Ensure HTTPS for all S3 communications
3. **Data Classification**: Classify and handle data according to sensitivity
4. **Retention Policies**: Implement appropriate data retention schedules

---

## COST MANAGEMENT

### S3 Storage Costs
- **Monitor**: Daily file sizes and growth trends
- **Optimize**: Implement lifecycle policies for old data
- **Budget**: Set up billing alerts for unexpected cost increases
- **Archive**: Move old data to cheaper storage classes

### Network Costs
- **Upload Timing**: Consider off-peak upload times if applicable
- **Compression**: Implement compression to reduce transfer volumes
- **Regional**: Ensure bucket region matches compute region

---

## FUTURE ENHANCEMENTS

### Potential Improvements
1. **Multi-Bucket Support**: Support multiple buckets for different data types
2. **Advanced Analytics**: Add built-in data analysis capabilities
3. **Real-Time Monitoring**: Implement real-time monitoring dashboard
4. **Automated Alerting**: Set up automated alerts for system issues
5. **Data Validation**: Add comprehensive data validation before upload

### Integration Opportunities
1. **Business Intelligence**: Connect to BI tools for data analysis
2. **Machine Learning**: Prepare data for ML model training
3. **Real-Time Processing**: Integration with stream processing systems
4. **Notification Systems**: Enhanced alerting and notification capabilities

---

## CONCLUSION

This comprehensive logging system provides:
- **Reliable Data Storage**: All data safely stored in Linode Object Storage
- **Operational Simplicity**: Automated daily rotation and match counting
- **Developer Friendly**: Local file access for development and debugging
- **Production Ready**: Comprehensive error handling and monitoring
- **Cost Effective**: Efficient storage with daily organization
- **Scalable Architecture**: Designed to handle growing data volumes

The system is designed for zero-maintenance operation while providing complete visibility into the data pipeline operations. Following this roadmap ensures successful implementation and long-term operational success.

---

**Document Version**: 1.0  
**Last Updated**: July 10, 2025  
**Status**: Ready for Implementation