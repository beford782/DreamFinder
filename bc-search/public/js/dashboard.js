/* ============================================
   Dashboard – Charts, Tables, KPIs
   ============================================ */

// Chart.js color palette (gold-based)
const CHART_COLORS = [
  '#d4a84b', '#5b9cf5', '#4caf7d', '#e8c87a', '#e05555',
  '#9b7dd4', '#5cc9c9', '#f0975b', '#b08a30', '#7baaf7'
];

const ROWS_PER_PAGE = 25;

let currentChart = null;
let tableState = {
  data: [],
  columns: [],
  sortKey: null,
  sortDir: 'asc',
  filterText: '',
  page: 0
};

// ---------------------------------------------------------------------------
// Render full dashboard from API response
// ---------------------------------------------------------------------------
function renderDashboard(response) {
  // Title & description
  document.getElementById('resultsTitle').textContent = response.title || 'Results';
  document.getElementById('resultsDescription').textContent = response.description || '';

  // AI Summary
  const summaryCard = document.getElementById('summaryCard');
  const summaryText = document.getElementById('summaryText');
  if (response.summary) {
    summaryText.textContent = response.summary;
    summaryCard.classList.remove('hidden');
  } else {
    summaryCard.classList.add('hidden');
  }

  // KPIs
  renderKPIs(response.kpis || []);

  // Chart
  const viz = response.visualization || 'table';
  if (viz !== 'table' && viz !== 'kpi' && response.data.length > 0) {
    renderChart(response);
  } else {
    document.getElementById('chartContainer').classList.add('hidden');
    destroyChart();
  }

  // Table (always show if there's data)
  if (response.data.length > 0 && response.columns.length > 0) {
    initTable(response.data, response.columns);
    document.getElementById('tableContainer').classList.remove('hidden');
  } else {
    document.getElementById('tableContainer').classList.add('hidden');
  }

  // Footer
  document.getElementById('resultsFooter').textContent =
    `${response.totalRecords || response.data.length} record(s) returned`;

  // Show dashboard
  document.getElementById('dashboard').classList.remove('hidden');
}

// ---------------------------------------------------------------------------
// KPI Cards
// ---------------------------------------------------------------------------
function renderKPIs(kpis) {
  const container = document.getElementById('kpiContainer');
  if (!kpis || kpis.length === 0) {
    container.classList.add('hidden');
    container.innerHTML = '';
    return;
  }

  container.innerHTML = kpis.map(kpi => `
    <div class="kpi-card">
      <div class="kpi-label">${escapeHtml(kpi.label)}</div>
      <div class="kpi-value">${formatKPIValue(kpi.value, kpi.format)}</div>
    </div>
  `).join('');

  container.classList.remove('hidden');
}

function formatKPIValue(value, format) {
  switch (format) {
    case 'currency':
      return '$' + Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    case 'percent':
      return Number(value).toFixed(1) + '%';
    default:
      return Number(value).toLocaleString('en-US');
  }
}

// ---------------------------------------------------------------------------
// Chart.js rendering
// ---------------------------------------------------------------------------
function destroyChart() {
  if (currentChart) {
    currentChart.destroy();
    currentChart = null;
  }
}

function renderChart(response) {
  const container = document.getElementById('chartContainer');
  container.classList.remove('hidden');
  destroyChart();

  const canvas = document.getElementById('resultChart');
  const ctx = canvas.getContext('2d');

  const viz = response.visualization;
  const cfg = response.chartConfig || {};
  const data = response.data;

  // Determine if multi-dataset (comparison)
  const hasMultipleDatasets = data.some(d => d._datasetIndex !== undefined);

  let chartConfig;

  if (viz === 'combo' || (hasMultipleDatasets && viz === 'bar')) {
    chartConfig = buildComparisonChart(data, cfg, viz);
  } else if (viz === 'pie' || viz === 'doughnut') {
    chartConfig = buildPieChart(data, cfg, viz);
  } else if (viz === 'line') {
    chartConfig = buildLineChart(data, cfg);
  } else {
    chartConfig = buildBarChart(data, cfg);
  }

  currentChart = new Chart(ctx, chartConfig);
}

