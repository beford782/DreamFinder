/* ============================================
   App – Search logic, history, event binding
   ============================================ */

(function() {
  'use strict';

  // ---------------------------------------------------------------------------
  // DOM refs
  // ---------------------------------------------------------------------------
  const searchForm     = document.getElementById('searchForm');
  const searchInput    = document.getElementById('searchInput');
  const searchBtn      = document.getElementById('searchBtn');
  const searchSection  = document.getElementById('searchSection');
  const loading        = document.getElementById('loading');
  const errorState     = document.getElementById('errorState');
  const errorMessage   = document.getElementById('errorMessage');
  const errorRetry     = document.getElementById('errorRetry');
  const dashboard      = document.getElementById('dashboard');
  const historyToggle  = document.getElementById('historyToggle');
  const historySidebar  = document.getElementById('historySidebar');
  const historyList    = document.getElementById('historyList');
  const clearHistory   = document.getElementById('clearHistory');
  const testConnection = document.getElementById('testConnection');
  const connectionModal = document.getElementById('connectionModal');
  const connectionResult = document.getElementById('connectionResult');
  const closeModal     = document.getElementById('closeModal');
  const exportCsvBtn   = document.getElementById('exportCsv');
  const exportPdfBtn   = document.getElementById('exportPdf');
  const newQueryBtn    = document.getElementById('newQuery');
  const chips          = document.querySelectorAll('.chip');

  let lastQuery = '';

  // ---------------------------------------------------------------------------
  // Search submission
  // ---------------------------------------------------------------------------
  searchForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;
    executeQuery(query);
  });

  async function executeQuery(query) {
    lastQuery = query;
    searchInput.value = query;

    // UI state: loading
    searchSection.classList.add('compact');
    loading.classList.remove('hidden');
    errorState.classList.add('hidden');
    dashboard.classList.add('hidden');
    searchBtn.disabled = true;

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Server error');
      }

      // Save to history
      saveToHistory(query);

      // Render
      setExportData(data);
      renderDashboard(data);

      // Hide loading
      loading.classList.add('hidden');
      searchBtn.disabled = false;

    } catch (err) {
      loading.classList.add('hidden');
      searchBtn.disabled = false;
      showError(err.message || 'Failed to process query.');
    }
  }

  // ---------------------------------------------------------------------------
  // Error handling
  // ---------------------------------------------------------------------------
  function showError(msg) {
    errorMessage.textContent = msg;
    errorState.classList.remove('hidden');
    dashboard.classList.add('hidden');
  }

  errorRetry.addEventListener('click', function() {
    if (lastQuery) executeQuery(lastQuery);
  });

  // ---------------------------------------------------------------------------
  // New query
  // ---------------------------------------------------------------------------
  newQueryBtn.addEventListener('click', function() {
    searchSection.classList.remove('compact');
    dashboard.classList.add('hidden');
    errorState.classList.add('hidden');
    searchInput.value = '';
    searchInput.focus();
  });

  // ---------------------------------------------------------------------------
  // Suggested query chips
  // ---------------------------------------------------------------------------
  chips.forEach(chip => {
    chip.addEventListener('click', function() {
      const query = this.dataset.query;
      searchInput.value = query;
      executeQuery(query);
    });
  });

  // ---------------------------------------------------------------------------
  // Query History (localStorage)
  // ---------------------------------------------------------------------------
  const HISTORY_KEY = 'bc_search_history';
  const MAX_HISTORY = 50;

  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch {
      return [];
    }
  }

  function saveToHistory(query) {
    const history = loadHistory();
    // Remove duplicate if exists
    const idx = history.findIndex(h => h.query === query);
    if (idx !== -1) history.splice(idx, 1);
    // Add to front
    history.unshift({ query, timestamp: Date.now() });
    // Trim
    if (history.length > MAX_HISTORY) history.length = MAX_HISTORY;
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory();
  }

  function renderHistory() {
    const history = loadHistory();
    historyList.innerHTML = history.map(h => {
      const time = new Date(h.timestamp).toLocaleString();
      return `<li data-query="${escapeAttr(h.query)}">${escapeHtml(h.query)}<span class="history-time">${time}</span></li>`;
    }).join('');

    historyList.querySelectorAll('li').forEach(li => {
      li.addEventListener('click', function() {
        executeQuery(this.dataset.query);
      });
    });
  }

  historyToggle.addEventListener('click', function() {
    historySidebar.classList.toggle('hidden');
    renderHistory();
  });

  clearHistory.addEventListener('click', function() {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
  });

  // ---------------------------------------------------------------------------
  // Connection test
  // ---------------------------------------------------------------------------
  testConnection.addEventListener('click', async function() {
    connectionResult.textContent = 'Testing connection...';
    connectionModal.classList.remove('hidden');

    try {
      const res = await fetch('/api/auth/test');
      const data = await res.json();

      if (data.success) {
        let text = '✓ ' + data.message + '\n\nCompanies:\n';
        data.companies.forEach(c => {
          text += `  • ${c.name} (${c.id})\n`;
        });
        connectionResult.textContent = text;
      } else {
        connectionResult.textContent = '✗ ' + data.message + '\n\n' + data.detail;
      }
    } catch (err) {
      connectionResult.textContent = '✗ Could not reach server.\n' + err.message;
    }
  });

  closeModal.addEventListener('click', function() {
    connectionModal.classList.add('hidden');
  });

  connectionModal.addEventListener('click', function(e) {
    if (e.target === connectionModal) connectionModal.classList.add('hidden');
  });

  // ---------------------------------------------------------------------------
  // Export buttons
  // ---------------------------------------------------------------------------
  exportCsvBtn.addEventListener('click', exportCSV);
  exportPdfBtn.addEventListener('click', exportPDF);

  // ---------------------------------------------------------------------------
  // Keyboard shortcut: Ctrl+K or Cmd+K to focus search
  // ---------------------------------------------------------------------------
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
    // Escape to close modal
    if (e.key === 'Escape') {
      connectionModal.classList.add('hidden');
    }
  });

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  function escapeAttr(str) {
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // Initial focus
  searchInput.focus();

})();
