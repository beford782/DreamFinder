function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    Logger.log('Received: ' + JSON.stringify(data));

    // --- Log to Google Sheet ---
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    sheet.appendRow([
      new Date(),
      data.name || '',
      data.email || '',
      data.phone || '',
      data.dreamCode || '',
      (data.allMatches || []).map(function(m) { return m.name + ' (' + m.matchPct + '%)'; }).join(', '),
      (data.accessories || []).map(function(a) { return a.name; }).join(', ')
    ]);

    // --- Send email with fallback ---
    var toEmail = data.email;
    var subject = 'Your DreamFinder Results from Bel Furniture';
    var firstName = (data.name || 'there').split(' ')[0];

    try {
      // Use client-built HTML if available, otherwise build server-side
      var htmlBody = buildSimpleHtml(data, firstName);

      GmailApp.sendEmail(toEmail, subject, 'Please view in an HTML email client.', {
        htmlBody: htmlBody,
        name: 'Bel Furniture Sleep Team'
      });

    } catch (emailErr) {
      Logger.log('HTML email failed, trying plain text: ' + emailErr.toString());
      var plainBody = 'Hi ' + firstName + ',\n\n'
        + 'Your top match: ' + (data.topMatch || '') + ' (' + (data.matchPct || '') + '% match)\n'
        + 'Sleep profile: ' + (data.sleepProfile || '') + '\n'
        + 'Your discount: ' + (data.discount || 5) + '% OFF\n'
        + 'Discount code: ' + (data.dreamCode || '') + '\n\n'
        + 'Show this email at Bel Furniture to redeem.\n\n'
        + (data.allMatches || []).map(function(m, i) { return (i+1) + '. ' + m.name + ' - ' + m.matchPct + '% match'; }).join('\n');

      GmailApp.sendEmail(toEmail, subject, plainBody, {
        name: 'Bel Furniture Sleep Team'
      });
    }

    return ContentService
      .createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    Logger.log('doPost error: ' + err.toString());
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function buildSimpleHtml(data, firstName) {
  var dreamCode = data.dreamCode || '';
  var matches = (data.allMatches || []).slice(0, 3);
  var accs = (data.accessories || []);

  var matchRows = matches.map(function(m, i) {
    var imgHtml = m.imageUrl ? '<td width="80" style="padding:0;vertical-align:top;"><img src="' + m.imageUrl + '" width="80" height="70" style="display:block;border:0;" alt="' + m.name + '"></td>' : '';
    var label = i === 0 ? '<div style="font-size:9px;color:#c9a84c;text-transform:uppercase;letter-spacing:2px;margin-bottom:2px;">Top Pick</div>' : '';
    var border = i === 0 ? '2px solid #c9a84c' : '1px solid #2a3f5f';
    return '<table width="100%" cellpadding="0" cellspacing="0" style="border:' + border + ';border-radius:8px;overflow:hidden;margin-bottom:8px;background:#1d3352;"><tr>'
      + imgHtml
      + '<td style="padding:10px 12px;vertical-align:middle;">'
      + label
      + '<div style="font-size:14px;font-weight:700;color:#ffffff;">' + m.name + '</div>'
      + '<div style="font-size:11px;color:#a0b0c8;margin-top:2px;">' + m.brand + '</div>'
      + '<div style="font-size:11px;color:#c9a84c;font-weight:600;margin-top:3px;">' + m.matchPct + '% Match</div>'
      + '</td></tr></table>';
  }).join('');

  var accCols = accs.slice(0, 3).map(function(a) {
    var w = Math.floor(100 / Math.min(accs.length, 3));
    var imgHtml = a.imageUrl ? '<img src="' + a.imageUrl + '" width="160" height="60" style="display:block;width:100%;border:0;" alt="' + a.name + '">' : '<div style="height:60px;background:#1a2744;"></div>';
    return '<td width="' + w + '%" style="padding:0 4px;vertical-align:top;text-align:center;">'
      + '<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #2a3f5f;border-radius:8px;overflow:hidden;"><tr><td>'
      + imgHtml
      + '</td></tr><tr><td style="padding:5px 6px;font-size:11px;color:#ffffff;font-weight:600;text-align:center;">' + a.name + '</td></tr>'
      + '<tr><td style="padding:0 6px 6px;font-size:10px;color:#a0b0c8;text-align:center;">' + a.category + '</td></tr></table>'
      + '</td>';
  }).join('');

  var accSection = accs.length > 0
    ? '<tr><td style="padding:8px 28px 16px;">'
      + '<div style="font-size:9px;letter-spacing:2px;color:#c9a84c;text-transform:uppercase;margin-bottom:12px;">Recommended Accessories</div>'
      + '<table width="100%" cellpadding="0" cellspacing="0"><tr>' + accCols + '</tr></table>'
      + '</td></tr>'
    : '';

  return '<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">'
    + '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:20px 0;"><tr><td align="center">'
    + '<table width="600" cellpadding="0" cellspacing="0" style="background:#0d1730;border-radius:12px;overflow:hidden;max-width:600px;">'
    + '<tr><td style="background:#1a2744;padding:28px 28px 20px;text-align:center;border-bottom:2px solid #c9a84c;">'
    + '<div style="font-size:10px;letter-spacing:3px;color:#c9a84c;text-transform:uppercase;margin-bottom:6px;">Bel Furniture x DreamFinder</div>'
    + '<div style="font-size:22px;font-weight:700;color:#ffffff;margin-bottom:4px;">Your Perfect Matches, ' + firstName + '</div>'
    + '<div style="font-size:12px;color:#a0b0c8;">Based on your personalized sleep profile</div>'
    + '</td></tr>'
    + '<tr><td style="background:#c9a84c;padding:12px 28px;text-align:center;">'
    + '<div style="font-size:16px;font-weight:700;color:#0d1730;">' + (data.discount || 5) + '% OFF - Your Discount Is Ready!</div>'
    + (dreamCode ? '<div style="font-size:22px;font-weight:800;color:#0d1730;letter-spacing:3px;margin-top:4px;">' + dreamCode + '</div>' : '')
    + '<div style="font-size:11px;color:#0d1730;margin-top:2px;">Show this code to your sleep specialist today</div>'
    + '</td></tr>'
    + '<tr><td style="padding:20px 28px 8px;">'
    + '<div style="font-size:9px;letter-spacing:2px;color:#c9a84c;text-transform:uppercase;margin-bottom:5px;">Your Sleep Profile</div>'
    + '<div style="font-size:13px;color:#ffffff;font-weight:600;">' + (data.sleepProfile || '') + '</div>'
    + '</td></tr>'
    + '<tr><td style="padding:12px 28px 8px;">'
    + '<div style="font-size:9px;letter-spacing:2px;color:#c9a84c;text-transform:uppercase;margin-bottom:12px;">Your Top Mattress Matches</div>'
    + matchRows
    + '</td></tr>'
    + accSection
    + '<tr><td style="padding:18px 28px 24px;text-align:center;border-top:1px solid #1e3050;">'
    + '<div style="font-size:12px;color:#a0b0c8;margin-bottom:3px;">Bring this email to your Bel Furniture store</div>'
    + '<div style="font-size:13px;color:#c9a84c;font-weight:700;">Your ' + (data.discount || 5) + '% discount is waiting for you</div>'
    + (dreamCode ? '<div style="font-size:16px;font-weight:800;color:#c9a84c;letter-spacing:3px;margin-top:4px;">' + dreamCode + '</div>' : '')
    + '</td></tr>'
    + '</table></td></tr></table></body></html>';
}
