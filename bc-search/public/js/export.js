/* ============================================
   Export – CSV & PDF
   ============================================ */

let lastResponse = null;

function setExportData(response) {
  lastResponse = response;
}

// ---------------------------------------------------------------------------
// CSV Export
// ---------------------------------------------------------------------------
function exportCSV() {
  if (!lastResponse || !lastResponse.data.length) return;

  const columns = lastResponse.columns;
  const data = lastResponse.data;

  // Header row
  const rows = [columns.map(c => c.label).join(',')];

  // Data rows
  data.forEach(row => {
    const line = columns.map(col => {
      let val = row[col.key];
      if (val === null || val === undefined) val = '';
      val = String(val);
      // Escape quotes and wrap in quotes if contains comma/quote/newline
      if (val.includes(',') || val.includes('"') || val.includes('\n')) {
        val = '"' + val.replace(/"/g, '""') + '"';
      }
      return val;
    });
    rows.push(line.join(','));
  });

  const csv = rows.join('\n');
  downloadFile(csv, sanitizeFilename(lastResponse.title) + '.csv', 'text/csv');
}

// ---------------------------------------------------------------------------
// PDF Export (jsPDF + autoTable)
// ---------------------------------------------------------------------------
function exportPDF() {
  if (!lastResponse || !lastResponse.data.length) return;

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });

  const pageWidth = doc.internal.pageSize.getWidth();

  // Title
  doc.setFontSize(16);
  doc.setTextColor(40, 40, 40);
  doc.text(lastResponse.title || 'Report', 40, 40);

  // Description
  if (lastResponse.description) {
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text(lastResponse.description, 40, 58);
  }

  // Date
  doc.setFontSize(9);
  doc.setTextColor(140, 140, 140);
  doc.text('Generated: ' + new Date().toLocaleString(), 40, 74);

  // Summary
  let startY = 90;
  if (lastResponse.summary) {
    doc.setFontSize(10);
    doc.setTextColor(60, 60, 60);
    const lines = doc.splitTextToSize(lastResponse.summary, pageWidth - 80);
    doc.text(lines, 40, startY);
    startY += lines.length * 14 + 10;
  }

  // Chart image (if visible)
  const canvas = document.getElementById('resultChart');
  if (canvas && !document.getElementById('chartContainer').classList.contains('hidden')) {
    try {
      const imgData = canvas.toDataURL('image/png');
      const imgWidth = pageWidth - 80;
      const imgHeight = (canvas.height / canvas.width) * imgWidth;
      doc.addImage(imgData, 'PNG', 40, startY, imgWidth, Math.min(imgHeight, 280));
      startY += Math.min(imgHeight, 280) + 20;
    } catch (e) {
      // Canvas may be tainted, skip chart
    }
  }

  // Table
  const columns = lastResponse.columns;
  const head = [columns.map(c => c.label)];
  const body = lastResponse.data.map(row =>
    columns.map(col => {
      const val = row[col.key];
      if (val === null || val === undefined) return '';
      if (typeof val === 'number') return val.toLocaleString('en-US');
      return String(val);
    })
  );

  // Check if we need a new page for the table
  if (startY > doc.internal.pageSize.getHeight() - 100) {
    doc.addPage();
    startY = 40;
  }

  doc.autoTable({
    head,
    body,
    startY,
    styles: {
      fontSize: 8,
      cellPadding: 4,
      textColor: [40, 40, 40]
    },
    headStyles: {
      fillColor: [18, 34, 64],
      textColor: [240, 238, 232],
      fontStyle: 'bold'
    },
    alternateRowStyles: {
      fillColor: [245, 245, 245]
    },
    margin: { left: 40, right: 40 }
  });

  doc.save(sanitizeFilename(lastResponse.title) + '.pdf');
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function downloadFile(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function sanitizeFilename(str) {
  return (str || 'report')
    .replace(/[^a-zA-Z0-9 _-]/g, '')
    .replace(/\s+/g, '_')
    .slice(0, 60);
}
