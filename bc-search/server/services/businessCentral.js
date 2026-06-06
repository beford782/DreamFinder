const axios = require('axios');
const config = require('../config');

// ---------------------------------------------------------------------------
// Basic Auth header (username + web service access key)
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
      }
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
  const { data } = await axios.get(`${config.bc.serverUrl}/Company`, {
    headers: {
      Authorization: authHeader(),
      Accept: 'application/json'
    }
  });

  return data.value || [];
}

module.exports = { query, queryMultiple, listCompanies };
