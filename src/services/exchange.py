from abc import ABC, abstractmethod
from datetime import datetime as dt
from typing import Literal, NotRequired, TypedDict

class Order(TypedDict):
    order_id: str
    datetime: dt
    symbol: str # The trading pair in the format of "BTC/USDT"
    side: Literal["Buy", "Sell"]
    average: float # Average price of the order
    executed: float # Executed quantity of the order
    fee: NotRequired[float]
    fee_currency: NotRequired[str]

class Exchange(ABC):
    def query_spot_order(self, symbol, orderId) -> Order:
        """
        Query a spot account order
        """
        pass
    
    def get_all_spot_orders_from(self, start_time) -> list[Order]:
        """
        Get all spot orders from the exchange from the start time
        """
        pass
    
    def query_leverage_order(self, symbol, orderId) -> Order:
        """
        Query a leveraged (margin, futures) order
        """
        pass
    
    def get_all_leverage_orders_from(self, start_time) -> list[Order]:
        """
        Get all leveraged (margin, futures) orders from the exchange from the start time
        """
        pass
    