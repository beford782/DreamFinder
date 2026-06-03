const httpntlm = require('httpntlm');
const config = require('../config');

// ---------------------------------------------------------------------------
// NTLM request helper (on-premises BC uses Windows/NTLM authentication)
// ---------------------------------------------------------------------------
function ntlmGet(url) {
  const username = config.bc.username;
  const parts = username.split('\\');
  const domain = parts.length > 1 ? parts[0] : '';
  const user = parts.length > 1 ? parts[1] : username;

  return new Promise((resolve, reject) => {
    httpntlm.get({
      url,
      username: user,
      password: config.bc.webServiceKey,
      domain: domain,
      headers: { 'Accept': 'application/json' }
    }, (err, res) => {
      if (err) return reject(err);
      if (res.statusCode === 401) {
        return reject({ response: { status: 401, statusText: 'Unauthorized' } });
      }
      if (res.statusCode === 404) {
        return reject({ response: { status: 404, statusText: 'Not Found' } });
      }
      if (res.statusCode >= 400) {
        return reject({ response: { status: res.statusCode, statusText: res.statusMessage || 'Error' } });
      }
      try {
        resolve(JSON.parse(res.body));
      } catch (e) {
        reject(new Error('Invalid JSON response from BC: ' + res.body.substring(0, 200)));
      }
    });
  });
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

  const params = [];
  if (opts.select)  params.push(`$select=${encodeURIComponent(opts.select)}`);
  if (opts.filter)  params.push(`$filter=${encodeURIComponent(opts.filter)}`);
  if (opts.orderby) params.push(`$orderby=${encodeURIComponent(opts.orderby)}`);
  if (opts.top)     params.push(`$top=${opts.top}`);
  if (opts.expand)  params.push(`$expand=${encodeURIComponent(opts.expand)}`);
  if (opts.count)   params.push('$count=true');

  if (params.length > 0) {
    url += '?' + params.join('&');
  }

  let allRecords = [];
  let nextLink = null;
  let isFirst = true;
  let totalCount = null;

  do {
    const requestUrl = isFirst ? url : nextLink;
    const data = await ntlmGet(requestUrl);

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
  const data = await ntlmGet(`${config.bc.serverUrl}/Company`);
  return data.value || [];
}

module.exports = { query, queryMultiple, listCompanies };
