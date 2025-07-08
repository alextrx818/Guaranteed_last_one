# JSON Watchdog - How It Works

A simple file monitoring system that watches your JSON files for changes and sends real-time alerts via Telegram.

## How It Works

### 🔍 **File Monitoring**
- Monitors specified JSON files every **5 seconds**
- Uses MD5 hash comparison to detect file changes
- Only triggers alerts when files actually change (not just timestamp updates)

### 📱 **Alert System**
- Sends notifications via **Telegram Bot API**
- Real-time delivery to your phone/desktop
- Formatted messages with match details

### ⚙️ **Configuration**
- **User-controlled**: You specify which JSON files to monitor
- **Easy setup**: Just edit the `MONITOR_FILES` object
- **No file editing**: Only reads files, never modifies them

## Current Monitoring Setup

```javascript
const MONITOR_FILES = {
    alert_3ou: './7_alert_3ou_half/alert_3ou_half.json',
    alert_underdog: './8_alert_underdog_0half/alert_underdog_0half.json'
};
```

## Detection Logic

### 🚨 **3+ O/U Alerts**
- Monitors: `7_alert_3ou_half/alert_3ou_half.json`
- Triggers when: `filtered_match_count > 0`
- Alert: Shows number of matches with 3+ Over/Under criteria

### 🎯 **Underdog Alerts**
- Monitors: `8_alert_underdog_0half/alert_underdog_0half.json`
- Triggers when: Match data found in `monitor_central_display`
- Alert: Shows number of underdog matches detected

## Commands

```bash
# Get your Telegram Chat ID
node get-chat-id.js

# Show help and current configuration
node telegram-monitor.js

# Test Telegram connection
node telegram-monitor.js test

# Start monitoring (runs continuously)
node telegram-monitor.js start
```

## Setup Process

1. **Message the bot**: https://t.me/Livesportsfootball_bot
2. **Get your Chat ID**: `node get-chat-id.js`
3. **Configure monitor**: Edit `CHAT_ID` in `telegram-monitor.js`
4. **Start watching**: `node telegram-monitor.js start`

## Sample Alerts

```
🚨 3+ O/U ALERT

📊 5 matches found with 3+ Over/Under criteria
⏰ 07/02/2025 06:30:51 PM EDT
```

```
🎯 UNDERDOG ALERT

📊 12 underdog matches detected
⏰ 07/02/2025 06:30:51 PM EDT
```

## Adding More Files

Edit the `MONITOR_FILES` object in `telegram-monitor.js`:

```javascript
const MONITOR_FILES = {
    alert_3ou: './7_alert_3ou_half/alert_3ou_half.json',
    alert_underdog: './8_alert_underdog_0half/alert_underdog_0half.json',
    monitor_central: './6_monitor_central/monitor_central.json',  // Add this
    your_custom_file: './path/to/your/file.json'                 // Or this
};
```

## Watchdog Features

✅ **Continuous monitoring** - Runs until you stop it  
✅ **Change detection** - Only alerts on actual changes  
✅ **Real-time alerts** - Instant Telegram notifications  
✅ **Easy configuration** - Just edit the file list  
✅ **No file modification** - Read-only monitoring  
✅ **Error handling** - Graceful failure recovery  

## Stop Monitoring

Press `Ctrl+C` in the terminal where it's running.

## Technical Details

- **Language**: Node.js (JavaScript)
- **Dependencies**: Built-in modules only (`https`, `fs`, `crypto`)
- **Update frequency**: 5 seconds
- **Detection method**: MD5 hash comparison
- **Alert delivery**: Telegram Bot API
- **File access**: Read-only

The system is designed to be lightweight, reliable, and easy to customize for your specific JSON monitoring needs.