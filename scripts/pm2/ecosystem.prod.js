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
    }
  ]
};
