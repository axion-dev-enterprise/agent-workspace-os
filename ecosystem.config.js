const path = require('path');
const rootDir = __dirname;
const isWin = process.platform === 'win32';
const pyInterpreter = isWin ? 'python' : 'python3';
const winGitPath = 'C:\\Program Files\\Git\\usr\\bin;C:\\Program Files\\Git\\cmd;';
const extraPath = isWin ? winGitPath + (process.env.PATH || '') : (process.env.PATH || '');

module.exports = {
  apps: [
    {
      name: 'axion-brain-server',
      script: 'scripts/brain_server.py',
      cwd: rootDir,
      interpreter: pyInterpreter,
      autorestart: true,
      watch: false,
      max_memory_restart: '800M',
      restart_delay: 2000,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        BRAIN_HOST: '0.0.0.0',
        PATH: extraPath
      },
      error_file: 'memory/brain/pm2_logs/error.log',
      out_file: 'memory/brain/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'axion-telegram-bot',
      script: 'scripts/telegram_assistant_bot.py',
      cwd: rootDir,
      interpreter: pyInterpreter,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        BRAIN_URL: 'http://127.0.0.1:8765',
        PATH: extraPath
      },
      error_file: 'memory/telegram/pm2_logs/error.log',
      out_file: 'memory/telegram/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'axion-whatsapp-bridge',
      script: 'server.js',
      cwd: path.join(rootDir, 'scripts/whatsapp_bridge'),
      interpreter: 'node',
      autorestart: true,
      watch: false,
      max_memory_restart: '400M',
      restart_delay: 3000,
      env: {
        WHATSAPP_PORT: process.env.WHATSAPP_PORT || '4114',
        WHATSAPP_PAIRING_NUMBER: process.env.WHATSAPP_PAIRING_NUMBER || '',
        WHATSAPP_ADMIN_NUMBER: process.env.WHATSAPP_ADMIN_NUMBER || '',
        WHATSAPP_ADMIN_LID: process.env.WHATSAPP_ADMIN_LID || '',
        BRAIN_URL: process.env.BRAIN_URL || 'http://127.0.0.1:8765'
      },
      error_file: 'memory/whatsapp/pm2_logs/error.log',
      out_file: 'memory/whatsapp/pm2_logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
