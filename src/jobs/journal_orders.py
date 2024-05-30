from notion_client import APIResponseError

from src.logger_config import setup_logger
from src.services.notion_journal import NotionJournal
from src.services.sheets_ob import SheetsOB

logger = setup_logger(__name__)

class JournalOrders:
    def __init__(self, notion: NotionJournal, sheets: SheetsOB):
        """
        Initialize the JournalOrders class
        """
        if (notion is None):
            raise ValueError("Notion is required")
        if (sheets is None):
            raise ValueError("Sheets is required")
        
        self.NOTION=notion
        self.SHEETS=sheets
    
    def run(self):
        """
        Run the job
        """
        logger.info("Running Journal Orders job...")
        
        # Query the Notion database for any entries with tag 'refresh-orders'
        entries = self.NOTION.query_db_for_refresh_orders()
        if (entries is None):
            logger.error("Failed to retrieve pending orders to refresh, exiting...")
            return

        # Process each entry
        self.process_entries(entries)
        
        logger.info("Journal Orders job completed successfully")
    
    def process_entries(self, entries):
        """
        Process each entry
        """
        if (entries is None):
            raise ValueError("Entries are required")
        
        for entry in entries: 
            try:
                self.process_entry(entry)
            except Exception as err:
                logger.error("Failed to process entry [" + entry["id"] + "] with error [" + str(err) + "], ignoring and continuing...")
                try: 
                    self.NOTION.add_unknown_error_tag(entry["id"], entry["action-tags"])
                except APIResponseError as err:
                    logger.error("Failed to add failed orders tag to entry [" + entry["id"] + "] with error [" + str(err) + "], ignoring and continuing...")
            
    def process_entry(self, entry):
        logger.info("Processing entry [" + entry["id"] + "] with [" + str(len(entry["order-references"])) + "] order references")

        # Query the Google Sheets API to get rows with matching Order References
        entry["orders"] = self.SHEETS.get_rows_with_order_references(entry["order-references"])
        
        # Delete exisiting table block if it exists
        if (entry["table-block-id"]):
            try: 
                self.NOTION.delete_block(entry["table-block-id"])
            except APIResponseError as err:
                logger.error("Failed to delete table block [" + entry["table-block-id"] + "] with error [" + str(err) + "], ignoring and creating a new block...")
        entry["table-block-id"] = None
        
        # Sum the columns Effect, Total (inc. Fees)
        effect = 0
        total = 0
        missing = False
        for order in entry["orders"][1:]:
            if order[6] is not None and order[6] != "" and order[7] is not None and order[7] != "":
                effect += float(order[6].replace(',', ''))
                total += float(order[7].replace(',', ''))
            else:
                missing = True
        entry["orders"].append(["", "", "", "", "", "Net:", str(round(effect, 2)), str(round(total, 2)), "", "", "", "", ""])
        
        # Create a new table block with the orders
        if (entry["orders"]):
            entry["table-block-id"] = self.NOTION.create_orders_table_block(entry["id"], entry["orders"])
        else:
            logger.warning("No orders found for entry [" + entry["id"] + "]")
        
        # Update the entry with the new table block id
        self.NOTION.update_entry_table_block_id(entry["id"], entry["table-block-id"])
        
        # Remove the refresh-orders tag
        tags = [tag["name"] for tag in entry["action-tags"]]
        print(tags)
        self.NOTION.remove_refresh_orders_tag(entry["id"])
        # Add a missing orders tag if any orders are missing
        if (missing):
            self.NOTION.add_missing_orders_tag(entry["id"])