const https = require('https');
const fs = require('fs');

// CONFIGURATION - Edit these settings
const BOT_TOKEN = '7848696790:AAFhzVNuNsL_hUvsZMabpCUz2RVRhc0PMo8';
const CHAT_ID = 'YOUR_CHAT_ID_HERE';  // Get this by running: node get-chat-id.js

// JSON FILES TO MONITOR - Edit monitor-files.txt to add/remove files
function loadMonitorFiles() {
    try {
        const fileContent = fs.readFileSync('./monitor-files.txt', 'utf8');
        const files = {};
        fileContent.split('\n').forEach((line, index) => {
            const path = line.trim();
            if (path && !path.startsWith('#')) {
                const name = `file_${index + 1}`;
                files[name] = path;
            }
        });
        return files;
    } catch (error) {
        console.log('❌ Could not read monitor-files.txt, using default files');
        return {
            alert_3ou: './7_alert_3ou_half/alert_3ou_half.json',
            alert_underdog: './8_alert_underdog_0half/alert_underdog_0half.json'
        };
    }
}

// Store previous file contents to detect changes
let previousData = {};

function sendTelegramMessage(message) {
    if (CHAT_ID === 'YOUR_CHAT_ID_HERE') {
        console.log('❌ Chat ID not configured. Run: node get-chat-id.js');
        return;
    }

    const postData = JSON.stringify({
        chat_id: CHAT_ID,
        text: message,
        parse_mode: 'Markdown'
    });

    const options = {
        hostname: 'api.telegram.org',
        path: `/bot${BOT_TOKEN}/sendMessage`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': postData.length
        }
    };

    const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            try {
                const response = JSON.parse(data);
                if (response.ok) {
                    console.log(`✅ Message sent: ${message.substring(0, 50)}...`);
                } else {
                    console.log('❌ Telegram error:', response.description);
                }
            } catch (error) {
                console.log('❌ Error parsing response:', error.message);
            }
        });
    });

    req.on('error', (error) => {
        console.log('❌ Network error:', error.message);
    });

    req.write(postData);
    req.end();
}

function checkFile(filename, filepath) {
    try {
        if (!fs.existsSync(filepath)) {
            console.log(`⚠️  File not found: ${filepath}`);
            return;
        }

        const fileContent = fs.readFileSync(filepath, 'utf8');
        const currentHash = require('crypto').createHash('md5').update(fileContent).digest('hex');
        
        // Check if file changed
        if (previousData[filename] && previousData[filename] !== currentHash) {
            console.log(`📄 File changed: ${filename}`);
            
            // Send alert for ANY JSON file change
            const fileName = filepath.split('/').pop();
            sendTelegramMessage(`🔔 *JSON FILE UPDATED*\n\n📄 File: ${fileName}\n⏰ ${new Date().toLocaleString()}`);
        }
        
        previousData[filename] = currentHash;
        
    } catch (error) {
        console.log(`❌ Error reading ${filename}:`, error.message);
    }
}

function startMonitoring() {
    const MONITOR_FILES = loadMonitorFiles();
    
    console.log('\n🔍 Starting JSON file monitoring...');
    console.log('📁 Monitoring files:');
    Object.entries(MONITOR_FILES).forEach(([name, path]) => {
        console.log(`   • ${name}: ${path}`);
    });
    console.log('\n⏹️  Press Ctrl+C to stop\n');

    // Initialize file hashes
    Object.entries(MONITOR_FILES).forEach(([name, path]) => {
        checkFile(name, path);
    });

    // Monitor every 5 seconds
    setInterval(() => {
        Object.entries(MONITOR_FILES).forEach(([name, path]) => {
            checkFile(name, path);
        });
    }, 5000);
}

function testConnection() {
    console.log('🧪 Testing Telegram connection...');
    sendTelegramMessage('✅ Test message from JSON Monitor\n\nIf you see this, everything is working!');
}

function showHelp() {
    console.log(`
📋 JSON Monitor - Telegram Alert System

Commands:
  node telegram-monitor.js start      - Start monitoring JSON files
  node telegram-monitor.js test       - Test Telegram connection  
  node telegram-monitor.js getchatid  - Get your Telegram Chat ID

Setup:
1. Get your chat ID: node get-chat-id.js
2. Edit CHAT_ID in this file
3. Edit monitor-files.txt to add/remove JSON files to monitor
4. Start monitoring: node telegram-monitor.js start

To add/remove files: Edit monitor-files.txt
Each line = one JSON file path to monitor
`);
}

// Command handler
const command = process.argv[2];

switch (command) {
    case 'start':
        startMonitoring();
        break;
    case 'test':
        testConnection();
        break;
    case 'getchatid':
        console.log('Run this command to get your chat ID: node get-chat-id.js');
        break;
    default:
        showHelp();
}