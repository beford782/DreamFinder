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
- **Business Central on-premises** instance with OData services enabled
- **BC user account** with a Web Service Access Key

---

## Setup (On-Premises Business Central)

### Step 1: Get Your Anthropic API Key

1. Go to console.anthropic.com → API Keys → Create Key
2. Copy the key (starts with `sk-ant-...`)

### Step 2: Find Your BC OData URL

Your BC server exposes OData at a URL like:

```
https://your-server:7048/BC/ODataV4
```

The format is: `https://{server}:{port}/{instance}/ODataV4`

- **server** — your BC server hostname or IP
- **port** — typically 7048 (OData port)
- **instance** — your BC instance name (e.g. `BC`, `BC250`, `NAV`, etc.)

Ask your BC admin (Jack/Greg at Enhanced Systems) if you're unsure.

### Step 3: Get Your Web Service Access Key

If you already have one, great. If not:

1. Open Business Central
2. Go to your **User Settings** or search for "User Setup"
3. Find **Web Service Access Key**
4. If empty, generate a new one
5. Copy the key

Your **username** is typically in `DOMAIN\username` format.

### Step 4: Find Your Company Name

In Business Central, look at the top bar — it shows your company name. Or:
- Run the app and click **Test Connection** — it will list all companies

### Step 5: Configure .env

```bash
cp .env.example .env
```

Fill in all values:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
BC_SERVER_URL=https://your-server:7048/BC/ODataV4
BC_USERNAME=DOMAIN\yourusername
BC_WEB_SERVICE_KEY=your-web-service-access-key
BC_COMPANY_NAME=Your Company Name
PORT=3000
```

**Optional:** If your BC server uses a self-signed SSL certificate, add:
```
BC_ALLOW_SELF_SIGNED=true
```

### Step 6: Run

```bash
npm start
```

Open http://localhost:3000 and click **Test Connection** to verify everything works.

---

## What to Ask Your BC Admin

If you need help from your admin (Enhanced Systems), ask them for:

1. **The OData URL** — the base URL to reach BC's OData v4 endpoint
2. **Confirm OData is enabled** — OData services must be turned on in BC server configuration
3. **Your username and Web Service Access Key** — or confirmation that your existing key is valid
4. **Company name** — the exact company name as it appears in BC

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
Server executes the BC OData queries
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
│       └── businessCentral.js # BC OData client (Basic Auth + queries)
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
| "Invalid credentials" | Double-check `BC_USERNAME` and `BC_WEB_SERVICE_KEY` |
| "OData endpoint not found" | Check `BC_SERVER_URL` — should end with `/ODataV4` |
| "Connection refused" | BC server may be down or port is wrong |
| "SSL certificate error" | Add `BC_ALLOW_SELF_SIGNED=true` to `.env` |
| "Entity not found" | The entity may need to be published as a web service in BC |
| "Claude API authentication failed" | Check your `ANTHROPIC_API_KEY` |
| No data returned | Try a broader question; check that your BC has data for the time period |

---

## Development

```bash
# Start with auto-reload (Node 18+)
npm run dev
```

The server watches for file changes and restarts automatically.
