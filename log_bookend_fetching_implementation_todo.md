# Bookend Fetching Implementation TODO Checklist

## Overview
This checklist shows exactly what needs to be done to implement fetch ID tracking with bookended processing for any pipeline file. Use this to implement the same system for pretty_print.py, pretty_print_conversion.py, monitor_central.py, and alert files.

## Prerequisites
- [ ] Verify all_api.py has header/footer markers implemented
- [ ] Verify all_api_fetch_id_tracking.json has pipeline stage fields
- [ ] Verify target file currently uses unreliable input method (lines[-1] or similar)

## Implementation Steps

### Step 1: Add Helper Functions to Target File
Add these 3 functions to the target file class (adjust file names and stage names):

#### Function 1: Find Unprocessed Fetch ID
```python
def find_unprocessed_fetch_id(self):
    """Find the next unprocessed fetch ID from tracking file"""
    tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
    
    try:
        with open(tracking_file, 'r') as f:
            content = f.read()
        
        # Split by closing brace to get individual entries
        entries = content.split('}\n{')
        
        unprocessed_entries = []
        for i, entry_str in enumerate(entries):
            # Fix JSON formatting for middle entries
            if i > 0:
                entry_str = '{' + entry_str
            if i < len(entries) - 1:
                entry_str = entry_str + '}'
            
            try:
                entry = json.loads(entry_str)
                if entry.get("STAGE_NAME.py") == "":  # ← CHANGE THIS
                    unprocessed_entries.append(entry)
            except json.JSONDecodeError:
                continue
        
        # Return the NEWEST unprocessed entry (last in the list)
        if unprocessed_entries:
            return unprocessed_entries[-1].get("fetch_id")
        
        return None  # Nothing to process
    except Exception as e:
        print(f"Error reading tracking file: {e}")
        return None
```

#### Function 2: Extract Fetch Data by ID
```python
def extract_fetch_data_by_id(self, fetch_id, input_file_path):
    """Extract complete fetch data between header and footer markers"""
    try:
        with open(input_file_path, 'r') as f:
            content = f.read()
        
        # Find start marker
        start_marker = f'=== FETCH START: {fetch_id} |'
        start_pos = content.find(start_marker)
        
        if start_pos == -1:
            return None
        
        # Find end marker
        end_marker = f'=== FETCH END: {fetch_id} |'
        end_pos = content.find(end_marker, start_pos)
        
        if end_pos == -1:
            return None
        
        # Extract JSON between markers
        fetch_section = content[start_pos:end_pos]
        json_start = fetch_section.find('\n{')
        json_end = fetch_section.rfind('\n}') + 2
        
        if json_start == -1 or json_end == -1:
            return None
        
        json_content = fetch_section[json_start:json_end]
        return json.loads(json_content)
        
    except Exception as e:
        print(f"Error extracting fetch data for {fetch_id}: {e}")
        return None
```

#### Function 3: Mark Fetch Completed
```python
def mark_fetch_completed(self, fetch_id):
    """Mark fetch as completed in tracking file"""
    tracking_file = '/root/Guaranteed_last_one/1_all_api/all_api_fetch_id_tracking.json'
    
    try:
        # Read all entries
        with open(tracking_file, 'r') as f:
            content = f.read()
        
        # Split by closing brace to get individual entries
        entries = content.split('}\n{')
        
        updated_entries = []
        for i, entry_str in enumerate(entries):
            # Fix JSON formatting for middle entries
            if i > 0:
                entry_str = '{' + entry_str
            if i < len(entries) - 1:
                entry_str = entry_str + '}'
            
            try:
                entry = json.loads(entry_str)
                if entry.get("fetch_id") == fetch_id:
                    entry["STAGE_NAME.py"] = "completed"  # ← CHANGE THIS
                updated_entries.append(json.dumps(entry, indent=2))
            except json.JSONDecodeError:
                continue
        
        # Write back updated entries
        with open(tracking_file, 'w') as f:
            f.write('\n'.join(updated_entries) + '\n')
            
    except Exception as e:
        print(f"Error marking fetch {fetch_id} as completed: {e}")
```

### Step 2: Replace Input Logic
Find the main processing function and replace the input logic:

#### Old Logic (DELETE THIS):
```python
# Example old logic patterns to replace:
with open(input_file_path, 'r') as f:
    lines = f.readlines()

# Get the latest data (last line)
if not lines:
    return {"error": "No valid data"}

try:
    latest_data = json.loads(lines[-1].strip())
except json.JSONDecodeError:
    return {"error": "Invalid JSON"}

# OR other patterns like:
data = json.load(f)
latest_data = data[-1]
```

#### New Logic (ADD THIS):
```python
# Find unprocessed fetch ID using new tracking system
fetch_id = self.find_unprocessed_fetch_id()
if not fetch_id:
    return {"error": "No unprocessed fetch IDs found"}

# Extract complete fetch data by ID
latest_data = self.extract_fetch_data_by_id(fetch_id, input_file_path)
if not latest_data:
    return {"error": f"Could not extract data for fetch ID: {fetch_id}"}

# Continue with existing processing logic...
```

### Step 3: Add Completion Marking
Find where the main processing function completes and add completion marking:

#### Add Before Return Statement:
```python
# Mark fetch as completed in tracking file
self.mark_fetch_completed(fetch_id)

# Rest of existing logic (triggers, returns, etc.)
```

### Step 4: Update Stage-Specific Details
For each file, customize these elements:

#### For pretty_print.py:
- [ ] Change `"STAGE_NAME.py"` to `"pretty_print.py"`
- [ ] Input file: `/root/Guaranteed_last_one/3_merge/merge.json`
- [ ] Output file: `/root/Guaranteed_last_one/4_pretty_print/pretty_print.json`

