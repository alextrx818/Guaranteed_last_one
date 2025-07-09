# 🎨 Pretty JSON Implementation Plan - Human-Readable Format

## 📋 Overview

This implementation maintains all the benefits of the clean code refactor while keeping JSON files beautiful and human-readable. We get rid of the ugly bookended format but keep pretty printing.

## 🔧 Implementation Details

### 1. **NEW FILE: `/root/Guaranteed_last_one/shared_utils/fetch_data_reader.py`**

```python
# CREATE NEW FILE: shared_utils/fetch_data_reader.py
import json
import os
from typing import Optional, Dict, Any, List
import fcntl  # For file locking

class FetchDataReader:
    """Universal reader/writer for fetch data - handles both old and new formats"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.format_type = self._detect_format()
        
    def _detect_format(self) -> str:
        """Detect if file uses bookended or pretty JSON array format"""
        if not os.path.exists(self.file_path):
            return 'new_file'
            
        try:
            with open(self.file_path, 'r') as f:
                first_char = f.read(1)
                if not first_char:
                    return 'new_file'
                    
                f.seek(0)
                first_line = f.readline().strip()
                
                if first_line.startswith('=== FETCH START:'):
                    return 'bookended'
                elif first_char == '[':
                    return 'json_array'
                else:
                    return 'unknown'
        except Exception:
            return 'new_file'
    
    def read_all(self) -> List[Dict[str, Any]]:
        """Read all entries from file"""
        if self.format_type == 'bookended':
            return self._read_all_bookended()
        elif self.format_type == 'json_array':
            return self._read_all_json_array()
        else:
            return []
    
    def read_by_id(self, fetch_id: str) -> Optional[Dict[str, Any]]:
        """Read fetch data by ID - format agnostic"""
        if self.format_type == 'bookended':
            return self._read_bookended(fetch_id)
        elif self.format_type == 'json_array':
            return self._read_json_array(fetch_id)
        else:
            return None
    
    def _read_bookended(self, fetch_id: str) -> Optional[Dict[str, Any]]:
        """Handle current bookended format"""
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
            
            start_marker = f'=== FETCH START: {fetch_id} |'
            start_pos = content.find(start_marker)
            if start_pos == -1:
                return None
                
            end_marker = f'=== FETCH END: {fetch_id} |'
            end_pos = content.find(end_marker, start_pos)
            if end_pos == -1:
                return None
                
            fetch_section = content[start_pos:end_pos]
            json_start = fetch_section.find('\n{')
            json_end = fetch_section.rfind('\n}') + 2
            
            if json_start == -1 or json_end == -1:
                return None
                
            json_content = fetch_section[json_start:json_end]
            return json.loads(json_content)
        except Exception as e:
            print(f"Error reading bookended format: {e}")
            return None
    
    def _read_json_array(self, fetch_id: str) -> Optional[Dict[str, Any]]:
        """Handle pretty JSON array format"""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                return None
                
            for entry in data:
                if entry.get('fetch_id') == fetch_id:
                    return entry.get('data')
            return None
        except Exception as e:
            print(f"Error reading JSON array format: {e}")
            return None
    
    def _read_all_json_array(self) -> List[Dict[str, Any]]:
        """Read all entries from JSON array"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _read_all_bookended(self) -> List[Dict[str, Any]]:
        """Read all entries from bookended format"""
        entries = []
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
            
            fetch_sections = content.split('=== FETCH START:')
            for section in fetch_sections[1:]:
                # Extract fetch_id and timestamp
                marker_end = section.find(' ===')
                if marker_end == -1:
                    continue
                    
                marker = section[:marker_end]
                parts = marker.split(' | ')
                if len(parts) != 2:
                    continue
                    
                fetch_id = parts[0].strip()
                timestamp = parts[1].strip()
                
                # Extract JSON
                json_start = section.find('\n{')
                json_end = section.find('\n=== FETCH END:')
                
                if json_start != -1 and json_end != -1:
                    json_content = section[json_start:json_end].strip()
                    try:
                        data = json.loads(json_content)
                        entries.append({
                            "fetch_id": fetch_id,
                            "timestamp": timestamp,
                            "data": data
                        })
                    except:
                        continue
        except:
            pass
        return entries
    
    def write_entry(self, fetch_id: str, timestamp: str, data: Dict[str, Any]) -> None:
        """Write entry in appropriate format"""
        if self.format_type == 'new_file':
            # New files use pretty JSON array format
            self.format_type = 'json_array'
            self._initialize_json_array()
            
        if self.format_type == 'json_array':
            self._write_json_array(fetch_id, timestamp, data)
        elif self.format_type == 'bookended':
            self._write_bookended(fetch_id, timestamp, data)
    
    def _initialize_json_array(self) -> None:
        """Initialize empty JSON array file"""
        with open(self.file_path, 'w') as f:
            json.dump([], f, indent=2)
    
    def _write_json_array(self, fetch_id: str, timestamp: str, data: Dict[str, Any]) -> None:
        """Write in pretty JSON array format with file locking"""
        try:
            # Read existing data with file lock
            with open(self.file_path, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    entries = json.load(f)
                    if not isinstance(entries, list):
                        entries = []
                except:
                    entries = []
                
                # Add new entry
                new_entry = {
                    "fetch_id": fetch_id,
                    "timestamp": timestamp,
                    "data": data
                }
                entries.append(new_entry)
                
                # Keep only last 50 entries (rotation)
                if len(entries) > 50:
                    entries = entries[-50:]
                
                # Write back with pretty formatting
                f.seek(0)
                f.truncate()
                json.dump(entries, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Add final newline for clean files
                
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print(f"Error writing JSON array: {e}")
            # Fallback to bookended format if array write fails
            self._write_bookended(fetch_id, timestamp, data)
    
    def _write_bookended(self, fetch_id: str, timestamp: str, data: Dict[str, Any]) -> None:
        """Write in bookended format (legacy)"""
        with open(self.file_path, 'a') as f:
            f.write(f'=== FETCH START: {fetch_id} | {timestamp} ===\n')
            json.dump(data, f, indent=2)
            f.write('\n')
            f.write(f'=== FETCH END: {fetch_id} | {timestamp} ===\n')
```

