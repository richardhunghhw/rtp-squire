from datetime import datetime as dt
from typing import Optional

from src.logger_config import setup_logger
from src.services.exchange import Exchange
from src.services.sheets_ob import SheetsOB
from src.helper import get_exchange_type, get_rounded_time

logger = setup_logger(__name__)

class NewOrders:
    """
    Fetches new orders from Exchange APIS and updates the Google Sheets
    """
    def __init__(self, sheets: SheetsOB, exchanges: list[Exchange]):
        """
        Initialize the NewOrders class
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
        logger.info("Running New Orders job...")

        # Query Google Sheets for the last updated time
        last_updated = self.SHEETS.get_no_last_updated()
        
        # Accumulate orders from each account
        account_orders = {}
        for account in last_updated.keys():
            try: 
                timestamp: dt = None
                if (last_updated[account] is not None):
                    # Convert 27/05/2024 00:00:00 to datetime
                    timestamp = dt.strptime(last_updated[account], "%d/%m/%Y %H:%M:%S")
                
                orders = self.run_for_account(account, timestamp)

                if (orders is None or len(orders) == 0):
                    logger.info(f"No new orders found for account [{account}]")
                    continue
                else:
                    logger.info(f"Found [{len(orders)}] new orders for account [{account}]")
                    account_orders[account] = orders
            except Exception as e:
                logger.error(f"Error running New Orders job for account [{account}] with exception [{e}], skipping and continuing...")        
        logger.info(f"Finished running New Orders job for [{len(account_orders)}] accounts, with [{sum([len(v) for v in account_orders.values()])}] new orders found in total")
        
        # Update Google Sheets with the new orders
        if (len(account_orders) > 0):
            self.SHEETS.update_new_orders(account_orders)
            logger.info("Updated Google Sheets with new orders")
        else:
            logger.info("No new orders found, Google Sheets not updated")
        
    def run_for_account(self, account: str, last_updated: Optional[dt]):
        """
        Run the job for a specific account
        """
        logger.info(f"Running New Orders job for account [{account}] since [{last_updated}]...")
        
        exchange: Exchange
        type: str
        exchange, type = get_exchange_type(account, self.EXCHANGES)
        
        # Check if the start time is None
        start_time = get_rounded_time() if last_updated is None else int((last_updated).timestamp() * 1000)
        
        # Get all orders from the exchange
        if type == "Spot":
            return exchange.get_all_spot_orders_from(start_time)
        elif type in ["Margin", "Futures"]:
            return exchange.get_all_leverage_orders_from(start_time)
        else:
            raise ValueError("Invalid exchange type")
    