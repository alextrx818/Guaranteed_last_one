module.exports = {
  apps: [{
    name: 'telegram-monitor',
    script: 'telegram-monitor.js',
    args: 'start',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    restart_delay: 5000,
    max_restarts: 10,
    min_uptime: '10s',
    env: {
      NODE_ENV: 'production'
    },
    log_file: './logs/telegram-monitor.log',
    out_file: './logs/telegram-monitor-out.log',
    error_file: './logs/telegram-monitor-error.log',
    log_date_format: 'YYYY-MM-DD HH:mm Z'
  }]
};