# 📱 Telegram JSON Monitor - Visual Flow Guide

A visual walkthrough of how the Telegram monitoring system works for real-time sports data alerts.

## 📱 TELEGRAM JSON MONITOR - VISUAL FLOW

### ┌─────────────────────────────────────────────────────────────────┐
### │                        STARTUP PHASE                           │
### └─────────────────────────────────────────────────────────────────┘

**1. YOU RUN:** `node telegram-monitor.js start`
```
   │
   ├── 📋 Reads monitor-files.txt
   │   ├── ./7_alert_3ou_half/alert_3ou_half.json
   │   └── ./8_alert_underdog_0half/alert_underdog_0half.json
   │
   ├── 🔍 Creates MD5 hash of each file (initial snapshot)
   │   ├── File1: abc123def456...
   │   └── File2: xyz789uvw012...
   │
   └── ⏰ Starts 5-second timer loop
```

### ┌─────────────────────────────────────────────────────────────────┐
### │                     CONTINUOUS MONITORING                      │
### └─────────────────────────────────────────────────────────────────┘

**Every 5 seconds:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Second 0-5    │    │   Second 5-10   │    │  Second 10-15   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ ✅ Check File 1 │    │ ✅ Check File 1 │    │ ✅ Check File 1 │
│ ✅ Check File 2 │    │ ✅ Check File 2 │    │ ✅ Check File 2 │
│ 😴 No changes  │    │ 😴 No changes  │    │ 🚨 CHANGE!     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               📱 TELEGRAM ALERT!
```

### ┌─────────────────────────────────────────────────────────────────┐
### │                       ALERT TRIGGER                            │
### └─────────────────────────────────────────────────────────────────┘

**🏃‍♂️ Your Sports Pipeline Updates Files:**
```
   │
   ├── 📊 Pipeline writes new data to alert_3ou_half.json
   │   │   - Old hash: abc123def456...
   │   │   - New hash: NEW987hash654...
   │   │
   └── 🔍 Monitor detects change (within 5 seconds)
       │
       ├── 📱 Sends Telegram Message:
       │   ┌─────────────────────────────────────┐
       │   │ 🔔 JSON FILE UPDATED               │
       │   │                                    │
       │   │ 📄 File: alert_3ou_half.json      │
       │   │ ⏰ 7/2/2025, 6:53:18 PM           │
       │   └─────────────────────────────────────┘
       │
       └── 💾 Updates stored hash for next check
```

### ┌─────────────────────────────────────────────────────────────────┐
### │                    FILE MANAGEMENT                             │
### └─────────────────────────────────────────────────────────────────┘

**ADD NEW FILE:**
```
Edit monitor-files.txt:
   ./7_alert_3ou_half/alert_3ou_half.json
   ./8_alert_underdog_0half/alert_underdog_0half.json
   ./new_file.json  ← ADD THIS
                    │
                    ▼
   Next check cycle (≤5 seconds) automatically picks up new file
```

**REMOVE FILE:**
```
Delete line from monitor-files.txt:
   ./7_alert_3ou_half/alert_3ou_half.json
   # ./8_alert_underdog_0half/alert_underdog_0half.json  ← COMMENT OUT
                    │
                    ▼
   Next check cycle stops monitoring that file
```

### ┌─────────────────────────────────────────────────────────────────┐
### │                    REAL-TIME EXAMPLE                           │
### └─────────────────────────────────────────────────────────────────┘

```
TIME: 6:53:16 PM - Monitor checks, files unchanged
TIME: 6:53:18 PM - Your pipeline updates JSON files 
                   ↓ (2 seconds later)
TIME: 6:53:21 PM - Monitor detects changes
                   ↓ (instantly)
TIME: 6:53:21 PM - 📱 Telegram alert sent!
```

### ┌─────────────────────────────────────────────────────────────────┐
### │                      YOUR WORKFLOW                             │
### └─────────────────────────────────────────────────────────────────┘

```
1. 🚀 Start once: node telegram-monitor.js start
2. 📱 Get alerts automatically
3. ➕ Add files: Edit monitor-files.txt 
4. ➖ Remove files: Comment out lines
5. 🔄 Runs forever until Ctrl+C
```

## Key Points

- ⚡ **Fast**: Detects changes within 5 seconds max
- 🔄 **Automatic**: No manual intervention needed  
- 📝 **Simple**: Just edit text file to add/remove monitoring
- 🎯 **Reliable**: MD5 hash comparison catches any change
- 📱 **Instant alerts**: Telegram message sent immediately when change detected

## The Flow in Action

**Your sports pipeline keeps updating files** → **Monitor catches changes** → **You get instant Telegram alerts!**

## Setup Commands

```bash
# Get your Telegram chat ID
node get-chat-id.js

# Test the connection  
node telegram-monitor.js test

# Start continuous monitoring
node telegram-monitor.js start

# Stop monitoring
Ctrl+C
```

## File Structure

```
monitor-files.txt           ← Simple list of files to monitor
telegram-monitor.js         ← Main monitoring script
get-chat-id.js             ← Helper to get your Telegram chat ID
```

Perfect for sports betting data pipelines - **set it and forget it!**