module.exports = {
  apps: [
    {
      name: 'axion-brain-dev',
      script: 'scripts/brain_server.py',
      cwd: 'C:/workspace',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '800M',
      restart_delay: 1000,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        AXION_ENV: 'dev',
        BRAIN_PORT: '8766',
        PATH: 'C:\\Program Files\\Git\\usr\\bin;C:\\Program Files\\Git\\cmd;' + (process.env.PATH || '')
      },
      error_file: 'memory_dev/brain/pm2_logs/error.log',
      out_file: 'memory_dev/brain/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'axion-bot-dev',
      script: 'scripts/telegram_assistant_bot.py',
      cwd: 'C:/workspace',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      restart_delay: 2000,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        AXION_ENV: 'dev',
        BRAIN_URL: 'http://127.0.0.1:8766',
        PATH: 'C:\\Program Files\\Git\\usr\\bin;C:\\Program Files\\Git\\cmd;' + (process.env.PATH || '')
      },

      error_file: 'memory_dev/telegram/pm2_logs/error.log',
      out_file: 'memory_dev/telegram/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
