# Pipeline Log Rotation Fix: Single Fetch to 50-Fetch Accumulation

## Executive Summary

**PROBLEM**: All 7 pipeline stages reset fetch count to 1 on every execution due to `--single-run` subprocess pattern, preventing designed 50-fetch accumulation and rotation.

**SOLUTION**: Implement persistent state files to track fetch counts across process restarts while keeping existing architecture.

**PROOF OF ISSUE**: Files consistently show `fetch_number: 1` with identical timestamps per fetch cycle.

---

## Current State Analysis

### Root Cause
```bash
# all_api.py line 177 triggers subprocess chain:
subprocess.run([sys.executable, merge_script_path, '--single-run'])

# Each stage checks for --single-run and exits after one execution:
single_run_mode = '--single-run' in sys.argv
```

### Affected Files
1. `/root/Guaranteed_last_one/1_all_api/all_api.py` (triggers chain)
2. `/root/Guaranteed_last_one/3_merge/merge.py`
3. `/root/Guaranteed_last_one/4_pretty_print/pretty_print.py`
4. `/root/Guaranteed_last_one/5_pretty_print_conversion/pretty_print_conversion.py`
5. `/root/Guaranteed_last_one/6_monitor_central/monitor_central.py`
6. `/root/Guaranteed_last_one/7_alert_3ou_half/alert_3ou_half.py`
7. `/root/Guaranteed_last_one/8_alert_underdog_0half/alert_underdog_0half.py`

### Current Behavior Evidence
```json
// All JSON files show:
"fetch_number": 1,
"timestamp": "07/06/2025 08:25:56 PM EDT"  // Same across all matches

// Historical logs are empty due to same issue
```

---

## SOLUTION: Persistent State Architecture

### Option A: Persistent State Files (RECOMMENDED)

**Core Components:**
1. **Shared State Manager** - `PersistentStateManager` class
2. **State Files** - One per pipeline stage: `{stage}_fetch_state.json`
3. **Modified Loggers** - Load/save state on each execution

### Implementation Details

#### 1. Create Shared State Manager
**NEW FILE**: `/root/Guaranteed_last_one/shared_utils/persistent_state.py`

```python
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
```

#### 2. Modify Each Logger Class

**EXAMPLE - Monitor Central Changes:**

**CURRENT** `/root/Guaranteed_last_one/6_monitor_central/monitor_central.py`:
```python
class MonitorCentralLogger:
    def __init__(self, log_dir="monitor_central_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.fetch_count = 0              # ← RESETS TO 0 EVERY TIME
        self.accumulated_data = []        # ← RESETS TO [] EVERY TIME
        self.setup_logging()
```

**PROPOSED** `/root/Guaranteed_last_one/6_monitor_central/monitor_central.py`:
```python
import sys
sys.path.append('../shared_utils')
from persistent_state import PersistentStateManager

class MonitorCentralLogger:
    def __init__(self, log_dir="monitor_central_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.state_manager = PersistentStateManager("monitor_central", max_fetches)
        self.fetch_count, self.accumulated_data = self.state_manager.load_state()
        self.setup_logging()
    
    def log_fetch(self, monitor_data):
        """Pure catch-all pass-through logging with persistent state"""
        self.fetch_count += 1
        
        log_entry = monitor_data
        self.accumulated_data.append(log_entry)
        
        # Save state after each fetch
        self.state_manager.save_state(self.fetch_count, self.accumulated_data)
        
        # Write to main JSON file
        with open('monitor_central.json', 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Check for rotation
        if self.state_manager.should_rotate(self.fetch_count):
            self.rotate_log()
    
    def rotate_log(self):
        # Save to rotation log
        with open(self.log_path, 'w') as f:
            json.dump(self.accumulated_data, f, indent=2)
        
        # Reset state
        self.state_manager.reset_state()
        self.fetch_count = 0
        self.accumulated_data = []
```

#### 3. Apply Same Pattern to All 7 Files

