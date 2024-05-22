from abc import ABC, abstractmethod

class Exchange(ABC):
    def format_pair(self, pair):
        """
        Format the pair for the exchange
        """
        pass
    
    def query_spot_order(self, symbol, orderId):
        """
        Query a spot order
        """
        pass
    
    def query_margin_order(self, symbol, orderId):
        """
        Query a margin order
        """
        pass