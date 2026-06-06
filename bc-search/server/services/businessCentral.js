const { NtlmClient } = require('axios-ntlm');
const config = require('../config');

// ---------------------------------------------------------------------------
// NTLM client (Windows Authentication with domain credentials)
// ---------------------------------------------------------------------------
const username = config.bc.username;
const parts = username.split('\\');
const domain = parts.length > 1 ? parts[0] : '';
const user = parts.length > 1 ? parts[1] : username;

const client = NtlmClient({
  username: user,
  password: config.bc.password,
  domain: domain
});

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

    const { data } = await client.get(requestUrl, {
      params: requestParams,
      headers: { Accept: 'application/json' }
    });

    if (data['@odata.count'] !== undefined) {
      totalCount = data['@odata.count'];
    }

    const records = data.value || [];
    allRecords = allRecords.concat(records);

    nextLink = data['@odata.nextLink'] || null;
    isFirst = false;

    if (allRecords.length >= 5000) break;
  } while (nextLink);

  return { records: allRecords, totalCount };
}

/**
 * Execute multiple OData queries in parallel.
 */
async function queryMultiple(queries) {
  return Promise.all(queries.map(q => query(q)));
}

/**
 * List all available companies.
 */
async function listCompanies() {
  const { data } = await client.get(`${config.bc.serverUrl}/Company`, {
    headers: { Accept: 'application/json' }
  });

  return data.value || [];
}

module.exports = { query, queryMultiple, listCompanies };
