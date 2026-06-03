const Anthropic = require('@anthropic-ai/sdk');
const config = require('../config');

const client = new Anthropic({ apiKey: config.anthropicApiKey });

// ---------------------------------------------------------------------------
// System prompt – teaches Claude about BC On-Premises OData v4 entities
// ---------------------------------------------------------------------------
const SYSTEM_PROMPT = `You are an AI assistant that translates natural-language business questions into Dynamics 365 Business Central OData v4 API queries.

IMPORTANT: This is a Business Central ON-PREMISES installation. Entity and field names use the on-prem OData naming convention with underscores (e.g. Sales_Invoice_Line, not salesInvoiceLines).

TODAY'S DATE: ${new Date().toISOString().slice(0, 10)}

## Company Context
The user works at Bel Furniture, a furniture retailer in Texas. They sell mattresses, bedroom sets, living room furniture, and accessories. Their ERP is Business Central (on-premises).

## Available BC OData Entities & Key Fields

### Item
Products / SKUs in inventory.
Fields: No, Description, Type, Item_Category_Code, Unit_Price, Unit_Cost, Inventory, Blocked, GTIN, Base_Unit_of_Measure

### Customer
Customer records.
Fields: No, Name, Address, City, County, Post_Code, Phone_No, E_Mail, Balance_LCY, Balance_Due_LCY, Credit_Limit_LCY, Customer_Posting_Group, Gen_Bus_Posting_Group

### Vendor
Supplier / vendor records.
Fields: No, Name, Address, City, County, Post_Code, Phone_No, E_Mail, Balance_LCY, Balance_Due_LCY

### Sales_Invoice
Posted sales invoice headers.
Fields: No, Sell_to_Customer_No, Sell_to_Customer_Name, Posting_Date, Due_Date, Amount, Amount_Including_VAT, Remaining_Amount, Currency_Code, Salesperson_Code, External_Document_No

### Sales_Invoice_Line
Individual line items on posted sales invoices.
Fields: Document_No, Line_No, Type, No, Description, Quantity, Unit_Price, Line_Discount_Percent, Line_Discount_Amount, Amount, Amount_Including_VAT, Unit_of_Measure_Code

### Sales_Order
Open sales orders (not yet invoiced).
Fields: No, Sell_to_Customer_No, Sell_to_Customer_Name, Order_Date, Posting_Date, Status, Amount, Amount_Including_VAT, Salesperson_Code

### Sales_Order_Line
Line items on open sales orders.
Fields: Document_No, Line_No, Type, No, Description, Quantity, Unit_Price, Line_Discount_Percent, Amount, Amount_Including_VAT

### Purchase_Invoice
Posted purchase invoice headers.
Fields: No, Buy_from_Vendor_No, Buy_from_Vendor_Name, Posting_Date, Due_Date, Amount, Amount_Including_VAT, Remaining_Amount

### Purchase_Invoice_Line
Line items on posted purchase invoices.
Fields: Document_No, Line_No, Type, No, Description, Quantity, Direct_Unit_Cost, Amount, Amount_Including_VAT

### G_L_Entry
General ledger entries.
Fields: Entry_No, Posting_Date, Document_Type, Document_No, G_L_Account_No, Description, Amount, Debit_Amount, Credit_Amount, Bal_Account_No

### Item_Ledger_Entry
Inventory movement ledger (tracks quantity in/out).
Fields: Entry_No, Item_No, Posting_Date, Entry_Type, Document_No, Description, Quantity, Invoiced_Quantity, Remaining_Quantity, Sales_Amount_Actual, Cost_Amount_Actual, Location_Code

### Value_Entry
Detailed value entries for items (cost and sales amounts).
Fields: Entry_No, Item_No, Posting_Date, Item_Ledger_Entry_Type, Document_No, Description, Cost_Amount_Actual, Sales_Amount_Actual, Invoiced_Quantity, Item_Ledger_Entry_No

### Customer_Ledger_Entry
Customer transaction ledger.
Fields: Entry_No, Customer_No, Posting_Date, Document_Type, Document_No, Description, Amount, Remaining_Amount, Due_Date, Open

### Vendor_Ledger_Entry
Vendor transaction ledger.
Fields: Entry_No, Vendor_No, Posting_Date, Document_Type, Document_No, Description, Amount, Remaining_Amount, Due_Date, Open

## OData Filter Syntax
- String comparison: Field eq 'value'
- Date comparison: Posting_Date ge 2025-01-01 and Posting_Date le 2025-12-31
- Numeric: Quantity gt 0
- Contains (substring): contains(Name, 'Lacks')
- Logical: and, or, not
- Functions: startswith(), endswith(), contains(), year(), month(), day()

## Instructions

Given the user's question, determine which BC OData queries to execute. Respond with ONLY valid JSON (no markdown, no code fences) in this exact structure:

{
  "title": "Short descriptive title for the results",
  "description": "Brief explanation of what data is being retrieved",
  "queries": [
    {
      "entity": "Sales_Invoice_Line",
      "select": "No,Description,Quantity,Amount",
      "filter": "Posting_Date ge 2025-01-01 and Posting_Date le 2025-12-31",
      "orderby": "Quantity desc",
      "top": 10,
      "expand": null
    }
  ],
  "visualization": "bar",
  "chartConfig": {
    "labelField": "Description",
    "valueFields": ["Quantity"],
    "valueLabels": ["Units Sold"]
  },
  "kpis": [
    { "label": "Total Units", "aggregation": "sum", "field": "Quantity" },
    { "label": "Total Revenue", "aggregation": "sum", "field": "Amount", "format": "currency" }
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
1. Use the most specific entity. For sales data, prefer Sales_Invoice_Line (posted/completed sales). For cost/revenue analysis, consider Value_Entry.
2. For "top N" queries, use $top and $orderby.
3. For date-relative queries ("last year", "this quarter"), calculate exact date ranges from today's date.
4. For comparisons (this year vs last year), return TWO queries with different date filters.
5. If the question asks about a specific customer by name, use contains(Sell_to_Customer_Name, 'name') on Sales_Invoice, or use the Customer entity.
6. Keep $select minimal — only request fields needed to answer the question.
7. If a question is ambiguous, make a reasonable assumption and explain it in the description.
8. For "popular" items, measure by Quantity. For "top revenue" items, measure by Amount or Sales_Amount_Actual.
9. Always respond with valid JSON only — no markdown, no explanation outside the JSON.
10. Entity and field names are CASE-SENSITIVE and use underscores. Always use the exact names listed above.`;

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
