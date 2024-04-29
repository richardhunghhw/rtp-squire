import os

from dotenv import load_dotenv

from src.logger_config import setup_logger
from src.jobs.journal_orders import JournalOrders
from src.notion_journal import NotionJournal
from src.sheets_ob import SheetsOB

logger = setup_logger(__name__)

# Load environment variables
load_dotenv()


class Main:
    def __init__(self):
        """
        Initialize the main class
        """
        # Initialize the Notion API
        token=os.getenv("NOTION_TOKEN")
        database_id=os.getenv("NOTION_DATABASE_ID")
        self.NOTION = NotionJournal(token, database_id)
        
        # Initialize the Google Sheets API
        ss_id=os.getenv("GS_SS_ID")
        sheet_name=os.getenv("GS_SHEET_NAME")
        self.SHEETS = SheetsOB(ss_id, sheet_name)
        
        # Initialize jobs
        self.JOBS = []
        self.JOBS.append(JournalOrders(self.NOTION, self.SHEETS))

    def run(self):
        logger.info("Running RTP Squire to the moon!")
        
        # Run the Journal Orders job
        for job in self.JOBS:
            job.run()
        
        logger.info("Done running RTP Squire to the moon!")


if __name__ == "__main__":
    main = Main()
    main.run()