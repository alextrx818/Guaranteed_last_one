# VAR Type 28 Scanner Results

## Script Created: `var_type_28.py`

A standalone VAR incident scanner that monitors `all_api.json` for VAR incidents (type 28) without modifying any existing pipeline code.

## Current Scan Results

**Scan Timestamp**: 2025-07-02 21:40:39

**Total Matches with VAR**: 1

### VAR Incidents Found:

**Match ID**: 23xmvkh8epxkqg8  
**Teams**: Juan Pablo II vs FBC Melgar  
**Competition**: Peruvian Liga 1  

**VAR Incident Details**:
- **Type**: 28 (VAR incident)
- **Position**: 1
- **Time**: 35 minutes
- **Player ID**: l5ergphep5l0r8k
- **Player Name**: Cristhian Andres Tizon Correa
- **VAR Reason**: 1
- **VAR Result**: 2
- **Total Incidents in Match**: 11
- **VAR Incident Count**: 1

## Script Features

- **Non-invasive**: Doesn't modify existing pipeline code
- **Automated logging**: Creates timestamped entries in `var_type_28_log.json`
- **Historical tracking**: Maintains log of all scans over time
- **Detailed reporting**: Provides comprehensive VAR incident details
- **Real-time monitoring**: Can be run periodically to track VAR incidents

## Usage

### Manual Execution
```bash
cd /root/Guaranteed_last_one
python3 var_type_28.py
```

### Automated Options

#### 1. Cron Job (Scheduled execution)
```bash
# Run every 5 minutes
*/5 * * * * cd /root/Guaranteed_last_one && python3 var_type_28.py

# Run every hour
0 * * * * cd /root/Guaranteed_last_one && python3 var_type_28.py
```

#### 2. Shell Script Wrapper
```bash
#!/bin/bash
cd /root/Guaranteed_last_one
while true; do
    python3 var_type_28.py
    sleep 300  # Wait 5 minutes
done
```

#### 3. Integration with Existing Pipeline
Add to the end of `monitor_central.py`:
```python
import subprocess
subprocess.run(['python3', '/root/Guaranteed_last_one/var_type_28.py'])
```

#### 4. File Watcher (When all_api.json changes)
```bash
while inotifywait -e modify /root/Guaranteed_last_one/1_all_api/all_api.json; do
    python3 /root/Guaranteed_last_one/var_type_28.py
done
```

#### 5. Systemd Service (Linux)
```ini
[Unit]
Description=VAR Type 28 Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /root/Guaranteed_last_one/var_type_28.py
Restart=always
WorkingDirectory=/root/Guaranteed_last_one

[Install]
WantedBy=multi-user.target
```

## Log File Location

Results are saved to: `/root/Guaranteed_last_one/var_type_28_log.json`

## Previous Investigation Summary

During our investigation, we discovered that:

1. **VAR incidents flow correctly** through the pipeline from `all_api.json` → `monitor_central.json` → `alert_underdog_0half.json`
2. **Mock test data gets filtered out** because the `all_api.json` file is continuously refreshed from the live API
3. **Real VAR incidents are preserved** and successfully transmitted through all pipeline stages
4. **The filtering happens at the data source level**, not in the pipeline processing code

The VAR type 28 scanner provides a clean solution to monitor these incidents without interfering with the existing data pipeline infrastructure.