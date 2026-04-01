require('dotenv').config();

const required = [
  'ANTHROPIC_API_KEY',
  'BC_TENANT_ID',
  'BC_CLIENT_ID',
  'BC_CLIENT_SECRET',
  'BC_ENVIRONMENT',
  'BC_COMPANY_ID'
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
    tenantId: process.env.BC_TENANT_ID,
    clientId: process.env.BC_CLIENT_ID,
    clientSecret: process.env.BC_CLIENT_SECRET,
    environment: process.env.BC_ENVIRONMENT,
    companyId: process.env.BC_COMPANY_ID
  },
  port: parseInt(process.env.PORT, 10) || 3000
};
