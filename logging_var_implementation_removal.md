# VAR Incident Logger Implementation & Removal Guide

## Overview
This document explains the minimal VAR incident logging system that was implemented to track Video Assistant Referee (VAR) incidents from the sports betting pipeline.

## What Was Implemented

### 1. New File: `all_api_var_logger.py`
**Location**: `/root/Guaranteed_last_one/1_all_api/all_api_var_logger.py`

**Purpose**: Standalone VAR incident logger that processes the most recent `all_api.json` fetch and logs any VAR incidents (type 28) with timestamps.

**Key Features**:
- Reads the most recent fetch from `all_api.json`
- Filters for incident type 28 (VAR incidents)
- Logs incidents with NYC timestamps
- Creates/appends to `var_incidents.json` file
- Includes match ID, incident data, and fetch timestamps
- Handles errors gracefully without breaking the pipeline

### 2. Modified File: `all_api.py`
**Location**: `/root/Guaranteed_last_one/1_all_api/all_api.py`
**Line Modified**: Lines 185-189

**Code Added**:
```python
# Trigger VAR incident logger
try:
    subprocess.run([sys.executable, 'all_api_var_logger.py'], cwd=os.path.dirname(__file__), check=False)
except Exception as e:
    print(f"Warning: Could not trigger VAR logger: {e}")
```

**Integration Point**: Added in the `trigger_merge()` method, right after the merge process trigger.

### 3. Output File: `all_api_var_logger.json`
**Location**: `/root/Guaranteed_last_one/1_all_api/all_api_var_logger.json`
**Purpose**: Accumulates all VAR incidents found across all fetches with timestamps

## How It Works

1. **Trigger**: Every time `all_api.py` completes a fetch, it triggers the VAR logger
2. **Processing**: VAR logger reads the most recent fetch from `all_api.json`
3. **Filtering**: Extracts all incidents with `type == 28` (VAR incidents)
4. **Logging**: Appends found VAR incidents to `all_api_var_logger.json` with timestamps
5. **Error Handling**: Continues pipeline operation even if VAR logger fails

## Sample Output Format

```json
[
  {
    "timestamp_logged": "07/08/2025 01:00:00 PM EDT",
    "match_id": "y0or5jhnv48wqwz",
    "incident_type": 28,
    "incident_data": {
      "type": 28,
      "time": 21,
      "player_id": "player123",
      "description": "VAR Review"
    },
    "fetch_timestamp": "07/08/2025 12:59:45 PM EDT"
  }
]
```

## Complete Removal Instructions

If you need to remove this VAR logging system completely:

### Step 1: Remove the VAR Logger File
```bash
rm /root/Guaranteed_last_one/1_all_api/all_api_var_logger.py
```

### Step 2: Remove the VAR Log Output File
```bash
rm /root/Guaranteed_last_one/1_all_api/all_api_var_logger.json
```

### Step 3: Remove the Code from all_api.py
**File**: `/root/Guaranteed_last_one/1_all_api/all_api.py`
**Lines to Remove**: Lines 185-189

Remove this block:
```python
# Trigger VAR incident logger
try:
    subprocess.run([sys.executable, 'all_api_var_logger.py'], cwd=os.path.dirname(__file__), check=False)
except Exception as e:
    print(f"Warning: Could not trigger VAR logger: {e}")
```

### Step 4: Verify Removal
After removal, the `trigger_merge()` method should look like this:
```python
except Exception as e:
    print(f"Warning: Could not trigger merge process: {e}")
    # Continue normal operation even if merge fails

def analyze_match_stats(self, all_data):
    """Analyze match statistics from live data"""
```

## Why This Implementation is Minimal

1. **Single File Addition**: Only one new file (`all_api_var_logger.py`)
2. **Minimal Code Change**: Only 5 lines added to existing code
3. **No Dependencies**: Uses existing libraries (json, os, datetime, pytz)
4. **No Pipeline Impact**: Fails gracefully without breaking the main pipeline
5. **Easy Removal**: Complete removal requires only 3 simple steps
6. **Self-Contained**: VAR logger operates independently of other pipeline stages

## Testing the Implementation

To verify the VAR logger is working:

1. **Check for VAR logger execution**: Look for `[VAR Logger]` messages in console output
2. **Verify output file**: Check if `all_api_var_logger.json` is created in the `1_all_api` directory
3. **Monitor VAR incidents**: Watch for VAR incidents being logged during live matches
4. **Check error handling**: VAR logger should not crash the main pipeline if it fails

## Notes

- The VAR logger only processes the most recent fetch from `all_api.json`
- It accumulates all VAR incidents in a persistent log file
- Uses NYC timezone for consistent timestamping
- Designed to be completely removable without affecting the main pipeline functionality