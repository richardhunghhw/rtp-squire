import os.path

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.logger_config import setup_logger

logger = setup_logger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

class SheetsOB:
    GS_COLUMN_MAPPING = {
        "DATE": 0,
        "ACCOUNT": 1,
        "PAIR": 2,
        "BUY_SELL": 3,
        "AVERAGE": 4,
        "EXECUTED": 5,
        "EFFECT": 6,
        "TOTAL_INC_FEES": 7,
        "FEES": 8,
        "FEES_CURRENCY": 9,
        "FEES_USDT": 10,
        "REFERENCE": 11,
        "NOTES": 12,
        "RTPS_REFRESH": 13
    }
    
    def __init__(self, id, sheet_name, service_account_file=None, user_token_file=None, user_secret_file=None):
        """
        Initialize the SheetsOB class
        """
        if (id is None):
            raise ValueError("ID is required")
        if (sheet_name is None):
            raise ValueError("Sheet is required")
        if (service_account_file is None and user_secret_file is None):
            raise ValueError("Service account file or user secret file is required")
        
        self.ID=id
        self.SHEET_NAME=sheet_name
        
        # Get credentials from service account file or user token file
        creds = None
        if service_account_file is not None and os.path.exists(service_account_file):
            creds = service_account.Credentials.from_service_account_file(service_account_file)
        if user_token_file is not None and os.path.exists(user_token_file):
            creds = Credentials.from_authorized_user_file(user_token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if (not creds or not creds.valid) and user_secret_file is not None and os.path.exists(user_secret_file):
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    user_secret_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open(user_token_file, "w") as token:
                    token.write(creds.to_json())
                    
        # Initialize the service
        self.SERVICE = build("sheets", "v4", credentials=creds)
        
        # Initialize the cache
        self.CACHE = None
    
    def populate_cache(self):
        """
        Populate the cache
        """
        logger.info("Populating Google Sheets cache...")
        try:
            sheet = self.SERVICE.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.ID, range=self.SHEET_NAME)
                .execute()
            )
            values = result.get("values", [])
            
            if not values:
                print("No data found.")
                return None
            
            self.CACHE = values
            logger.info("Successfully populated Google Sheets cache with [" + str(len(self.CACHE)) + "] rows")
        except HttpError as err:
            logger.error(err)
            return None
    
    def get_rows_with_order_references(self, order_references):
        """
        Get all rows with order references
        """
        if (order_references is None):
            raise ValueError("Order references are required")
        logger.info("Getting rows from Google Sheets with order references [" + str(order_references) + "]")
        
        if (self.CACHE is None):
            self.populate_cache()
            
        # Initialise res with headers
        res = [self.CACHE[0]]
        
        # Filter rows with matching order references
        for row in self.CACHE[1:]:
            if len(row) > self.GS_COLUMN_MAPPING["REFERENCE"] and row[self.GS_COLUMN_MAPPING["REFERENCE"]] in order_references:
                res.append(row)
        logger.info("Found [" + str(len(res)) + "] rows with matching order references")
            
        # Check if there are missing order references    
        if (len(res) < len(order_references)):
            logger.warning("Missing [" + str(len(order_references) - len(res)) + "> order references")
            # Add missing order references with empty values
            for order_ref in order_references:
                if not any(row[self.GS_COLUMN_MAPPING["REFERENCE"]] == order_ref for row in res):
                    res.append([None] * 12)
        
        # Ensure each row has 13 columns, if not add empty values
        for row in res:
            if len(row) < 13:
                row.extend([''] * (13 - len(row)))
        
        return res

    def get_rows_pending_rtps_refresh(self):
        """
        Get rows with TRUE in the `RTPS Refresh` column
        Returns a list of row_number, account, pair, reference
        """
        logger.info("Getting rows from Google Sheets pending RTPS Refresh")
        
        if (self.CACHE is None):
            self.populate_cache()
            
        # Filter rows with value True in the `RTPS Refresh` column
        res = []
        for idx, row in enumerate(self.CACHE[1:], start=2):
            if len(row) > self.GS_COLUMN_MAPPING["RTPS_REFRESH"] and row[self.GS_COLUMN_MAPPING["RTPS_REFRESH"]] == "TRUE":
                res.append([idx, row[self.GS_COLUMN_MAPPING["ACCOUNT"]], row[self.GS_COLUMN_MAPPING["PAIR"]], row[self.GS_COLUMN_MAPPING["REFERENCE"]]])
        
        return res
    
    def update_row(self, row_number: int, row: list[str]):
        """
        Update the Google Sheets row, updating only the columns with values
        """
        if (row_number is None):
            raise ValueError("Row number is required")
        if (row is None or len(row) == 0):
            raise ValueError("Row is required")
        
        logger.debug("Updating Google Sheets row [" + str(row_number) + "] with values [" + str(row) + "]")
        
        data = []
        for key, value in row.items():
            if value is not None:                
                column = self.GS_COLUMN_MAPPING[key]
                range_str = 'Crypto Book!' + chr(65 + column) + str(row_number) + ':' + chr(65 + column) + str(row_number)
                data.append({
                    "range": range_str,
                    "majorDimension": "ROWS",
                    "values": [[value]],
                })

        try:
            sheet = self.SERVICE.spreadsheets()
            (
                sheet.values()
                .batchUpdate(
                    spreadsheetId=self.ID,
                    body={
                        "valueInputOption": "USER_ENTERED",
                        "data": data,
                    }
                )
                .execute()
            )
            logger.info("Successfully updated Google Sheets row [" + str(row_number) + "]")
        except HttpError as err:
            logger.error(err)
            return None