#### For pretty_print_conversion.py:
- [ ] Change `"STAGE_NAME.py"` to `"pretty_print_conversion.py"`
- [ ] Input file: `/root/Guaranteed_last_one/4_pretty_print/pretty_print.json`
- [ ] Output file: `/root/Guaranteed_last_one/5_pretty_print_conversion/pretty_print_conversion.json`

#### For monitor_central.py:
- [ ] Change `"STAGE_NAME.py"` to `"monitor_central.py"`
- [ ] Input file: `/root/Guaranteed_last_one/5_pretty_print_conversion/pretty_print_conversion.json`
- [ ] Output file: `/root/Guaranteed_last_one/6_monitor_central/monitor_central.json`

#### For alert_3ou_half.py:
- [ ] Change `"STAGE_NAME.py"` to `"alert_3ou_half.py"`
- [ ] Input file: `/root/Guaranteed_last_one/6_monitor_central/monitor_central.json`
- [ ] Output file: `/root/Guaranteed_last_one/7_alert_3ou_half/alert_3ou_half.json`

#### For alert_underdog_0half.py:
- [ ] Change `"STAGE_NAME.py"` to `"alert_underdog_0half.py"`
- [ ] Input file: `/root/Guaranteed_last_one/6_monitor_central/monitor_central.json`
- [ ] Output file: `/root/Guaranteed_last_one/7_alert_underdog_0half/alert_underdog_0half.json`

## Testing Checklist

### Before Implementation:
- [ ] Backup the target file
- [ ] Verify tracking file has correct stage field
- [ ] Test helper functions individually

### After Implementation:
- [ ] Run single test: `python3 target_file.py --single-run`
- [ ] Verify tracking file shows `"STAGE_NAME.py": "completed"`
- [ ] Verify output file gets new entries
- [ ] Check for any error messages
- [ ] Verify downstream stages still work

### Verification Steps:
1. [ ] Check that newest unprocessed fetch ID is found
2. [ ] Verify correct data extraction from input file
3. [ ] Confirm processing logic works unchanged
4. [ ] Verify completion marking updates tracking file
5. [ ] Test error handling for missing/corrupted data

## Common Issues & Solutions

### Issue 1: JSON Parsing Errors
**Problem**: `Expecting property name enclosed in double quotes`
**Solution**: Verify the tracking file format and adjust the parsing logic

### Issue 2: Fetch ID Not Found
**Problem**: `Could not extract data for fetch ID`
**Solution**: Check if the header/footer markers exist in the input file

### Issue 3: No Unprocessed Fetch IDs
**Problem**: `No unprocessed fetch IDs found`
**Solution**: Verify the tracking file has entries where the stage field is empty

### Issue 4: Processing Logic Broken
**Problem**: Existing processing doesn't work with new input
**Solution**: Verify the extracted data format matches what the processing logic expects

## Files Modified Per Implementation

### For Each Pipeline Stage:
- [ ] Add 3 helper functions to the stage file
- [ ] Replace input logic in main processing function
- [ ] Add completion marking before return/trigger
- [ ] Update stage-specific field names and file paths

### Tracking File Updates:
- [ ] No changes needed - tracking file is shared across all stages
- [ ] Each stage will update its own field to "completed"

## Documentation Updates

### After Each Implementation:
- [ ] Update the main documentation with new stage
- [ ] Add stage-specific notes about processing logic
- [ ] Document any unique requirements for that stage
- [ ] Update rollback instructions if needed

## Implementation Order Recommendation

### Sequential Implementation:
1. [ ] **pretty_print.py** - Processes merge.json output
2. [ ] **pretty_print_conversion.py** - Processes pretty_print.json output  
3. [ ] **monitor_central.py** - Processes conversion output
4. [ ] **alert_3ou_half.py** - Processes monitor output
5. [ ] **alert_underdog_0half.py** - Processes monitor output

### Why This Order:
- **Sequential dependencies** - Each stage depends on the previous one
- **Easier debugging** - Issues can be isolated to specific stages
- **Incremental testing** - Can verify each stage works before moving to next

## Final Verification

### Complete Pipeline Test:
- [ ] Run all_api.py to generate new fetch ID
- [ ] Verify each stage processes the fetch ID in sequence
- [ ] Check that tracking file shows "completed" for all stages
- [ ] Verify final output files contain processed data
- [ ] Confirm no duplicate processing occurs

### Performance Verification:
- [ ] Check processing times are reasonable
- [ ] Verify memory usage doesn't increase significantly
- [ ] Confirm file I/O operations are efficient
- [ ] Test with multiple concurrent fetch IDs

## Rollback Plan

### If Implementation Fails:
1. [ ] Restore original file from backup
2. [ ] Remove any temporary files created
3. [ ] Verify original functionality works
4. [ ] Document what went wrong for future reference

### Rollback Verification:
- [ ] Original input logic works (lines[-1] or similar)
- [ ] Processing logic functions correctly
- [ ] Output files are generated properly
- [ ] No references to fetch ID tracking remain

## Success Criteria

### Implementation is Complete When:
- [ ] All helper functions added and working
- [ ] Input logic replaced with fetch ID tracking
- [ ] Completion marking updates tracking file correctly
- [ ] All existing functionality preserved
- [ ] Error handling works gracefully
- [ ] Documentation updated
- [ ] Testing completed successfully

This checklist ensures consistent implementation across all pipeline stages while maintaining the existing functionality and adding reliable fetch ID tracking.