// ─────────────────────────────────────────────────────────────
//  Project Management Dashboard — Google Apps Script Backend
//
//  SETUP:
//  1. In your Google Sheet go to Extensions → Apps Script
//  2. Delete the default code and paste this entire file
//  3. Replace the values below marked with ← Change this
//  4. Save (Ctrl+S)
//  5. Click Deploy → New deployment
//  6. Type: Web app  |  Execute as: Me  |  Who has access: Anyone
//  7. Click Deploy → copy the Web App URL
//  8. Paste the URL in the dashboard under ⚙ Connect Sheet
//
//  DAILY EMAIL SETUP:
//  1. After pasting this file, click Run → sendDailyDigest once
//     to grant Gmail permissions
//  2. Click Triggers (clock icon on left sidebar) → Add Trigger
//  3. Function: sendDailyDigest
//  4. Event source: Time-driven
//  5. Type: Week timer → Every weekday (Monday to Friday)
//  6. Time: 9am to 10am
//  7. Click Save
// ─────────────────────────────────────────────────────────────

var ADMIN_PASSWORD   = 'your-admin-password-here'; // ← Change this
var SHEET_NAME       = 'Sheet1';                    // ← Change if needed
var DASHBOARD_URL    = 'https://your-netlify-url.netlify.app'; // ← Change after hosting
var RECIPIENT_EMAIL  = 'bhakti@letstranzact.com';  // ← Change if needed

