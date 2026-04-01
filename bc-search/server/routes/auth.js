const express = require('express');
const router = express.Router();
const bc = require('../services/businessCentral');

/**
 * GET /api/auth/test
 * Quick test to verify Business Central credentials are working.
 * Returns list of companies or an error.
 */
router.get('/test', async (req, res) => {
  try {
    const companies = await bc.listCompanies();
    res.json({
      success: true,
      message: `Connected! Found ${companies.length} company(ies).`,
      companies: companies.map(c => ({ id: c.id, name: c.displayName }))
    });
  } catch (err) {
    console.error('Auth test failed:', err.message);

    let detail = 'Unknown error';
    if (err.response) {
      if (err.response.status === 401) detail = 'Invalid client credentials. Check BC_CLIENT_ID and BC_CLIENT_SECRET.';
      else if (err.response.status === 403) detail = 'Access denied. Ensure API permissions are granted and admin consent is given.';
      else if (err.response.status === 404) detail = 'Tenant or environment not found. Check BC_TENANT_ID and BC_ENVIRONMENT.';
      else detail = `HTTP ${err.response.status}: ${err.response.statusText}`;
    } else if (err.code === 'ENOTFOUND') {
      detail = 'Network error. Cannot reach Microsoft login servers.';
    }

    res.status(500).json({
      success: false,
      message: 'Failed to connect to Business Central.',
      detail
    });
  }
});

module.exports = router;
