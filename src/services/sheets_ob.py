from datetime import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.logger_config import setup_logger
from src.services.exchange import Order

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
    NO_BREAK_STRING = "*=*=*=*=*"
    
    def __init__(self, id, ob_sheet_name, neworders_sheet_name, service_account_file=None, user_token_file=None, user_secret_file=None):
        """
        Initialize the SheetsOB class
        """
        if (id is None):
            raise ValueError("ID is required")
        if (ob_sheet_name is None):
            raise ValueError("Order Book Sheet is required")
        if (neworders_sheet_name is None):
            raise ValueError("New Orders Sheet is required")
        if (service_account_file is None and user_secret_file is None):
            raise ValueError("Service account file or user secret file is required")
        
        self.ID=id
        self.OB_SHEET_NAME=ob_sheet_name
        self.NEWORDERS_SHEET_NAME=neworders_sheet_name
        
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
        self.CACHE: dict[str, list[list]] = {}
    
    def populate_cache(self, sheet_name=None):
        """
        Populate the cache for sheet_name
        """
        if (sheet_name is None):
            sheet_name = self.OB_SHEET_NAME
        
        logger.info("Populating Google Sheets cache for sheet [" + sheet_name + "]")
        try:
            sheet = self.SERVICE.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.ID, range=sheet_name)
                .execute()
            )
            values = result.get("values", [])
            
            if not values:
                logger.info("No data found.")
                return None
            
            self.CACHE[sheet_name] = values
            logger.info("Successfully populated Google Sheets cache with [" + str(len(self.CACHE[sheet_name])) + "] rows")
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
        
        if (self.OB_SHEET_NAME not in self.CACHE or self.CACHE[self.OB_SHEET_NAME] is None):
            self.populate_cache(self.OB_SHEET_NAME)
            
        # Initialise res with headers
        res = [self.CACHE[self.OB_SHEET_NAME][0]]
        
        # Filter rows with matching order references
        for row in self.CACHE[self.OB_SHEET_NAME][1:]:
            if len(row) > self.GS_COLUMN_MAPPING["REFERENCE"] and row[self.GS_COLUMN_MAPPING["REFERENCE"]] in order_references:
                res.append(row)
        logger.info("Found [" + str(len(res)) + "] rows with matching order references")
            
        # Check if there are missing order references    
        if (len(res) < len(order_references)):
            logger.warning("Missing [" + str(len(order_references) - len(res)) + "] order references")
            # Add missing order references with empty values
            for order_ref in order_references:
                if not any(row[self.GS_COLUMN_MAPPING["REFERENCE"]] == order_ref for row in res):
                    res.append(["", "", "", "", "", "", "", "", "", "", "", order_ref, ""])
        
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
        self.populate_cache()
            
        # Filter rows with value True in the `RTPS Refresh` column
        res = []
        for idx, row in enumerate(self.CACHE[self.OB_SHEET_NAME][1:], start=2):
            if len(row) > self.GS_COLUMN_MAPPING["RTPS_REFRESH"] and row[self.GS_COLUMN_MAPPING["RTPS_REFRESH"]] == "TRUE":
                res.append([idx, row[self.GS_COLUMN_MAPPING["ACCOUNT"]], row[self.GS_COLUMN_MAPPING["PAIR"]], row[self.GS_COLUMN_MAPPING["REFERENCE"]]])
        
        return res
    
    def update_ob_row(self, row_number: int, row: list[str]):
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
    
    def update_new_orders(self, account_orders: dict[str, list[Order]]):
        """
        Update the New Orders sheet with new orders
        """
        if (account_orders is None):
            raise ValueError("Account orders is required")
        
        logger.info(f"Updating Google Sheets with [{sum([len(v) for v in account_orders.values()])}] rows of new orders")
        
        # Check if the cache is populated, this should not be necessary
        if (self.NEWORDERS_SHEET_NAME not in self.CACHE or self.CACHE[self.NEWORDERS_SHEET_NAME] is None):
            self.populate_cache(self.NEWORDERS_SHEET_NAME)
        
        # Find the NO_BREAK_STRING row
        no_break_row = None
        for idx, row in enumerate(self.CACHE[self.NEWORDERS_SHEET_NAME]):
            if row is not None and len(row) > 0:
                if row[0] == self.NO_BREAK_STRING:
                    no_break_row = idx + 1
                    break
                
        if (no_break_row is None):
            logger.error("No breaker row found in Google Sheets! Not updating new orders")
            return None
        
        # Construct the new orders list
        data = [["Last Updated", "Account", "Symbol", "Side", "Average", "Executed", "Fee", "Fee Currency", "Order ID"]]
        for account, orders in account_orders.items():
            for order in orders:
                data.append([
                    order["datetime"].strftime("%d/%m/%Y %H:%M:%S"), 
                    account,
                    order["symbol"],
                    order["side"],
                    order["average"],
                    order["executed"],
                    order["fee"],
                    order["fee_currency"],
                    order["order_id"],
                ])
        
        # Add the new orders to the Google Sheets
        row_number = no_break_row + 1
        self.add_new_order_rows(data, row_number)
    
    def add_new_order_rows(self, orders: list[Order], start_row_number: int):
        """
        Add new order rows to the New Orders sheet
        """
        if (orders is None):
            raise ValueError("Order is required")
        if (start_row_number is None):
            raise ValueError("Row number is required")
        
        if (len(orders) == 0):
            logger.debug("No new orders to add")
            return None
        logger.debug("Adding new orders to Google Sheets starting from row [" + str(start_row_number) + "] with [" + str(len(orders)) + "] orders")

        try:
            sheet = self.SERVICE.spreadsheets()
            (
                sheet.values()
                .update(
                    spreadsheetId=self.ID,
                    range=self.NEWORDERS_SHEET_NAME + "!A" + str(start_row_number),
                    valueInputOption="USER_ENTERED",
                    body={"values": orders}
                )
                .execute()
            )
            logger.debug("Successfully added orders to Google Sheets")
        except HttpError as err:
            logger.error(err)
            return None
    
    def convert_str_to_datetime(self, date_str):
        """
        Convert a date string to datetime
        """
        if (date_str is None):
            return None
        
    def get_no_last_updated(self) -> dict[str, datetime]:
        """
        Get the last updated time from the new orders sheet
        """
        
        if (self.NEWORDERS_SHEET_NAME not in self.CACHE or self.CACHE[self.NEWORDERS_SHEET_NAME] is None):
            self.populate_cache(self.NEWORDERS_SHEET_NAME)
        
        logger.info("Getting last updated time from Google Sheets")
        
        res = {}
        for row in self.CACHE[self.NEWORDERS_SHEET_NAME]:
            if row is not None and len(row) > 0:
                if row[0] == self.NO_BREAK_STRING:
                    return res
                
                if row[0] == "Account" or row[1] == "Deactivated":
                    continue
                
                res[row[0]] = row[1] if len(row) > 1 else None
    
    def clear_no_from_breaker(self):
        """
        Clear all rows on New Orders Sheet from the breaker row
        """
        logger.info("Clearing New Orders sheet")
        
        # Check if the cache is populated, this should not be necessary
        if (self.NEWORDERS_SHEET_NAME not in self.CACHE or self.CACHE[self.NEWORDERS_SHEET_NAME] is None):
            self.populate_cache(self.NEWORDERS_SHEET_NAME)
        
        # Clear the NO_BREAK_STRING from the breaker row
        for idx, row in enumerate(self.CACHE[self.NEWORDERS_SHEET_NAME]):
            if row is not None and len(row) > 0:
                if row[0] == self.NO_BREAK_STRING:
                    self.clear_no_rows_from(idx+3)
    
    def clear_no_rows_from(self, row_number):
        """
        Clear all rows on New Orders Sheet from the row_number
        """
        if (row_number is None):
            raise ValueError("Row number is required")
        
        # Get the last column and row
        last_col = chr(65 + len(self.CACHE[self.NEWORDERS_SHEET_NAME][0]))
        last_row = len(self.CACHE[self.NEWORDERS_SHEET_NAME])
        range = self.NEWORDERS_SHEET_NAME + "!A" + str(row_number) + ":" + last_col + str(last_row)
        
        logger.info("Clearing New Orders sheet cells range [" + range + "]")
        
        # Clear all rows from the row_number
        sheet = self.SERVICE.spreadsheets()
        (
            sheet.values()
            .clear(
                spreadsheetId=self.ID,
                range=range,
                body={}
            )
            .execute()
        )