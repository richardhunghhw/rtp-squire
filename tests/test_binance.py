import os
import pytest

from dotenv import load_dotenv
from src.services.binance_exchange import BinanceExchange

load_dotenv()

class TestBinance:
    def setup_method(self, method):
        name="Binance"
        key=os.getenv("BINANCE_API_KEY").split(",")[0]
        secret=os.getenv("BINANCE_API_SECRET").split(",")[0]
        self.binance = BinanceExchange(name, key, secret)
    
    # @pytest.mark.skip(reason="For manual testing only")
    def test_query_spot_order(self):
        symbol = "WIFUSDT"
        orderId = "-"
        res = self.binance.query_spot_order(symbol, orderId)
        
        assert res["order_id"] == orderId
        assert res["symbol"] == symbol
        
        # Uncomment the following line to print the response
        # print(res)
        # assert False
        
    # @pytest.mark.skip(reason="For manual testing only")
    def test_query_leverage_order(self):
        symbol = "BTCUSDT"
        orderId = "-"
        res = self.binance.query_leverage_order(symbol, orderId)
        
        assert res["order_id"] == orderId
        assert res["symbol"] == symbol
        
        # Uncomment the following line to print the response
        # print(res)
        # assert False