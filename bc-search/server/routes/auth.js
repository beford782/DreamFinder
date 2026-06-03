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
      companies: companies.map(c => ({ id: c.Name || c.name, name: c.Name || c.name }))
    });
  } catch (err) {
    console.error('Auth test failed:', err.message);

    let detail = 'Unknown error';
    if (err.response) {
      if (err.response.status === 401) detail = 'Invalid credentials. Check BC_USERNAME and BC_WEB_SERVICE_KEY.';
      else if (err.response.status === 403) detail = 'Access denied. The user may not have permission to access OData services.';
      else if (err.response.status === 404) detail = 'OData endpoint not found. Check BC_SERVER_URL — it should end with /ODataV4 (e.g. https://server:7048/BC/ODataV4).';
      else detail = `HTTP ${err.response.status}: ${err.response.statusText}`;
    } else if (err.code === 'ENOTFOUND') {
      detail = 'Cannot reach the BC server. Check BC_SERVER_URL and make sure the server is accessible from this machine.';
    } else if (err.code === 'ECONNREFUSED') {
      detail = 'Connection refused. The BC server may be down or the port may be wrong.';
    } else if (err.code === 'UNABLE_TO_VERIFY_LEAF_SIGNATURE' || err.code === 'DEPTH_ZERO_SELF_SIGNED_CERT') {
      detail = 'SSL certificate error. If using a self-signed cert, add BC_ALLOW_SELF_SIGNED=true to your .env file.';
    }

    res.status(500).json({
      success: false,
      message: 'Failed to connect to Business Central.',
      detail
    });
  }
});

module.exports = router;
