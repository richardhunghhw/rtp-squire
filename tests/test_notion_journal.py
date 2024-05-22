import os
import csv
import pytest

from dotenv import load_dotenv
from src.services.notion_journal import NotionJournal

load_dotenv()

class TestNotionAPI:
    def setup_method(self, method):
        token=os.getenv("NOTION_TOKEN")
        database_id=os.getenv("NOTION_DATABASE_ID")
        self.notion = NotionJournal(token, database_id)
    
    @pytest.mark.skip(reason="For manual testing only")
    def test_query_db_for_refresh_orders(self):
        response = self.notion.query_db_for_refresh_orders()
        print(response)
        assert False
    
    @pytest.mark.skip(reason="For manual testing only")
    def test_create_orders_table_block(self):        
        with open('tests/data/sample_orders.csv', newline='') as csvfile:
            data = list(csv.reader(csvfile))

        response = self.notion.create_orders_table_block("-", data)
        print(response)
        assert False
    
    @pytest.mark.skip(reason="For manual testing only")
    def test_delete_block(self):
        response = self.notion.delete_block("-")
        print(response)
        assert False