import os
from dotenv import load_dotenv
from src.sheets_ob import SheetsOB

load_dotenv()

class TestSheetsOB:
    def setup_method(self, method):
        id=os.getenv("GS_SS_ID")
        sheet=os.getenv("GS_SHEET_NAME")
        self.sheets = SheetsOB(id, sheet)
    
    def test_query_sheets(self):
        response = self.sheets.get_rows_with_order_references(["32913432101"])
        print(response)
        assert False