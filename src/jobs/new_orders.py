from datetime import datetime as dt

from src.logger_config import setup_logger
from src.services.exchange import Exchange
from src.services.sheets_ob import SheetsOB
from src.helper import dt_to_str, get_exchange_type, get_rounded_time

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
        last_updated_if_none = get_rounded_time()
        logger.info(f"Default last updated time is [{dt_to_str(last_updated_if_none)}] for accounts with no last updated time")
        
        if (last_updated is None or len(last_updated) == 0):
            raise ValueError("No accounts found! This is weird...")
        
        # Accumulate orders from each account
        account_orders = {}
        for account in last_updated.keys():
            try: 
                timestamp: dt = None
                if (last_updated[account] is not None):
                    # Convert 27/05/2024 00:00:00 to datetime
                    timestamp = dt.strptime(last_updated[account], "%d/%m/%Y %H:%M:%S")
                else: 
                    timestamp = last_updated_if_none
                
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
        
        # Update Google Sheets with the new orders, regardless if there are any (clears the existing data)
        self.SHEETS.update_new_orders(account_orders)
        logger.info("Updated Google Sheets with new orders")
        
        # Check the last_updated time for each account and update Google Sheets where last_updated is None
        for account in last_updated.keys():
            if (last_updated[account] is None):
                self.SHEETS.update_no_last_updated(account, last_updated_if_none)
        
    def run_for_account(self, account: str, start_time: dt):
        """
        Run the job for a specific account
        """
        if (account is None):
            raise ValueError("Account is required")
        if (start_time is None):
            raise ValueError("Start time is required")
        
        logger.info(f"Running New Orders job for account [{account}] since [{start_time}]...")
        
        # Convert datetime to epoch time
        timestamp = int(start_time.timestamp() * 1000)
        
        exchange: Exchange
        type: str
        exchange, type = get_exchange_type(account, self.EXCHANGES)
        
        # Get all orders from the exchange
        if type == "Spot":
            return exchange.get_all_spot_orders_from(timestamp)
        elif type in ["Margin", "Futures"]:
            return exchange.get_all_leverage_orders_from(timestamp)
        else:
            raise ValueError("Invalid exchange type")
    