/**
 * Google Apps Script Web App for Personal Finance Advisor Bot
 *
 * 1. Create/open a Google Sheet.
 * 2. Open Extensions -> Apps Script.
 * 3. Paste this file into Code.gs.
 * 4. Deploy as Web app.
 * 5. Allow access for the users who should submit data.
 * 6. Put the deployment URL into:
 *    GOOGLE_SHEETS_WEBHOOK_URL
 *
 * Suggested columns are created automatically if the sheet is empty.
 */

const SHEET_NAME = "Finance Reports";

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents || "{}");
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);

    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Timestamp",
        "Report ID",
        "Income",
        "Goal",
        "Expenses",
        "Savings",
        "Savings Rate",
        "Largest Expense",
        "AI Source",
        "Suggestions"
      ]);
    }

    const summary = payload.summary || {};
    const expenses = payload.expenses || {};
    const suggestions = Array.isArray(payload.suggestions)
      ? payload.suggestions.join(" | ")
      : "";

    sheet.appendRow([
      payload.timestamp || new Date().toISOString(),
      payload.report_id || "",
      payload.income || 0,
      payload.goal || "",
      JSON.stringify(expenses),
      summary.savings || 0,
      summary.savings_rate || 0,
      summary.largest_expense_category || "",
      payload.ai_source || "local",
      suggestions
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: "Finance report stored in Google Sheets."
      }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: String(error)
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
