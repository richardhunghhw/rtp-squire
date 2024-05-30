import os
import pytest

from dotenv import load_dotenv
from src.services.mexc_exchange import MexcExchange

load_dotenv()

class TestMexc:
    def setup_method(self, method):
        name="MEXC"
        key=os.getenv("MEXC_API_KEY")
        secret=os.getenv("MEXC_API_SECRET")
        self.mexc = MexcExchange(name, key, secret)
    
    # @pytest.mark.skip(reason="For manual testing only")
    def test_query_spot_order(self):
        symbol = "ETH/USDT"
        orderId = "-"
        res = self.mexc.query_spot_order(symbol, orderId)
        
        assert res["order_id"] == orderId
        assert res["symbol"] == symbol
        
        # Uncomment the following line to print the response
        # print(res)
        # assert False
    
    # @pytest.mark.skip(reason="For manual testing only")
    def test_query_leverage_order(self):
        symbol = "BTC/USDT"
        orderId = "-"
        res = self.mexc.query_leverage_order(symbol, orderId)
        
        assert res["order_id"] == orderId
        assert res["symbol"] == symbol
        
        # Uncomment the following line to print the response
        # print(res)
        # assert False
    
    @pytest.mark.skip(reason="For manual testing only")
    def test_get_all_leverage_orders_from(self):
        res = self.mexc.get_all_leverage_orders_from(1716829200000)
        print(res)
        assert False