function buildBarChart(data, cfg) {
  const labelField = cfg.labelField || guessLabelField(data);
  const valueField = (cfg.valueFields && cfg.valueFields[0]) || guessValueField(data);
  const valueLabel = (cfg.valueLabels && cfg.valueLabels[0]) || valueField;

  return {
    type: 'bar',
    data: {
      labels: data.map(d => truncateLabel(d[labelField])),
      datasets: [{
        label: valueLabel,
        data: data.map(d => parseFloat(d[valueField]) || 0),
        backgroundColor: CHART_COLORS[0],
        borderColor: CHART_COLORS[0],
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: chartOptions()
  };
}

function buildLineChart(data, cfg) {
  const labelField = cfg.labelField || guessLabelField(data);
  const valueField = (cfg.valueFields && cfg.valueFields[0]) || guessValueField(data);
  const valueLabel = (cfg.valueLabels && cfg.valueLabels[0]) || valueField;

  return {
    type: 'line',
    data: {
      labels: data.map(d => truncateLabel(d[labelField])),
      datasets: [{
        label: valueLabel,
        data: data.map(d => parseFloat(d[valueField]) || 0),
        borderColor: CHART_COLORS[0],
        backgroundColor: CHART_COLORS[0] + '33',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointBackgroundColor: CHART_COLORS[0]
      }]
    },
    options: chartOptions()
  };
}

function buildPieChart(data, cfg, type) {
  const labelField = cfg.labelField || guessLabelField(data);
  const valueField = (cfg.valueFields && cfg.valueFields[0]) || guessValueField(data);

  return {
    type: type,
    data: {
      labels: data.map(d => truncateLabel(d[labelField])),
      datasets: [{
        data: data.map(d => parseFloat(d[valueField]) || 0),
        backgroundColor: CHART_COLORS.slice(0, data.length),
        borderWidth: 2,
        borderColor: '#0b1929'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#f0eee8', font: { size: 12 }, padding: 12 }
        },
        tooltip: tooltipConfig()
      }
    }
  };
}

function buildComparisonChart(data, cfg, viz) {
  const labelField = cfg.labelField || guessLabelField(data);

  // Group by dataset
  const groups = {};
  data.forEach(d => {
    const idx = d._datasetIndex || 0;
    if (!groups[idx]) groups[idx] = { label: d._datasetLabel || `Dataset ${idx + 1}`, records: [] };
    groups[idx].records.push(d);
  });

  const valueField = (cfg.valueFields && cfg.valueFields[0]) || guessValueField(data);
  const datasets = Object.values(groups).map((g, i) => ({
    label: g.label,
    data: g.records.map(d => parseFloat(d[valueField]) || 0),
    backgroundColor: CHART_COLORS[i],
    borderColor: CHART_COLORS[i],
    borderWidth: 1,
    borderRadius: 4
  }));

  // Use labels from the first dataset
  const firstGroup = Object.values(groups)[0];
  const labels = firstGroup.records.map(d => truncateLabel(d[labelField]));

  return {
    type: viz === 'combo' ? 'bar' : 'bar',
    data: { labels, datasets },
    options: chartOptions()
  };
}

function chartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: true,
    interaction: { intersect: false, mode: 'index' },
    plugins: {
      legend: { labels: { color: '#f0eee8', font: { size: 12 } } },
      tooltip: tooltipConfig()
    },
    scales: {
      x: {
        ticks: { color: '#a0a0a0', font: { size: 11 }, maxRotation: 45 },
        grid: { color: 'rgba(212, 168, 75, 0.06)' }
      },
      y: {
        ticks: { color: '#a0a0a0', font: { size: 11 } },
        grid: { color: 'rgba(212, 168, 75, 0.06)' },
        beginAtZero: true
      }
    }
  };
}

function tooltipConfig() {
  return {
    backgroundColor: '#162b47',
    titleColor: '#f0eee8',
    bodyColor: '#f0eee8',
    borderColor: 'rgba(212,168,75,0.3)',
    borderWidth: 1,
    padding: 10,
    callbacks: {
      label: function(ctx) {
        let val = ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.parsed;
        if (typeof val === 'number') val = val.toLocaleString('en-US');
        return `${ctx.dataset.label}: ${val}`;
      }
    }
  };
}

// ---------------------------------------------------------------------------
// Data Table
// ---------------------------------------------------------------------------
function initTable(data, columns) {
  tableState.data = data;
  tableState.columns = columns;
  tableState.sortKey = null;
  tableState.sortDir = 'asc';
  tableState.filterText = '';
  tableState.page = 0;

  // Build header
  const thead = document.getElementById('tableHead');
  thead.innerHTML = '<tr>' + columns.map(col =>
    `<th data-key="${col.key}">${escapeHtml(col.label)} <span class="sort-arrow">↕</span></th>`
  ).join('') + '</tr>';

  // Bind sort
  thead.querySelectorAll('th').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      if (tableState.sortKey === key) {
        tableState.sortDir = tableState.sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        tableState.sortKey = key;
        tableState.sortDir = 'asc';
      }
      tableState.page = 0;
      renderTableBody();
      updateSortIndicators();
    });
  });

  // Bind filter
  const filterInput = document.getElementById('tableFilter');
  filterInput.value = '';
  filterInput.oninput = () => {
    tableState.filterText = filterInput.value.toLowerCase();
    tableState.page = 0;
    renderTableBody();
  };

  renderTableBody();
}

