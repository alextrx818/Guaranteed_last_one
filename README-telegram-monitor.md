# Telegram JSON Monitor

Real-time monitoring system that watches your sports betting JSON pipeline and sends alerts to Telegram.

## What it does:
- **VAR incident detection** (Type 28 incidents)
- **Match status changes** (First half → Half-time → Second half → End)
- **Score updates** in real-time
- **Alert conditions** for 3+ O/U and Underdog first half scenarios
- **File monitoring** of your JSON pipeline every 5 seconds

## Quick Setup:

### 1. Message the Telegram Bot
Go to: https://t.me/Livesportsfootball_bot
Send any message (like "hello")

### 2. Get Your Chat ID
```bash
node get-chat-id.js
```
This will show you a number like: `123456789`

### 3. Update the Monitor File
Edit `telegram-monitor.js` line 7:
```javascript
const CHAT_ID = '123456789'; // Replace with your actual chat ID
```

### 4. Start Monitoring
```bash
node telegram-monitor.js start
```

## Commands:

```bash
# Show help menu
node telegram-monitor.js

# Test Telegram connection
node telegram-monitor.js test

# Get setup instructions
node telegram-monitor.js getchatid

# Start real-time monitoring
node telegram-monitor.js start
```

## What Node means:
- **node** = the program that runs JavaScript on your computer
- **telegram-monitor.js** = the monitoring script I created
- So `node telegram-monitor.js` means "run the telegram monitoring program"

## Files being monitored:
- `6_monitor_central/monitor_central.json` - Main match data
- `7_alert_3ou_half/alert_3ou_half.json` - 3+ Over/Under alerts
- `8_alert_underdog_0half/alert_underdog_0half.json` - Underdog first half alerts

## Sample Telegram alerts you'll receive:
```
🚨 VAR INCIDENT DETECTED
⚽ Match: Real Madrid vs Barcelona
🏆 Competition: La Liga
📱 Type: VAR Review (Type 28)
⏰ Time: 07/02/2025 06:15:33 PM EDT
```

```
⚽ SCORE UPDATE
🆚 Match: Arsenal vs Chelsea  
📊 Score: Live Score: 2-1 (HT: 1-0)
⏰ Time: 07/02/2025 06:15:33 PM EDT
```

## Stop monitoring:
Press `Ctrl+C` in the terminal where it's running

## Bot credentials:
- **Bot URL**: https://t.me/Livesportsfootball_bot
- **Bot Token**: 7848696790:AAFhzVNuNsL_hUvsZMabpCUz2RVRhc0PMo8

## Troubleshooting:
- If you get "Chat ID not configured" - follow steps 2-3 above
- If messages aren't sending - make sure you messaged the bot first
- If the script stops - just run `node telegram-monitor.js start` again