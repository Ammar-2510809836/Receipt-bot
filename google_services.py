import os
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import gspread

from config import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEET_ID, GOOGLE_DRIVE_PARENT_FOLDER_ID

import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authenticate_google():
    """Authenticates with Google APIs using OAuth 2.0 (User Account)."""
    creds = None
    token_file = 'token.json'
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials.json exists (renamed from client_secret_*.json)
            # We reuse the env var path or default to 'credentials.json'
            client_config_path = 'credentials.json' 
            if not os.path.exists(client_config_path):
                 # Fallback if user kept the service account naming in env, 
                 # but we need the OAuth json here.
                 client_config_path = GOOGLE_SERVICE_ACCOUNT_JSON 
            
            flow = InstalledAppFlow.from_client_secrets_file(
                client_config_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_drive_service(creds):
    return build('drive', 'v3', credentials=creds)

def get_sheets_client(creds):
    return gspread.authorize(creds)

def find_or_create_folder(drive_service, folder_name, parent_id):
    """Finds a folder by name inside a parent folder, or creates it."""
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

def upload_receipt_image(file_path: str, date_str: str) -> str:
    """
    Uploads the image to Google Drive in a YYYY/MM folder structure.
    Returns the webViewLink of the uploaded file.
    """
    try:
        creds = authenticate_google()
        service = get_drive_service(creds)

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = str(date_obj.year)
        month = f"{date_obj.month:02d}"

        # Create/Find Year Folder
        year_folder_id = find_or_create_folder(service, year, GOOGLE_DRIVE_PARENT_FOLDER_ID)
        
        # Create/Find Month Folder inside Year Folder
        month_folder_id = find_or_create_folder(service, month, year_folder_id)

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [month_folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        logger.info(f"File ID: {file.get('id')}")
        return file.get('webViewLink')

    except Exception as e:
        logger.error(f"Error uploading to Drive: {e}")
        return None

def _get_or_create_worksheet(client, sheet_id, sheet_name):
    """Helper to get a worksheet or create it with headers if missing."""
    sheet = client.open_by_key(sheet_id)
    try:
        worksheet = sheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # Create new worksheet
        worksheet = sheet.add_worksheet(title=sheet_name, rows=100, cols=20)
        # Add Headers immediately
        HEADINGS = ["Date", "Vendor", "Total", "Currency", "Category", "Items", "Drive Link", "Status"]
        worksheet.append_row(HEADINGS)
        logger.info(f"Created new worksheet: {sheet_name}")
    return worksheet

def add_transaction_to_sheet(data: dict, drive_link: str):
    """
    Appends receipt data to the correct Month/Year worksheet.
    """
    try:
        creds = authenticate_google()
        client = get_sheets_client(creds)
        
        # Determine Sheet Name from Date
        date_str = data.get('date') 
        if not date_str: date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_obj = datetime.now()
            
        sheet_name = date_obj.strftime("%B %Y") # e.g., "February 2026"
        
        worksheet = _get_or_create_worksheet(client, GOOGLE_SHEET_ID, sheet_name)

        # Ensure headers exist (in case sheet existed but was empty/cleared)
        HEADINGS = ["Date", "Vendor", "Total", "Currency", "Category", "Items", "Drive Link", "Status"]
        existing_headers = worksheet.row_values(1)
        
        # Check if headers are missing or invalid (A1 should be "Date")
        if not existing_headers or existing_headers[0] != "Date":
            logger.info(f"Headers missing in {sheet_name}. Inserting at Row 1.")
            worksheet.insert_row(HEADINGS, 1)
        
        # Data map
        vendor = data.get('vendor', 'Unknown')
        total = data.get('total', 0.0)
        currency = data.get('currency', 'EUR') 
        category = data.get('category', 'Uncategorized')
        items = ", ".join(data.get('items', [])) if data.get('items') else ""

        # Construct row
        row = [date_str, vendor, total, currency, category, items, drive_link, "Processed"]
        
        # Append
        worksheet.append_row(row)
        logger.info(f"Added row to {sheet_name}: {row}")
        return True
    
    except Exception as e:
        logger.error(f"Error adding to Sheet: {e}")
        return False

def get_monthly_spend(year: int, month: int) -> float:
    """Calculates total spend for a given month/year from its specific worksheet."""
    try:
        creds = authenticate_google()
        client = get_sheets_client(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Construct sheet name
        # We need a datetime object to get the month name easily
        dt = datetime(year, month, 1)
        sheet_name = dt.strftime("%B %Y") # "February 2026"
        
        try:
            worksheet = sheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return 0.0 # No sheet for this month yet
            
        # Get all values
        rows = worksheet.get_all_values()
        
        if len(rows) < 2:
            return 0.0 # No data
            
        total_spend = 0.0
        import re
        
        for i, row in enumerate(rows):
            if i == 0: continue # Skip header
            
            try:
                # Ensure row has enough columns (Date is col 0, Total is col 2)
                if len(row) < 3: continue 

                total_val = str(row[2]).strip()
                if not total_val: continue

                # Robust number extraction
                clean_val = total_val.replace(' ', '')
                if ',' in clean_val and '.' in clean_val:
                    clean_val = clean_val.replace(',', '')
                elif ',' in clean_val:
                    clean_val = clean_val.replace(',', '.')
                    
                match = re.search(r"[-+]?\d*\.\d+|\d+", clean_val)
                if match:
                    total_spend += float(match.group())
                        
            except (ValueError, IndexError) as e:
                continue 

        return total_spend
    except Exception as e:
        logger.error(f"Error calculating spend: {e}")
        return 0.0
