const axios = require('axios');
const config = require('../config');

// ---------------------------------------------------------------------------
// Basic Auth header (on-premises: username + web service access key)
// ---------------------------------------------------------------------------
function authHeader() {
  const credentials = Buffer.from(
    `${config.bc.username}:${config.bc.webServiceKey}`
  ).toString('base64');
  return `Basic ${credentials}`;
}

// ---------------------------------------------------------------------------
// Base URL builder
// ---------------------------------------------------------------------------
function baseUrl() {
  const companyFilter = encodeURIComponent(config.bc.companyName);
  return `${config.bc.serverUrl}/Company('${companyFilter}')`;
}

// ---------------------------------------------------------------------------
// OData query helper
// ---------------------------------------------------------------------------

/**
 * Execute an OData query against a Business Central entity.
 *
 * @param {Object} opts
 * @param {string} opts.entity      - e.g. "Item", "Customer", "Sales_Invoice_Line"
 * @param {string} [opts.select]    - $select fields  (comma-separated)
 * @param {string} [opts.filter]    - $filter expression
 * @param {string} [opts.orderby]   - $orderby expression
 * @param {number} [opts.top]       - $top limit
 * @param {string} [opts.expand]    - $expand navigation properties
 * @param {boolean}[opts.count]     - include $count
 * @returns {Promise<Object>}       - { records: Object[], totalCount: number|null }
 */
async function query(opts) {
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
        Authorization: authHeader(),
        Accept: 'application/json'
      },
      // On-prem may use self-signed certs — allow configuring this
      ...(process.env.BC_ALLOW_SELF_SIGNED === 'true' && {
        httpsAgent: new (require('https').Agent)({ rejectUnauthorized: false })
      })
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
 * List all available companies (useful for initial setup / connection test).
 */
async function listCompanies() {
  const { data } = await axios.get(`${config.bc.serverUrl}/Company`, {
    headers: {
      Authorization: authHeader(),
      Accept: 'application/json'
    },
    ...(process.env.BC_ALLOW_SELF_SIGNED === 'true' && {
      httpsAgent: new (require('https').Agent)({ rejectUnauthorized: false })
    })
  });

  return data.value || [];
}

module.exports = { query, queryMultiple, listCompanies };