// ── DAILY EMAIL DIGEST ────────────────────────────────────────
function sendDailyDigest() {
  var sheet  = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  var rows   = sheet.getDataRange().getValues();
  var header = rows[0].map(function(c) { return c.toString().toLowerCase().trim(); });

  var colName   = header.indexOf('project name');
  var colType   = header.indexOf('project type');
  var colStatus = header.indexOf('status');
  var colDev    = header.indexOf('developer');
  var colRelease = header.indexOf('release date');

  // Count by status
  var statusCount = {};
  var projects    = [];

  for (var i = 1; i < rows.length; i++) {
    var name = rows[i][colName] ? rows[i][colName].toString().trim() : '';
    if (!name) continue;

    var status  = colStatus  !== -1 ? rows[i][colStatus].toString().trim()  : '';
    var type    = colType    !== -1 ? rows[i][colType].toString().trim()    : '';
    var dev     = colDev     !== -1 ? rows[i][colDev].toString().trim()     : '';
    var release = colRelease !== -1 ? rows[i][colRelease].toString().trim() : '';

    statusCount[status] = (statusCount[status] || 0) + 1;
    projects.push({ name: name, type: type, status: status, dev: dev, release: release });
  }

  // Build status summary rows
  var statusOrder = ['In Dev', 'In QA', 'In UAT', 'Pending for Release', 'Paused', 'Todo', 'Released'];
  var summaryRows = '';
  statusOrder.forEach(function(s) {
    if (statusCount[s]) {
      summaryRows += '<tr><td style="padding:4px 12px 4px 0;color:#64748b;">' + s + '</td>'
                   + '<td style="padding:4px 0;font-weight:600;">' + statusCount[s] + '</td></tr>';
    }
  });

  // Build project table rows
  var projectRows = '';
  projects.forEach(function(p) {
    var statusColor = {
      'In Dev': '#2563eb', 'In QA': '#7c3aed', 'In UAT': '#0891b2',
      'Pending for Release': '#d97706', 'Released': '#16a34a',
      'Paused': '#dc2626', 'Todo': '#64748b', 'Dev Complete': '#0f766e'
    }[p.status] || '#64748b';

    projectRows += '<tr style="border-bottom:1px solid #f1f5f9;">'
      + '<td style="padding:8px 12px 8px 0;font-weight:500;">' + p.name + '</td>'
      + '<td style="padding:8px 12px 8px 0;color:#64748b;font-size:12px;">' + p.type + '</td>'
      + '<td style="padding:8px 12px 8px 0;">'
      +   '<span style="background:' + statusColor + '1a;color:' + statusColor + ';padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500;">' + p.status + '</span>'
      + '</td>'
      + '<td style="padding:8px 12px 8px 0;color:#64748b;font-size:12px;">' + p.dev + '</td>'
      + '<td style="padding:8px 0;color:#64748b;font-size:12px;">' + p.release + '</td>'
      + '</tr>';
  });

  var today = new Date();
  var dateStr = today.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  var html = '<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;max-width:680px;margin:0 auto;color:#1a2332;">'

    // Header
    + '<div style="background:#0f172a;padding:20px 28px;border-radius:8px 8px 0 0;">'
    +   '<div style="font-size:16px;font-weight:600;color:#f1f5f9;">Project Management Dashboard</div>'
    +   '<div style="font-size:12px;color:#64748b;margin-top:4px;">' + dateStr + '</div>'
    + '</div>'

    // Status summary
    + '<div style="background:#fff;padding:24px 28px;border-bottom:1px solid #e2e8f0;">'
    +   '<div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:12px;">STATUS SUMMARY</div>'
    +   '<table style="border-collapse:collapse;">' + summaryRows + '</table>'
    + '</div>'

    // Projects table
    + '<div style="background:#fff;padding:24px 28px;border-bottom:1px solid #e2e8f0;">'
    +   '<div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:12px;">ALL PROJECTS</div>'
    +   '<table style="border-collapse:collapse;width:100%;">'
    +     '<thead><tr style="border-bottom:2px solid #e2e8f0;">'
    +       '<th style="padding:6px 12px 6px 0;text-align:left;font-size:11px;color:#94a3b8;font-weight:500;">PROJECT</th>'
    +       '<th style="padding:6px 12px 6px 0;text-align:left;font-size:11px;color:#94a3b8;font-weight:500;">TYPE</th>'
    +       '<th style="padding:6px 12px 6px 0;text-align:left;font-size:11px;color:#94a3b8;font-weight:500;">STATUS</th>'
    +       '<th style="padding:6px 12px 6px 0;text-align:left;font-size:11px;color:#94a3b8;font-weight:500;">DEVELOPER</th>'
    +       '<th style="padding:6px 0;text-align:left;font-size:11px;color:#94a3b8;font-weight:500;">RELEASE</th>'
    +     '</tr></thead>'
    +     '<tbody>' + projectRows + '</tbody>'
    +   '</table>'
    + '</div>'

    // CTA button
    + '<div style="background:#f8fafc;padding:20px 28px;border-radius:0 0 8px 8px;text-align:center;">'
    +   '<a href="' + DASHBOARD_URL + '" style="background:#2563eb;color:#fff;padding:10px 28px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600;">Open Dashboard →</a>'
    + '</div>'

  + '</div>';

  MailApp.sendEmail({
    to:      RECIPIENT_EMAIL,
    subject: 'Project Dashboard — ' + dateStr,
    htmlBody: html
  });
}

// ── WRITE-BACK: Update description/link from dashboard ────────
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);

    if (!data.token || data.token !== ADMIN_PASSWORD) {
      return respond({ error: 'Unauthorised.' });
    }

    var sheet  = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    var rows   = sheet.getDataRange().getValues();
    var header = rows[0].map(function(c) { return c.toString().toLowerCase().trim(); });

    var colName = header.indexOf('project name');
    var colDesc = header.indexOf('description');
    var colLink = header.indexOf('link');

    for (var i = 1; i < rows.length; i++) {
      if (rows[i][colName] === data.name) {
        if (colDesc !== -1) sheet.getRange(i + 1, colDesc + 1).setValue(data.description || '');
        if (colLink !== -1) sheet.getRange(i + 1, colLink + 1).setValue(data.link || '');
        return respond({ success: true });
      }
    }

    return respond({ error: 'Project "' + data.name + '" not found.' });

  } catch (err) {
    return respond({ error: err.message });
  }
}

function respond(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