**Files to Modify:**
- `3_merge/merge.py` - MergeLogger class
- `4_pretty_print/pretty_print.py` - PrettyPrintLogger class  
- `5_pretty_print_conversion/pretty_print_conversion.py` - PrettyPrintConversionLogger class
- `6_monitor_central/monitor_central.py` - MonitorCentralLogger class
- `7_alert_3ou_half/alert_3ou_half.py` - Alert3OUHalfLogger class
- `8_alert_underdog_0half/alert_underdog_0half.py` - AlertUnderdogLogger class

**Pattern**: Replace `self.fetch_count = 0` and `self.accumulated_data = []` with persistent state loading.

---

## EXACT CHANGES TO IMPLEMENT

### Step 1: Create Shared Utilities Directory
```bash
mkdir -p /root/Guaranteed_last_one/shared_utils
touch /root/Guaranteed_last_one/shared_utils/__init__.py
```

### Step 2: Create PersistentStateManager
**CREATE**: `/root/Guaranteed_last_one/shared_utils/persistent_state.py`
*(Full code provided above)*

### Step 3: Modify 6 Logger Files (NOT all_api.py)

#### 3.1 Monitor Central
**FILE**: `/root/Guaranteed_last_one/6_monitor_central/monitor_central.py`
**CHANGES**:
- **Line 21-25**: Replace initialization
- **Line 36-50**: Modify log_fetch method
- **Line 52-57**: Modify rotate_log method

#### 3.2 Merge Logger  
**FILE**: `/root/Guaranteed_last_one/3_merge/merge.py`
**CHANGES**:
- **Line 21-26**: Replace initialization  
- **Line 74-90**: Modify log_fetch method
- **Line 92-97**: Modify rotate_log method

#### 3.3 Pretty Print Logger
**FILE**: `/root/Guaranteed_last_one/4_pretty_print/pretty_print.py`
**CHANGES**:
- **Line ~20-25**: Replace initialization
- **Line ~60-75**: Modify log_fetch method  
- **Line ~77-82**: Modify rotate_log method

#### 3.4 Pretty Print Conversion Logger
**FILE**: `/root/Guaranteed_last_one/5_pretty_print_conversion/pretty_print_conversion.py`
**CHANGES**:
- **Line ~20-25**: Replace initialization
- **Line ~50-65**: Modify log_fetch method
- **Line ~67-72**: Modify rotate_log method

#### 3.5 Alert 3OU Half Logger
**FILE**: `/root/Guaranteed_last_one/7_alert_3ou_half/alert_3ou_half.py`
**CHANGES**:
- **Line ~20-25**: Replace initialization
- **Line ~60-75**: Modify log_fetch method  
- **Line ~77-82**: Modify rotate_log method

#### 3.6 Alert Underdog Logger  
**FILE**: `/root/Guaranteed_last_one/8_alert_underdog_0half/alert_underdog_0half.py`
**CHANGES**:
- **Line ~20-25**: Replace initialization
- **Line ~50-80**: Modify log_fetch method (special midnight rotation)
- **Line ~82-87**: Modify rotate_log method

---

## EXPECTED RESULTS AFTER IMPLEMENTATION

### Before Fix
```json
// Every JSON file shows:
{
  "HEADER": {
    "fetch_number": 1,  // ← Always 1
    "timestamp": "07/06/2025 08:25:56 PM EDT"
  }
}
```

### After Fix  
```json
// JSON files will show incremental progress:
{
  "HEADER": {
    "fetch_number": 23,  // ← Increments across fetches
    "timestamp": "07/06/2025 08:27:15 PM EDT"
  }
}

// At fetch 50, files will rotate and reset to 1
```

### Log Directory Results
```bash
# Before: Empty logs
monitor_central_log/monitor_central_log_20250702_155616.json  # 0 bytes

# After: Populated rotation logs every 50 fetches
monitor_central_log/monitor_central_log_20250707_142530.json  # 50 fetches worth
monitor_central_log/monitor_central_log_20250707_152845.json  # Next 50 fetches
```

