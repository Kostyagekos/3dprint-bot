import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_JSON")

def append_order_row(data):
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        now,
        data["user_id"],
        data["model"],
        data["technology"],
        data["quantity"],
        f"{data['volume']:.2f}",
        f"{data['total_volume']:.2f}",
        f"{data['price']:.2f}",
        data["screenshot_url"]
    ]
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Заказы!A1",
        valueInputOption="RAW",
        body={"values": [row]}
    ).execute()
