require('dotenv').config();

const required = [
  'ANTHROPIC_API_KEY',
  'BC_SERVER_URL',
  'BC_USERNAME',
  'BC_WEB_SERVICE_KEY',
  'BC_COMPANY_NAME'
];

const missing = required.filter(key => !process.env[key]);
if (missing.length > 0) {
  console.error(`Missing required environment variables: ${missing.join(', ')}`);
  console.error('Copy .env.example to .env and fill in your values.');
  process.exit(1);
}

module.exports = {
  anthropicApiKey: process.env.ANTHROPIC_API_KEY,
  bc: {
    serverUrl: process.env.BC_SERVER_URL.replace(/\/+$/, ''),
    username: process.env.BC_USERNAME,
    webServiceKey: process.env.BC_WEB_SERVICE_KEY,
    companyName: process.env.BC_COMPANY_NAME
  },
  port: parseInt(process.env.PORT, 10) || 3000
};
