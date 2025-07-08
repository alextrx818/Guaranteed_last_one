const https = require('https');

// Replace with your bot token from BotFather
const BOT_TOKEN = '7848696790:AAFhzVNuNsL_hUvsZMabpCUz2RVRhc0PMo8';

function getChatId() {
    const url = `https://api.telegram.org/bot${BOT_TOKEN}/getUpdates`;
    
    https.get(url, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            try {
                const updates = JSON.parse(data);
                
                if (updates.result && updates.result.length > 0) {
                    const chatId = updates.result[0].message.chat.id;
                    console.log('✅ Your Chat ID:', chatId);
                    console.log('\nSave this Chat ID - you\'ll need it for the log monitor!');
                } else {
                    console.log('❌ No messages found.');
                    console.log('📱 Send any message to your bot first, then run this script again.');
                }
            } catch (error) {
                console.log('❌ Error:', error.message);
                console.log('🔧 Make sure your bot token is correct.');
            }
        });
    }).on('error', (error) => {
        console.log('❌ Network error:', error.message);
    });
}

if (BOT_TOKEN === 'YOUR_BOT_TOKEN_HERE') {
    console.log('❌ Please replace YOUR_BOT_TOKEN_HERE with your actual bot token');
    console.log('📱 Get it from @BotFather on Telegram');
} else {
    getChatId();
}