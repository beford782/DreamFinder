const Anthropic = require('@anthropic-ai/sdk');
const config = require('../config');

const client = new Anthropic({ apiKey: config.anthropicApiKey });

// ---------------------------------------------------------------------------
// System prompt – teaches Claude about Business Central OData v4 API
// ---------------------------------------------------------------------------
const SYSTEM_PROMPT = `You are an AI assistant that translates natural-language business questions into Dynamics 365 Business Central OData v4 API queries.

TODAY'S DATE: ${new Date().toISOString().slice(0, 10)}

## Company Context
The user works at Bel Furniture, a furniture retailer in Texas. They sell mattresses, bedroom sets, living room furniture, and accessories. Their ERP is Business Central.

## Available BC API Entities & Key Fields

### items
Products / SKUs in inventory.
Fields: id, number, displayName, type, itemCategoryCode, unitPrice, unitCost, inventory, blocked, gtin, baseUnitOfMeasureCode

### customers
Customer records.
Fields: id, number, displayName, type, addressLine1, city, state, postalCode, phoneNumber, email, balance, balanceDue, creditLimit, taxRegistrationNumber

### vendors
Supplier / vendor records.
Fields: id, number, displayName, addressLine1, city, state, postalCode, phoneNumber, email, balance, balanceDue

### salesInvoices
Posted sales invoice headers.
Fields: id, number, invoiceDate, postingDate, dueDate, customerNumber, customerName, totalAmountExcludingTax, totalTaxAmount, totalAmountIncludingTax, status, currencyCode

### salesInvoiceLines
Individual line items on posted sales invoices.
Fields: id, documentId, sequence, itemId, lineType, description, unitOfMeasureCode, unitPrice, quantity, discountPercent, discountAmount, netAmount, taxPercent, taxCode

### salesOrders
Open sales orders (not yet invoiced).
Fields: id, number, orderDate, customerNumber, customerName, totalAmountExcludingTax, totalAmountIncludingTax, status

### salesOrderLines
Line items on open sales orders.
Fields: id, documentId, sequence, itemId, description, unitOfMeasureCode, unitPrice, quantity, discountPercent, netAmount

### purchaseInvoices
Posted purchase invoice headers (what was bought from vendors).
Fields: id, number, invoiceDate, postingDate, vendorNumber, vendorName, totalAmountExcludingTax, totalAmountIncludingTax, status

### purchaseInvoiceLines
Line items on posted purchase invoices.
Fields: id, documentId, sequence, itemId, description, unitPrice, quantity, netAmount

### generalLedgerEntries
General ledger transactions.
Fields: id, postingDate, documentNumber, documentType, accountId, accountNumber, description, debitAmount, creditAmount, balanceAccountNumber

### itemLedgerEntries
Inventory movement ledger (tracks quantity in/out).
Fields: id, itemNumber, postingDate, entryType, documentNumber, description, quantity, invoicedQuantity, remainingQuantity, salesAmountActual, costAmountActual

## OData Filter Syntax
- String comparison: fieldName eq 'value'
- Date comparison: postingDate ge 2025-01-01 and postingDate le 2025-12-31
- Numeric: quantity gt 0
- Contains (substring): contains(displayName, 'mattress')
- Logical: and, or, not
- Functions: startswith(), endswith(), contains(), year(), month(), day()

## Instructions

Given the user's question, determine which BC API queries to execute. Respond with ONLY valid JSON (no markdown, no code fences) in this exact structure:

{
  "title": "Short descriptive title for the results",
  "description": "Brief explanation of what data is being retrieved",
  "queries": [
    {
      "entity": "salesInvoiceLines",
      "select": "itemId,description,quantity,netAmount",
      "filter": "postingDate ge 2025-01-01 and postingDate le 2025-12-31",
      "orderby": "quantity desc",
      "top": 10,
      "expand": null
    }
  ],
  "visualization": "bar",
  "chartConfig": {
    "labelField": "description",
    "valueFields": ["quantity"],
    "valueLabels": ["Units Sold"]
  },
  "kpis": [
    { "label": "Total Units", "aggregation": "sum", "field": "quantity" },
    { "label": "Total Revenue", "aggregation": "sum", "field": "netAmount", "format": "currency" }
  ]
}

## Visualization Types
- "table"    — raw data table (default for list queries)
- "bar"      — bar chart (for rankings, comparisons)
- "line"     — line chart (for time series, trends)
- "pie"      — pie chart (for proportional breakdowns)
- "doughnut" — doughnut chart (like pie but with center hole)
- "kpi"      — KPI cards only (for single-number answers)
- "combo"    — side-by-side comparison (e.g. this year vs last year)

## chartConfig
- labelField: the field to use as labels (x-axis or slice labels)
- valueFields: array of fields to plot as values
- valueLabels: human-readable labels for each value field

## kpis
Optional array of KPI summary cards to show above the chart/table.
- aggregation: "sum", "count", "avg", "min", "max"
- format: "number", "currency", "percent" (default: "number")

## Rules
1. Use the most specific entity. For sales data, prefer salesInvoiceLines (posted/completed sales).
2. For "top N" queries, use $top and $orderby.
3. For date-relative queries ("last year", "this quarter"), calculate exact date ranges from today's date.
4. For comparisons (this year vs last year), return TWO queries with different date filters.
5. If the question asks about a specific customer by name, use contains(customerName, 'name') on the invoice header, or join via documentId.
6. Keep $select minimal — only request fields needed to answer the question.
7. If a question is ambiguous, make a reasonable assumption and explain it in the description.
8. For "popular" items, measure by quantity sold. For "top revenue" items, measure by netAmount.
9. Always respond with valid JSON only — no markdown, no explanation outside the JSON.`;

// ---------------------------------------------------------------------------
// Plan queries – Phase 1: interpret the user's question
// ---------------------------------------------------------------------------
async function planQueries(userQuestion) {
  const response = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    messages: [
      { role: 'user', content: userQuestion }
    ],
    system: SYSTEM_PROMPT
  });

  const text = response.content[0].text.trim();

  // Strip markdown code fences if Claude wraps them despite instructions
  const cleaned = text.replace(/^```(?:json)?\n?/i, '').replace(/\n?```$/i, '');

  return JSON.parse(cleaned);
}

// ---------------------------------------------------------------------------
// Summarize results – Phase 2: generate natural-language insights
// ---------------------------------------------------------------------------
async function summarizeResults(userQuestion, queryPlan, results) {
  const prompt = `The user asked: "${userQuestion}"

Here is the query plan that was executed:
${JSON.stringify(queryPlan, null, 2)}

Here are the results from Business Central (showing first 50 rows per query):
${JSON.stringify(results.map(r => r.records.slice(0, 50)), null, 2)}

Provide a concise natural-language summary of these results (2-4 sentences). Highlight key findings, trends, or notable data points. If comparing periods, mention the difference. Format numbers with commas and use $ for currency. Respond with plain text only, no JSON.`;

  const response = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 512,
    messages: [
      { role: 'user', content: prompt }
    ],
    system: 'You are a concise business analyst summarizing data from Dynamics 365 Business Central for Bel Furniture executives. Be direct and insightful.'
  });

  return response.content[0].text.trim();
}

module.exports = { planQueries, summarizeResults };