---

## ROLLBACK INSTRUCTIONS (EMERGENCY REVERT)

### Complete Revert Procedure

If issues arise, follow these EXACT steps to restore original functionality:

#### Step 1: Remove Shared Utils
```bash
rm -rf /root/Guaranteed_last_one/shared_utils/
```

#### Step 2: Remove State Files
```bash
find /root/Guaranteed_last_one -name "*_fetch_state.json" -delete
```

#### Step 3: Restore Original Logger Classes

**FOR EACH MODIFIED FILE**, revert these changes:

**3_merge/merge.py**:
```python
# REVERT TO:
class MergeLogger:
    def __init__(self, log_dir="merge_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
```

**6_monitor_central/monitor_central.py**:
```python
# REVERT TO:
class MonitorCentralLogger:
    def __init__(self, log_dir="monitor_central_log", max_fetches=50):
        self.log_dir = log_dir
        self.max_fetches = max_fetches
        self.fetch_count = 0
        self.accumulated_data = []
        self.setup_logging()
```

**Repeat for all 6 logger files**, removing:
- `import sys; sys.path.append('../shared_utils')`
- `from persistent_state import PersistentStateManager`
- All `self.state_manager` references
- Persistent state loading/saving calls

#### Step 4: Verify Revert
```bash
# Check no state files remain
find /root/Guaranteed_last_one -name "*_fetch_state.json"

# Check no import references remain  
grep -r "persistent_state" /root/Guaranteed_last_one --exclude-dir=.git

# Should return no results
```

#### Step 5: Restart Pipeline
```bash
# Kill existing all_api process
pkill -f "all_api.py"

# Restart
cd /root/Guaranteed_last_one/1_all_api
nohup python3 all_api.py &
```

---

## IMPLEMENTATION CHECKLIST

### Pre-Implementation
- [ ] Backup current working directory
- [ ] Document current JSON fetch_number values
- [ ] Stop all pipeline processes

### Implementation
- [ ] Create shared_utils directory structure
- [ ] Create PersistentStateManager class
- [ ] Modify MergeLogger (3_merge/merge.py)  
- [ ] Modify PrettyPrintLogger (4_pretty_print/pretty_print.py)
- [ ] Modify PrettyPrintConversionLogger (5_pretty_print_conversion/pretty_print_conversion.py)
- [ ] Modify MonitorCentralLogger (6_monitor_central/monitor_central.py)
- [ ] Modify Alert3OUHalfLogger (7_alert_3ou_half/alert_3ou_half.py)
- [ ] Modify AlertUnderdogLogger (8_alert_underdog_0half/alert_underdog_0half.py)

### Testing
- [ ] Restart pipeline
- [ ] Verify fetch_number increments across fetches
- [ ] Wait for 50-fetch cycle to test rotation
- [ ] Confirm rotation logs are populated
- [ ] Verify fresh cycle starts at fetch_number: 1

### Validation Success Criteria
1. **JSON files show incremental fetch_number** (2, 3, 4... up to 50)
2. **Rotation occurs at fetch 50** with populated log files
3. **New cycle starts at fetch_number: 1** after rotation
4. **No performance degradation** in pipeline execution time
5. **All --single-run architecture preserved** (no daemon changes)

---

## RISK ASSESSMENT

### Low Risk
- **File system operations** - JSON read/write (already happening)
- **State management** - Simple counters and arrays
- **Architecture preservation** - No subprocess changes

### Medium Risk  
- **Initial state file creation** - Handle missing files gracefully
- **Concurrent access** - Threading locks implemented
- **Error handling** - Fallback to original behavior on state errors

### Mitigation
- **Gradual rollout** - Test one stage at a time
- **Error logging** - Comprehensive exception handling
- **Rollback ready** - Complete revert procedure documented
- **Monitoring** - Watch fetch_number progression in real-time

---

**READY FOR IMPLEMENTATION**: All changes specified, rollback procedure documented, success criteria defined.