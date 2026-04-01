const express = require('express');
const router = express.Router();
const claude = require('../services/claude');
const bc = require('../services/businessCentral');

/**
 * POST /api/query
 * Body: { question: string }
 *
 * 1. Send the question to Claude to get a query plan
 * 2. Execute the BC OData queries
 * 3. Send results back to Claude for summarization
 * 4. Return everything to the frontend
 */
router.post('/', async (req, res) => {
  const { question } = req.body;

  if (!question || typeof question !== 'string' || question.trim().length === 0) {
    return res.status(400).json({ error: 'Please provide a question.' });
  }

  try {
    // Phase 1: Claude interprets the question and plans BC API queries
    const plan = await claude.planQueries(question.trim());

    if (!plan.queries || plan.queries.length === 0) {
      return res.json({
        title: plan.title || 'No Data',
        description: plan.description || 'Could not determine which data to fetch.',
        visualization: 'kpi',
        data: [],
        columns: [],
        kpis: [],
        summary: 'I wasn\'t able to determine which Business Central data to query for this question. Try rephrasing or being more specific.'
      });
    }

    // Phase 2: Execute all BC OData queries in parallel
    const results = await bc.queryMultiple(plan.queries);

    // Merge results for multi-query plans (e.g. comparisons)
    const allData = [];
    const queryLabels = plan.queries.map((q, i) =>
      plan.chartConfig && plan.chartConfig.valueLabels
        ? plan.chartConfig.valueLabels[i] || `Dataset ${i + 1}`
        : `Dataset ${i + 1}`
    );

    results.forEach((result, i) => {
      result.records.forEach(record => {
        if (results.length > 1) {
          record._datasetIndex = i;
          record._datasetLabel = queryLabels[i];
        }
        allData.push(record);
      });
    });

    // Determine columns from first non-empty result
    let columns = [];
    for (const result of results) {
      if (result.records.length > 0) {
        columns = Object.keys(result.records[0])
          .filter(k => !k.startsWith('@') && !k.startsWith('_'))
          .map(key => ({
            key,
            label: formatColumnLabel(key)
          }));
        break;
      }
    }

    // Compute KPIs
    const kpis = (plan.kpis || []).map(kpi => {
      const values = allData
        .filter(r => r._datasetIndex === undefined || r._datasetIndex === 0)
        .map(r => parseFloat(r[kpi.field]) || 0);

      let value = 0;
      switch (kpi.aggregation) {
        case 'sum':   value = values.reduce((a, b) => a + b, 0); break;
        case 'count': value = values.length; break;
        case 'avg':   value = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0; break;
        case 'min':   value = values.length ? Math.min(...values) : 0; break;
        case 'max':   value = values.length ? Math.max(...values) : 0; break;
      }

      return {
        label: kpi.label,
        value,
        format: kpi.format || 'number'
      };
    });

    // Phase 3: Claude summarizes the results
    let summary = '';
    try {
      summary = await claude.summarizeResults(question, plan, results);
    } catch (err) {
      console.error('Summarization failed (non-fatal):', err.message);
      summary = '';
    }

    res.json({
      title: plan.title,
      description: plan.description,
      visualization: plan.visualization || 'table',
      chartConfig: plan.chartConfig || null,
      data: allData,
      columns,
      kpis,
      summary,
      queryCount: results.length,
      totalRecords: allData.length
    });

  } catch (err) {
    console.error('Query error:', err);

    // Provide user-friendly error messages
    if (err.message && err.message.includes('JSON')) {
      return res.status(500).json({ error: 'AI could not parse the query. Try rephrasing your question.' });
    }
    if (err.response && err.response.status === 401) {
      return res.status(500).json({ error: 'Business Central authentication failed. Check your Azure AD credentials in .env.' });
    }
    if (err.response && err.response.status === 404) {
      return res.status(500).json({ error: 'Business Central entity not found. The requested data may not be available in your environment.' });
    }
    if (err.status === 401 || (err.error && err.error.type === 'authentication_error')) {
      return res.status(500).json({ error: 'Claude API authentication failed. Check your ANTHROPIC_API_KEY in .env.' });
    }

    res.status(500).json({ error: 'Something went wrong processing your query. Please try again.' });
  }
});

/**
 * Convert camelCase field names to human-readable labels.
 */
function formatColumnLabel(key) {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, s => s.toUpperCase())
    .trim();
}

module.exports = router;