### 2. **Visual Comparison: Before vs After**

#### **BEFORE (Current Bookended Format):**
```
=== FETCH START: V9eHoSddSVus | 07/08/2025 08:31:25 PM EDT ===
{
  "FETCH_HEADER": {
    "fetch_number": 1,
    "random_fetch_id": "V9eHoSddSVus",
    "nyc_timestamp": "07/08/2025 08:31:25 PM EDT"
  },
  "MERGED_DATA": {
    "matches": [...]
  }
}
=== FETCH END: V9eHoSddSVus | 07/08/2025 08:31:25 PM EDT ===
```

**Problems:**
- Not valid JSON (can't use standard tools)
- Complex parsing required
- Can't easily query or analyze
- Breaks JSON viewers/editors

#### **AFTER (Pretty JSON Array):**
```json
[
  {
    "fetch_id": "V9eHoSddSVus",
    "timestamp": "07/08/2025 08:31:25 PM EDT",
    "data": {
      "FETCH_HEADER": {
        "fetch_number": 1,
        "random_fetch_id": "V9eHoSddSVus",
        "nyc_timestamp": "07/08/2025 08:31:25 PM EDT"
      },
      "MERGED_DATA": {
        "matches": [
          {
            "match_id": "123456",
            "home_team": "Liverpool",
            "away_team": "Manchester United",
            "score": "0-0",
            "status": "Half-time"
          }
        ]
      }
    }
  },
  {
    "fetch_id": "yHnFSwp90dzm",
    "timestamp": "07/08/2025 09:29:36 PM EDT",
    "data": {
      "FETCH_HEADER": {...},
      "MERGED_DATA": {...}
    }
  }
]
```

**Benefits:**
- ✅ Valid JSON - works with all tools
- ✅ Human readable with indentation
- ✅ Easy to query (e.g., `jq '.[].fetch_id' merge.json`)
- ✅ Opens in JSON viewers/editors
- ✅ Can analyze with standard tools

### 3. **File Modifications (Same as Before)**

The modifications to each Python file remain exactly the same as in the previous plan. We only change the FetchDataReader implementation to use pretty JSON arrays instead of JSON Lines.

#### Example for `merge.py`:
**DELETE Lines 413-446** and **REPLACE WITH:**
```python
def extract_fetch_data_by_id(self, fetch_id, input_file_path):
    """Extract complete fetch data between header and footer markers"""
    from shared_utils.fetch_data_reader import FetchDataReader
    reader = FetchDataReader(input_file_path)
    return reader.read_by_id(fetch_id)
```

### 4. **Analysis Benefits with Pretty JSON**

Now you can easily analyze your data:

#### **Using jq (command-line JSON processor):**
```bash
# Get all fetch IDs
jq '.[].fetch_id' merge.json

# Find matches with specific status
jq '.[] | select(.data.MERGED_DATA.matches[].status == "Half-time")' merge.json

# Count total matches
jq '[.[].data.MERGED_DATA.matches | length] | add' merge.json

# Extract all home teams
jq '.[].data.MERGED_DATA.matches[].home_team' merge.json
```

#### **Using Python:**
```python
import json

# Load and analyze
with open('merge.json', 'r') as f:
    data = json.load(f)

# Find all half-time matches
half_time_matches = []
for entry in data:
    matches = entry['data']['MERGED_DATA']['matches']
    for match in matches:
        if match['status'] == 'Half-time':
            half_time_matches.append(match)

# Get fetch times
fetch_times = [entry['timestamp'] for entry in data]
```

#### **Using any JSON viewer:**
- VSCode: Opens with syntax highlighting and folding
- Browser extensions: JSON Formatter, JSON Viewer
- Online tools: JSONLint, JSON Editor Online

### 5. **Migration Tool**

Create a tool to convert existing bookended files to pretty JSON:

```python
# migration_tool.py
import json
from shared_utils.fetch_data_reader import FetchDataReader

def migrate_file(file_path):
    """Convert bookended format to pretty JSON array"""
    reader = FetchDataReader(file_path)
    
    if reader.format_type != 'bookended':
        print(f"File {file_path} is not in bookended format")
        return
    
    # Read all entries from bookended format
    entries = reader._read_all_bookended()
    
    # Write as pretty JSON array
    output_path = file_path.replace('.json', '_migrated.json')
    with open(output_path, 'w') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
        f.write('\n')
    
    print(f"Migrated {len(entries)} entries to {output_path}")

# Usage
if __name__ == "__main__":
    migrate_file('merge.json')
    migrate_file('pretty_print.json')
    # etc...
```

### 6. **Performance Considerations**

Pretty JSON arrays have a small performance trade-off compared to JSON Lines, but it's minimal for your use case:

| Aspect | Bookended (Current) | JSON Lines | Pretty JSON Array |
|--------|-------------------|------------|-------------------|
| Human Readable | ❌ No | ❌ No | ✅ Yes |
| Valid JSON | ❌ No | ✅ Yes (per line) | ✅ Yes |
| File Size | Large | Small | Medium |
| Parse Speed | Slow (string search) | Fast (line by line) | Medium (parse array) |
| Tool Support | ❌ None | ✅ Some | ✅ All JSON tools |
| Query-able | ❌ No | 🟡 Limited | ✅ Yes |

For 50 fetches (your rotation size), the performance difference is negligible (milliseconds).

### 7. **Additional Improvements**

Since we're moving to proper JSON, we can add useful features:

#### **Indexing for fast lookup:**
```python
def build_index(self):
    """Build index of fetch_id -> array position for O(1) lookup"""
    if self.format_type != 'json_array':
        return {}
        
    index = {}
    with open(self.file_path, 'r') as f:
        entries = json.load(f)
        for i, entry in enumerate(entries):
            index[entry['fetch_id']] = i
    return index
```

#### **Query methods:**
```python
def find_by_timestamp_range(self, start_time, end_time):
    """Find all entries within a time range"""
    entries = self.read_all()
    return [e for e in entries if start_time <= e['timestamp'] <= end_time]

def find_by_status(self, status):
    """Find all matches with specific status"""
    results = []
    for entry in self.read_all():
        matches = entry['data']['MERGED_DATA']['matches']
        for match in matches:
            if match['status'] == status:
                results.append(match)
    return results
```

## 📊 Summary

This approach gives you:
1. **Clean code** - No more duplicated parsing logic
2. **Human-readable files** - Beautiful, indented JSON
3. **Standard format** - Works with all JSON tools
4. **Easy analysis** - Query with jq, Python, or any tool
5. **Backward compatible** - Old files still work
6. **Visual debugging** - Open in any JSON viewer

The best part? All the code simplification benefits remain the same - you still remove 70+ lines of duplicated code while getting prettier, more useful output files.