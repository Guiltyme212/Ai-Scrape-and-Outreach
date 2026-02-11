"""Google Sheets integration — read leads, write scores and results."""

import gspread
from google.oauth2.service_account import Credentials

from leadpilot.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_sheet():
    """Authenticate and return the worksheet."""
    creds = Credentials.from_service_account_file(
        settings.google_credentials_path, scopes=SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(settings.google_sheet_id)
    return spreadsheet.worksheet(settings.sheet_name)


def get_leads() -> list[dict]:
    """Read all leads from the sheet. Returns list of dicts with row_index."""
    sheet = _get_sheet()
    rows = sheet.get_all_values()

    if len(rows) < 2:
        return []

    headers = rows[0]
    leads = []
    for i, row in enumerate(rows[1:], start=2):  # row 2 in sheet = index 1 in data
        lead = {
            "row_index": i,
            "business_name": row[0] if len(row) > 0 else "",
            "website": row[1] if len(row) > 1 else "",
            "description": row[2] if len(row) > 2 else "",
            "email": row[3] if len(row) > 3 else "",
            "score": row[4] if len(row) > 4 else "",
            "preview_url": row[5] if len(row) > 5 else "",
            "email_subject": row[6] if len(row) > 6 else "",
            "email_body": row[7] if len(row) > 7 else "",
        }
        leads.append(lead)

    return leads


def update_score(row_index: int, score: int):
    """Write the website score to column E."""
    sheet = _get_sheet()
    sheet.update_cell(row_index, 5, score)


def update_result(
    row_index: int, preview_url: str, email_subject: str, email_body: str
):
    """Write preview URL and email draft to columns F-H."""
    sheet = _get_sheet()
    sheet.update(f"F{row_index}:H{row_index}", [[preview_url, email_subject, email_body]])
