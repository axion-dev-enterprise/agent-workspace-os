module.exports = {
  apps: [
    {
      name: 'axion-brain-server',
      script: 'scripts/brain_server.py',
      cwd: 'C:/workspace',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '800M',
      restart_delay: 2000,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        PATH: 'C:\\Program Files\\Git\\usr\\bin;C:\\Program Files\\Git\\cmd;' + (process.env.PATH || '')
      },
      error_file: 'memory/brain/pm2_logs/error.log',
      out_file: 'memory/brain/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'axion-telegram-bot',
      script: 'scripts/telegram_assistant_bot.py',
      cwd: 'C:/workspace',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        BRAIN_URL: 'http://127.0.0.1:8765',
        PATH: 'C:\\Program Files\\Git\\usr\\bin;C:\\Program Files\\Git\\cmd;' + (process.env.PATH || '')
      },

      error_file: 'memory/telegram/pm2_logs/error.log',
      out_file: 'memory/telegram/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'axion-whatsapp-bridge',
      script: 'server.js',
      cwd: 'C:/workspace/scripts/whatsapp_bridge',
      interpreter: 'node',
      autorestart: true,
      watch: false,
      max_memory_restart: '400M',
      restart_delay: 3000,
      env: {
        WHATSAPP_PORT: process.env.WHATSAPP_PORT || '4114',
        WHATSAPP_PAIRING_NUMBER: process.env.WHATSAPP_PAIRING_NUMBER || '551151041784',
        WHATSAPP_ADMIN_NUMBER: process.env.WHATSAPP_ADMIN_NUMBER || '5511988045139',
        WHATSAPP_ADMIN_LID: process.env.WHATSAPP_ADMIN_LID || '36735559962762',
        BRAIN_URL: process.env.BRAIN_URL || 'http://127.0.0.1:8765'
      },
      error_file: 'memory/whatsapp/pm2_logs/error.log',
      out_file: 'memory/whatsapp/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
