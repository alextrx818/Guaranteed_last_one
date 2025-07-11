# S3 Logging System: Common Bugs & Solutions

## Implementation Summary for merge.py S3 Logging

### 1. **Initial Setup (Following all_api.py Pattern)**
- **What we did:** Simplified MergeLogger from 104 lines to 20 lines, delegating to external `merge_rotating_s3.py`
- **Pattern:** Temp file → subprocess call → external script handles all S3 logic
- **Files created:**
  - `merge_rotating_s3.py` (external S3 handler)
  - `merge_rotation_state.json` (local rotation persistence)

### 2. **Problems Encountered & Fixes**

#### **Problem 1: Fetch ID/Number Generation Conflict**
- **Issue:** merge_rotating_s3.py was generating its own fetch IDs instead of using all_api's
- **User feedback:** *"fetch counter mechanism should live in all_api.py and should just pass down"*
- **Fix:** Made merge extract fetch info from `SOURCE_ALL_API_HEADER` (read-only)
```python
# EXTRACT fetch info from all_api data (READ-ONLY)
source_header = merged_data.get("SOURCE_ALL_API_HEADER", {})
fetch_number = source_header.get("fetch_number", "unknown")
fetch_id = source_header.get("random_fetch_id", "unknown")
```

#### **Problem 2: Bookend Format Parsing**
- **Issue:** merge.py couldn't parse new bookend format with fetch numbers
- **Error:** `extract_fetch_data_by_id()` expected old format vs new format
- **Fix:** Updated parsing to handle: `=== FETCH START: #17 | P7FuiKA0u18B | timestamp ===`
```python
# Updated from:
start_marker = f'=== FETCH START: {fetch_id} |'
# To:
start_marker = f'| {fetch_id} |'  # Match "| P7FuiKA0u18B |" pattern
```

#### **Problem 3: Rotation Count Not Persisting**
- **Issue:** Rotation count stuck at (1/10) because script was instantiated fresh each time
- **User feedback:** *"rotation count should be two separate things right./ not related."*
- **Fix:** Added rotation state persistence separate from daily fetch count
```python
def save_rotation_state(self):
    state = {'local_fetch_count': self.local_fetch_count}
    with open('merge_rotation_state.json', 'w') as f:
        json.dump(state, f)
```

#### **Problem 4: S3 Upload Not Triggering**
- **Issue:** Rotation reached 13/10, 14/10 but S3 upload never happened
- **Root cause:** `self.current_date` was None causing `strftime()` error
- **Fix:** Properly initialize current_date in `__init__`
```python
# Initialize current date
nyc_tz = pytz.timezone('America/New_York')
self.current_date = datetime.now(nyc_tz).date()
```

#### **Problem 5: Wrong S3 Credentials**
- **Issue:** Used different credentials than working all_api.py
- **Error:** `InvalidAccessKeyId` and connection timeouts
- **Fix:** Updated to match all_api.py credentials (Chicago region)
```python
# From: us-east-1.linodeobjects.com with invalid keys
# To: us-ord-1.linodeobjects.com with working keys
```

#### **Problem 6: Daily vs Rotation Counter Confusion**
- **Issue:** Mixed up daily fetch numbering with local rotation counting
- **User clarification:** *"fetch count and log rotate count are two separate things"*
- **Fix:** 
  - Daily fetch count: Continuous (#1, #2, #3... until midnight)
  - Rotation count: Local (1/10, 2/10... resets after S3 upload)

### 3. **Key Principles Established**

#### **Hard Rules:**
1. **Bookends are sacred** - Pass through unchanged, never modify
2. **Fetch ID/number generated only in all_api.py** - Other stages extract (read-only)
3. **Separate daily count from rotation count** - Two different purposes
4. **External script delegation** - Main file stays simple, external handles S3
5. **State persistence** - Rotation count must survive script restarts

#### **Architecture Pattern:**
```
merge.py (20 lines) → temp file → merge_rotating_s3.py (handles everything)
                                         ↓
                                   - S3 upload logic
                                   - Local rotation management  
                                   - Daily file creation
                                   - State persistence
```

### 4. **Final Working System**
- ✅ **10-fetch rotation** (configurable)
- ✅ **Daily file creation** (`merge_json_log_2025-07-11.json`)
- ✅ **Proper S3 upload** to `sports-json-logs-all/merge_rotating_logs/`
- ✅ **Local rotation reset** after successful upload
- ✅ **Fetch info extraction** from all_api data
- ✅ **Bookend preservation** in local files
- ✅ **State persistence** across script restarts

### 5. **For Next File Implementation**
Use this checklist to avoid the same issues:
1. **Copy working S3 credentials** from all_api.py
2. **Initialize `current_date`** properly in `__init__`
3. **Extract fetch info** from upstream data (don't generate new)
4. **Separate rotation state** from daily counters
5. **Add state persistence** for rotation count
6. **Test S3 connection** before deploying
7. **Preserve bookend format** from upstream stage
8. **Use temp file delegation** pattern for clean architecture

This systematic approach should work for any pipeline stage going forward.

---

## Common S3 Logging Bugs Reference

### Bug: Rotation Count Stuck at 1/X
**Symptoms:** Always shows (1/10) instead of incrementing
**Cause:** No state persistence between script executions
**Solution:** Add rotation state JSON file with load/save methods

### Bug: S3 Upload Never Triggers
**Symptoms:** Rotation count exceeds limit (13/10, 14/10) but no upload
**Cause:** `self.current_date` is None, causing strftime() error
**Solution:** Initialize current_date in __init__ method

### Bug: Wrong Fetch ID/Numbers
**Symptoms:** Each stage generates different fetch IDs
**Cause:** Each stage creating its own IDs instead of passing through
**Solution:** Extract from upstream data, never generate new

### Bug: Bookend Format Mismatch
**Symptoms:** Can't parse bookends between pipeline stages
**Cause:** Format changes between stages
**Solution:** Maintain consistent format, update parsing logic

### Bug: Invalid S3 Credentials
**Symptoms:** InvalidAccessKeyId or connection timeouts
**Cause:** Different credentials than working stages
**Solution:** Copy exact credentials from working stage

### Bug: Daily vs Rotation Counter Mix-up
**Symptoms:** Counters reset when they shouldn't or don't reset when they should
**Cause:** Using same counter for different purposes
**Solution:** Separate daily continuous count from local rotation count