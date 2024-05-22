import os
import pytest

from dotenv import load_dotenv
from src.services.binance_exchange import BinanceExchange

load_dotenv()

class TestBinance:
    def setup_method(self, method):
        key=os.getenv("BINANCE_1_API_KEY")
        secret=os.getenv("BINANCE_1_API_SECRET")
        self.binance = BinanceExchange(key, secret)
    
    @pytest.mark.skip(reason="For manual testing only")
    def test_query_spot_order(self):
        symbol = "WIFUSDT"
        orderId = "-"
        res = self.binance.query_spot_order(symbol, orderId)
        print(res)
        assert False
        
    # @pytest.mark.skip(reason="For manual testing only")
    def test_query_margin_order(self):
        symbol = "BTCUSDT"
        orderId = "-"
        res = self.binance.query_margin_order(symbol, orderId)
        print(res)
        assert False