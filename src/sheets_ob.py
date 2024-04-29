import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.logger_config import setup_logger

logger = setup_logger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

class SheetsOB:
    GS_ORDER_REF_COL = 11
    
    def __init__(self, id, sheet):
        """
        Initialize the SheetsOB class
        """
        if (id is None):
            raise ValueError("ID is required")
        if (sheet is None):
            raise ValueError("Sheet is required")
        
        self.ID=id
        self.SHEET=sheet
        
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            self.CREDS = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.CREDS or not self.CREDS.valid:
            if self.CREDS and self.CREDS.expired and self.CREDS.refresh_token:
                self.CREDS.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.CREDS = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(self.CREDS.to_json())
                    
        # Initialize the service
        self.SERVICE = build("sheets", "v4", credentials=self.CREDS)
        
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
                .get(spreadsheetId=self.ID, range=self.SHEET)
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
            if len(row) > self.GS_ORDER_REF_COL and row[self.GS_ORDER_REF_COL] in order_references:
                res.append(row)
        logger.info("Found [" + str(len(res)) + "] rows with matching order references")
            
        # Check if there are missing order references    
        if (len(res) < len(order_references)):
            logger.warning("Missing [" + str(len(order_references) - len(res)) + "> order references")
            # Add missing order references with empty values
            for order_ref in order_references:
                if not any(row[11] == order_ref for row in res):
                    res.append([None] * 12)
        
        # Ensure each row has 13 columns, if not add empty values
        for row in res:
            if len(row) < 13:
                row.extend([''] * (13 - len(row)))
        
        return res

        