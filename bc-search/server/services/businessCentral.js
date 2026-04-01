const axios = require('axios');
const config = require('../config');

// ---------------------------------------------------------------------------
// Token cache
// ---------------------------------------------------------------------------
let tokenCache = { accessToken: null, expiresAt: 0 };

/**
 * Acquire an OAuth2 access token using the client-credentials flow.
 * Caches the token and refreshes 60 s before expiry.
 */
async function getAccessToken() {
  if (tokenCache.accessToken && Date.now() < tokenCache.expiresAt - 60000) {
    return tokenCache.accessToken;
  }

  const url = `https://login.microsoftonline.com/${config.bc.tenantId}/oauth2/v2.0/token`;

  const params = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: config.bc.clientId,
    client_secret: config.bc.clientSecret,
    scope: 'https://api.businesscentral.dynamics.com/.default'
  });

  const { data } = await axios.post(url, params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });

  tokenCache = {
    accessToken: data.access_token,
    expiresAt: Date.now() + data.expires_in * 1000
  };

  return tokenCache.accessToken;
}

// ---------------------------------------------------------------------------
// Base URL builder
// ---------------------------------------------------------------------------
function baseUrl() {
  const { tenantId, environment, companyId } = config.bc;
  return `https://api.businesscentral.dynamics.com/v2.0/${tenantId}/${environment}/api/v2.0/companies(${companyId})`;
}

// ---------------------------------------------------------------------------
// OData query helper
// ---------------------------------------------------------------------------

/**
 * Execute an OData query against a Business Central entity.
 *
 * @param {Object} opts
 * @param {string} opts.entity      - e.g. "items", "customers", "salesInvoiceLines"
 * @param {string} [opts.select]    - $select fields  (comma-separated)
 * @param {string} [opts.filter]    - $filter expression
 * @param {string} [opts.orderby]   - $orderby expression
 * @param {number} [opts.top]       - $top limit
 * @param {string} [opts.expand]    - $expand navigation properties
 * @param {boolean}[opts.count]     - include $count
 * @returns {Promise<Object[]>}     - array of entity records
 */
async function query(opts) {
  const token = await getAccessToken();

  let url = `${baseUrl()}/${opts.entity}`;

  const params = {};
  if (opts.select)  params['$select']  = opts.select;
  if (opts.filter)  params['$filter']  = opts.filter;
  if (opts.orderby) params['$orderby'] = opts.orderby;
  if (opts.top)     params['$top']     = opts.top;
  if (opts.expand)  params['$expand']  = opts.expand;
  if (opts.count)   params['$count']   = 'true';

  let allRecords = [];
  let nextLink = null;
  let isFirst = true;
  let totalCount = null;

  do {
    const requestUrl = isFirst ? url : nextLink;
    const requestParams = isFirst ? params : {};

    const { data } = await axios.get(requestUrl, {
      params: requestParams,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json'
      }
    });

    if (data['@odata.count'] !== undefined) {
      totalCount = data['@odata.count'];
    }

    const records = data.value || [];
    allRecords = allRecords.concat(records);

    nextLink = data['@odata.nextLink'] || null;
    isFirst = false;

    // Safety: stop after 5000 records to avoid runaway pagination
    if (allRecords.length >= 5000) break;
  } while (nextLink);

  return { records: allRecords, totalCount };
}

/**
 * Execute multiple OData queries in parallel.
 * @param {Object[]} queries - array of query option objects
 * @returns {Promise<Object[]>} - array of result objects
 */
async function queryMultiple(queries) {
  return Promise.all(queries.map(q => query(q)));
}

/**
 * List all available companies (useful for initial setup).
 */
async function listCompanies() {
  const token = await getAccessToken();
  const { tenantId, environment } = config.bc;
  const url = `https://api.businesscentral.dynamics.com/v2.0/${tenantId}/${environment}/api/v2.0/companies`;

  const { data } = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json'
    }
  });

  return data.value || [];
}

module.exports = { query, queryMultiple, listCompanies };
