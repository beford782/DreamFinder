const express = require('express');
const cors = require('cors');
const path = require('path');
const config = require('./config');

const app = express();

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'public')));

// ---------------------------------------------------------------------------
// API Routes
// ---------------------------------------------------------------------------
app.use('/api/query', require('./routes/query'));
app.use('/api/auth', require('./routes/auth'));

// ---------------------------------------------------------------------------
// SPA fallback – serve index.html for any non-API route
// ---------------------------------------------------------------------------
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

// ---------------------------------------------------------------------------
// Global error handler
// ---------------------------------------------------------------------------
app.use((err, req, res, _next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
app.listen(config.port, () => {
  console.log(`\n  BC Search running at http://localhost:${config.port}\n`);
});
