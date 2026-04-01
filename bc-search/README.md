# BC Search — AI-Powered Business Central Query Tool

Ask natural language questions about your Dynamics 365 Business Central data and get instant dashboards with charts, tables, and KPIs.

**Examples:**
- "What were our ten most popular SKUs last year?"
- "Compare Lacks Furniture sales this year to same period last year"
- "Show me total sales by month for the past 12 months"
- "Who are our top 5 customers by revenue?"

---

## Quick Start

```bash
cd bc-search
npm install
cp .env.example .env
# Edit .env with your credentials (see setup below)
npm start
# Open http://localhost:3000
```

---

## Prerequisites

- **Node.js** 18+ installed
- **Anthropic API key** (for Claude) — get one at https://console.anthropic.com
- **Dynamics 365 Business Central** instance with API access
- **Azure AD app registration** (see below)

---

## Azure AD Setup (Business Central API Access)

Follow these steps to get your BC API credentials:

### Step 1: Register an App in Azure AD

1. Go to [Azure Portal](https://portal.azure.com) → **Azure Active Directory** → **App registrations**
2. Click **New registration**
3. Name: `BC AI Search` (or any name you prefer)
4. Supported account types: **Single tenant**
5. Redirect URI: leave blank (not needed for client credentials)
6. Click **Register**
7. Note the **Application (client) ID** → this is your `BC_CLIENT_ID`
8. Note the **Directory (tenant) ID** → this is your `BC_TENANT_ID`

### Step 2: Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `BC Search`
4. Expiration: choose your preference (recommended: 12 months)
5. Click **Add**
6. **Copy the secret Value immediately** (it won't be shown again) → this is your `BC_CLIENT_SECRET`

### Step 3: Grant API Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **Dynamics 365 Business Central**
3. Select **Application permissions**
4. Check **API.ReadWrite.All**
5. Click **Add permissions**
6. Click **Grant admin consent for [your tenant]** (requires admin role)

### Step 4: Find Your Environment & Company

**Environment name:**
- Open Business Central → Settings (gear icon) → **About**
- Look for "Environment" — typically `production` or `sandbox`
- This is your `BC_ENVIRONMENT`

**Company ID:**
- Option A: After setting up the other credentials, run `npm start` and click **Test Connection** — it will list all companies with their IDs
- Option B: In Business Central, open the URL bar — the company ID is in the URL: `.../companies({GUID})/...`
- This is your `BC_COMPANY_ID`

### Step 5: Configure .env

```bash
cp .env.example .env
```

Fill in all values:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
BC_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
BC_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
BC_CLIENT_SECRET=your-secret-value
BC_ENVIRONMENT=production
BC_COMPANY_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PORT=3000
```

---

## How It Works

```
You type a question
    ↓
Express server receives it
    ↓
Claude AI interprets the question and generates
Business Central OData API query plan
    ↓
Server executes the BC API queries
    ↓
Claude summarizes the results
    ↓
Frontend renders dashboard (charts, tables, KPIs)
```

### Architecture

```
bc-search/
├── server/
│   ├── index.js              # Express server
│   ├── config.js             # Environment config
│   ├── routes/
│   │   ├── query.js          # POST /api/query
│   │   └── auth.js           # GET /api/auth/test
│   └── services/
│       ├── claude.js          # Claude API (query planning + summarization)
│       └── businessCentral.js # BC OData client (OAuth2 + queries)
├── public/
│   ├── index.html            # Frontend
│   ├── css/styles.css        # Dark navy/gold theme
│   └── js/
│       ├── app.js            # Search, history, UI logic
│       ├── dashboard.js      # Chart.js charts, tables, KPIs
│       └── export.js         # CSV & PDF export
├── .env.example
├── package.json
└── README.md
```

---

## Features

- **Natural language queries** — ask anything in plain English
- **AI-powered** — Claude interprets your question and builds the right API calls
- **Auto-visualization** — charts, tables, and KPI cards chosen automatically
- **Multiple chart types** — bar, line, pie, doughnut, combo comparisons
- **Sortable tables** — click column headers to sort, type to filter
- **Export** — download results as CSV or PDF
- **Query history** — recent queries saved locally for quick re-use
- **Connection test** — verify your BC credentials with one click
- **Keyboard shortcut** — Ctrl+K / Cmd+K to focus search bar
- **Dark theme** — easy on the eyes, matches Bel Furniture branding

---

## Supported Query Types

| Query Type | Example |
|---|---|
| Top/Bottom N | "Top 10 selling items last quarter" |
| Trends | "Monthly sales trend for the past year" |
| Comparisons | "Compare Q1 this year to Q1 last year" |
| Customer analysis | "Our biggest customers by revenue" |
| Inventory | "Current inventory levels by category" |
| Vendor analysis | "How much did we spend with each vendor this year?" |
| Specific lookups | "Show me all invoices for customer ABC Furniture" |
| Outstanding balances | "Customers with balances over $10,000" |
| GL analysis | "General ledger entries for account 4000 this month" |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Missing required environment variables" | Ensure `.env` exists and all values are filled in |
| "BC authentication failed" | Double-check `BC_CLIENT_ID`, `BC_CLIENT_SECRET`, `BC_TENANT_ID` |
| "Access denied" | Ensure admin consent is granted for API permissions in Azure AD |
| "Entity not found" | Your BC environment may not expose all standard API entities |
| "Claude API authentication failed" | Check your `ANTHROPIC_API_KEY` |
| No data returned | Try a broader question; check that your BC has data for the time period |

---

## Development

```bash
# Start with auto-reload (Node 18+)
npm run dev
```

The server watches for file changes and restarts automatically.
