from datetime import datetime

from src.logger_config import setup_logger
from src.services.exchange import Exchange, Order
from src.services.sheets_ob import SheetsOB
from src.helper import get_exchange_type

logger = setup_logger(__name__)

class OrderBook:
    """
    Automates the population of the order book using order references
    """
    def __init__(self, sheets: SheetsOB, exchanges: list[Exchange]):
        """
        Initialize the OrderBook class
        """
        if (sheets is None):
            raise ValueError("Sheets is required")
        if (exchanges is None and len(exchanges) == 0):
            raise ValueError("Exchanges is required")
        
        self.SHEETS=sheets
        self.EXCHANGES=exchanges
        
    def run(self):
        """
        Run the job
        """
        logger.info("Running Order Book job...")
        
        # Query the Google Sheets API for rows requiring processing
        rows = self.SHEETS.get_rows_pending_rtps_refresh()
        if (rows is None):
            logger.error("Failed to retrieve order references, exiting...")
            return
        
        # Process each order reference
        self.process_rows(rows)
        
        # Refresh the Google Sheets cache
        self.SHEETS.populate_cache()
        
        logger.info("Order Book job completed successfully")
        
    def process_rows(self, rows):
        """
        Process rows, error handling 
        """
        logger.info("Processing [" + str(len(rows)) + "] rows")
        
        if (rows is None or len(rows) == 0):
            logger.info("No rows to process")
            return
        
        for row in rows:
            # Get the sheets updated row
            order_row = None
            try:
                order_row = self.process_row(row)
            except Exception as e: 
                logger.error("Failed to process row [" + str(row) + "] with error [" + str(e) + "]")
                order_row = {
                    "RTPS_REFRESH": "FAILED - " + str(e)
                }
                
            # Update the Google Sheets row with the order
            if (order_row is not None):
                self.SHEETS.update_row(row[0], order_row)
        
    def process_row(self, row):
        """
        Process row with [row_num, account, pair, order reference]
        Fetch the order from the corresponding exchange and update the Google Sheets row
        """
        _, account, pair, order_reference = row
        
        # Validate the row
        if (account is None or pair is None or order_reference is None):
            raise ValueError("Invalid row with account [" + account + "], pair [" + pair + "], order reference [" + order_reference + "]")
        
        logger.info("Processing row with account [" + account + "], pair [" + pair + "], order reference [" + order_reference + "]")
        
        # Fetch the order from the corresponding exchange
        order: Order = self.fetch_order(account, pair, order_reference)
        
        # If the fetch_order returns None, the order is being skipped for some reason, ignore, do not update the Google Sheets row
        if (order is None):
            return None
        
        # Create a new order object as per the Google Sheets schema
        formatted_date = order["datetime"].strftime("%d/%m/%Y")
        res = {
            "DATE": formatted_date,
            "BUY_SELL": order["side"],
            "AVERAGE": order["average"],
            "EXECUTED": order["executed"],
            "RTPS_REFRESH": "COMPLETED"
        }
        if (order["fee"] is not None and order["fee_currency"] is not None):
            res["FEE"] = order["fee"]
            res["FEE_CURRENCY"] = order["fee_currency"]
        return res
        
    def fetch_order(self, account, pair, order_reference):
        """
        Fetch the order from the corresponding exchange
        """
        logger.debug("Fetching order for account [" + account + "], pair [" + pair + "], order reference [" + order_reference + "]")
        
        # Determine the exchange, type
        exchange: Exchange
        type: str
        exchange, type = get_exchange_type(account, self.EXCHANGES)
        if (exchange is None or type is None):
            raise Exception("Failed to determine exchange or type for account [" + account + "]")
        
        # Query the exchange for the order
        order = None
        if (type == "Spot"):
            order = exchange.query_spot_order(pair, order_reference)
        elif (type in ["Margin", "Futures"]):
            order = exchange.query_leverage_order(pair, order_reference)
        else:
            logger.error("Failed to determine type for account [" + account + "]")
        
        return order
    