function renderTableBody() {
  let filtered = tableState.data;

  // Filter
  if (tableState.filterText) {
    filtered = filtered.filter(row =>
      tableState.columns.some(col =>
        String(row[col.key] || '').toLowerCase().includes(tableState.filterText)
      )
    );
  }

  // Sort
  if (tableState.sortKey) {
    const key = tableState.sortKey;
    const dir = tableState.sortDir === 'asc' ? 1 : -1;
    filtered.sort((a, b) => {
      let va = a[key], vb = b[key];
      const na = parseFloat(va), nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir;
      return String(va || '').localeCompare(String(vb || '')) * dir;
    });
  }

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / ROWS_PER_PAGE));
  tableState.page = Math.min(tableState.page, totalPages - 1);
  const start = tableState.page * ROWS_PER_PAGE;
  const pageData = filtered.slice(start, start + ROWS_PER_PAGE);

  // Render rows
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = pageData.map(row =>
    '<tr>' + tableState.columns.map(col => {
      const val = row[col.key];
      const isNum = typeof val === 'number' || (val !== null && val !== undefined && !isNaN(parseFloat(val)) && String(val).trim() === String(parseFloat(val)));
      const display = formatCellValue(val);
      return `<td class="${isNum ? 'num' : ''}">${escapeHtml(display)}</td>`;
    }).join('') + '</tr>'
  ).join('');

  // Row count
  document.getElementById('rowCount').textContent = `${filtered.length} row(s)`;

  // Pagination controls
  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const container = document.getElementById('tablePagination');
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = `<button class="page-btn" ${tableState.page === 0 ? 'disabled' : ''} data-page="${tableState.page - 1}">← Prev</button>`;

  for (let i = 0; i < totalPages; i++) {
    if (totalPages > 7 && i > 1 && i < totalPages - 2 && Math.abs(i - tableState.page) > 1) {
      if (i === 2 || i === totalPages - 3) html += '<span style="color: var(--cream-dim); font-size: 12px;">...</span>';
      continue;
    }
    html += `<button class="page-btn ${i === tableState.page ? 'active' : ''}" data-page="${i}">${i + 1}</button>`;
  }

  html += `<button class="page-btn" ${tableState.page >= totalPages - 1 ? 'disabled' : ''} data-page="${tableState.page + 1}">Next →</button>`;

  container.innerHTML = html;
  container.querySelectorAll('.page-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.disabled) return;
      tableState.page = parseInt(btn.dataset.page, 10);
      renderTableBody();
    });
  });
}

function updateSortIndicators() {
  document.querySelectorAll('#tableHead th').forEach(th => {
    const arrow = th.querySelector('.sort-arrow');
    if (th.dataset.key === tableState.sortKey) {
      th.classList.add('sorted');
      arrow.textContent = tableState.sortDir === 'asc' ? '↑' : '↓';
    } else {
      th.classList.remove('sorted');
      arrow.textContent = '↕';
    }
  });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function guessLabelField(data) {
  if (!data.length) return '';
  const keys = Object.keys(data[0]).filter(k => !k.startsWith('@') && !k.startsWith('_'));
  const stringKeys = keys.filter(k => typeof data[0][k] === 'string');
  // Prefer displayName, description, name, customerName, etc.
  const preferred = ['displayName', 'description', 'name', 'customerName', 'vendorName', 'itemNumber', 'number'];
  for (const p of preferred) {
    if (stringKeys.includes(p)) return p;
  }
  return stringKeys[0] || keys[0];
}

function guessValueField(data) {
  if (!data.length) return '';
  const keys = Object.keys(data[0]).filter(k => !k.startsWith('@') && !k.startsWith('_'));
  const numKeys = keys.filter(k => typeof data[0][k] === 'number' || !isNaN(parseFloat(data[0][k])));
  const preferred = ['netAmount', 'totalAmountIncludingTax', 'totalAmountExcludingTax', 'quantity', 'balance', 'inventory', 'salesAmountActual'];
  for (const p of preferred) {
    if (numKeys.includes(p)) return p;
  }
  return numKeys[0] || keys[keys.length - 1];
}

function truncateLabel(val, max) {
  max = max || 30;
  const s = String(val || '');
  return s.length > max ? s.slice(0, max - 1) + '…' : s;
}

function formatCellValue(val) {
  if (val === null || val === undefined) return '';
  if (typeof val === 'number') return val.toLocaleString('en-US');
  return String(val);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
