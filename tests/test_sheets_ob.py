import os
from dotenv import load_dotenv
from src.services.sheets_ob import SheetsOB

load_dotenv()

class TestSheetsOB:
    def setup_method(self, method):
        id=os.getenv("GS_SS_ID")
        ob_sheet=os.getenv("GS_OB_SHEET_NAME")
        no_sheet=os.getenv("GS_NEWORDERS_SHEET_NAME")
        user_token_file="./token.json"
        user_secret_file="./credentials.json"
        self.sheets = SheetsOB(id, sheet, None, user_token_file, user_secret_file)
    
    def test_query_sheets(self):
        response = self.sheets.get_rows_with_order_references(["-"])
        print(response)
        assert False
        
    def test_get_rows_pending_refresh(self):
        response = self.sheets.get_rows_pending_rtps_refresh()
        print(response)
        assert False