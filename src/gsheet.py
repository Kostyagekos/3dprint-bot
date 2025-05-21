
import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "A1")

if GOOGLE_CREDENTIALS_JSON is None:
    raise RuntimeError("❌ GOOGLE_CREDENTIALS_JSON не задан. Укажите путь в .env")

if GOOGLE_SHEET_ID is None:
    raise RuntimeError("❌ GOOGLE_SHEET_ID не задан. Укажите его в .env")

def append_order_row(data: dict):
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_JSON,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()

    row = [
        str(datetime.datetime.now()),
        str(data.get("user_id", "")),
        str(data.get("model", "")),
        str(data.get("technology", "")),
        str(data.get("quantity", "")),
        f"{data.get('volume', 0):.2f}",
        f"{data.get('total_volume', 0):.2f}",
        f"{data.get('price', 0):.2f}",
        str(data.get("screenshot_url", ""))
    ]

    sheet.values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=GOOGLE_SHEET_RANGE,
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()
