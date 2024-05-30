from datetime import datetime as dt
import time
import requests
import hmac
import hashlib
import urllib.parse

from src.logger_config import setup_logger
from src.services.exchange import Exchange, Order

logger = setup_logger(__name__)

class BinanceExchange(Exchange):
    BASE_URL = "https://api.binance.com"
    ACCECTED_STATUSES = ["FILLED", "PARTIALLY_FILLED", "CANCELED"]

    def __init__(self, name, key, secret):
        """
        Initialize the Binance class
        """
        if (name is None):
            raise ValueError("Name is required")
        if (key is None):
            raise ValueError("Key is required")
        if (secret is None):
            raise ValueError("Secret is required")
        
        self.ACC_NAME_SPOT = name + " Spot"
        self.ACC_NAME_LEVERAGE = name + " Margin"
        self.KEY=key
        self.SECRET=secret
    
    def format_pair(self, pair):
        """
        Format the pair from [BTC/USDT] for Binance [BTCUSDT]
        """
        return pair.replace("/", "").upper()
    
    def get_signature(self, params):
        """
        Generate a signature for the Binance API
        """
        query_string = urllib.parse.urlencode(params)
        m = hmac.new(self.SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()
    
    def request(self, method, endpoint, params=None, payload=None):
        """
        Make a request to the Binance API
        """
        url = self.BASE_URL + endpoint
        headers = {
            "X-MBX-APIKEY": self.KEY
        }
        
        params['timestamp'] = int(time.time() * 1000) 
        params['signature'] = self.get_signature(params)
        
        logger.debug("Making a [" + method + "] request to [" + url + "] with params [" + str(params) + "] and payload [" + str(payload) + "]")
        
        if method == "GET":
            res = requests.get(url, headers=headers, params=params)
        else:
            raise ValueError("Invalid method")
        
        return res.json()

    def parse_order(self, api_order) -> Order:
        """
        Parse the order response from the Binance API
        """
        timestamp = int(api_order["updateTime"]) / 1000
        executed_qty = float(api_order.get("executedQty"))
        average_price = float(api_order.get("cummulativeQuoteQty")) / executed_qty
        order: Order = {
            "order_id": str(api_order["orderId"]), 
            "datetime": dt.fromtimestamp(timestamp),
            "symbol": str(api_order["symbol"]), # TODO BTCUSDT should be BTC/USDT
            "side": api_order["side"].capitalize(),
            "average": average_price,
            "executed": executed_qty,
            "fee": None,
            "fee_currency": None
        }
        return order
    
    def query_spot_order(self, symbol, orderId) -> Order:
        """
        Query a spot account order
        https://binance-docs.github.io/apidocs/spot/en/#query-order-user_data
        """
        endpoint = "/api/v3/order"

        logger.info("Querying spot order [" + orderId + "] for symbol [" + symbol + "]")
        
        # Query Binance
        pair = self.format_pair(symbol)
        params = {
            "symbol": pair,
            "orderId": orderId
        }
        api_order = self.request("GET", endpoint, params=params)
        
        # Check Error
        if (api_order is None):
            raise ValueError("Failed to fetch order for account [" + self.ACC_NAME_SPOT + "], pair [" + pair + "], order reference [" + str(orderId) + "]")
        if (api_order.get("code") is not None):
            raise ValueError("Failed to fetch order for account [" + self.ACC_NAME_SPOT + "], pair [" + pair + "], order reference [" + str(orderId) + "] with code [" + str(api_order.get("code")) + "] and error [" + api_order.get("msg") + "]")
        
        # Check if the order has FILLED, PARTIALLY_FILLED, CANCELLED status 
        if (api_order["status"] not in self.ACCECTED_STATUSES):
            logger.warning("Order for account [" + self.ACC_NAME_SPOT + "], pair [" + pair + "], order reference [" + str(orderId) + "] has status [" + str(api_order.get("status")) + "] which is not accecpted, skipping...")
            return None
        
        return self.parse_order(api_order)

    def get_all_spot_orders_from(self, start_time) -> list[Order]:
        """
        Get all spot orders from the exchange from the start time
        https://binance-docs.github.io/apidocs/spot/en/#all-orders-user_data
        """
        # TODO Spot read all orders require symbol as part of the request, so we can't get all orders
        pass

    def query_leverage_order(self, symbol, orderId) -> Order:
        """
        Query a margin account order
        https://binance-docs.github.io/apidocs/spot/en/#query-margin-account-39-s-order-user_data
        """
        endpoint = "/sapi/v1/margin/order"

        logger.info("Querying margin order [" + orderId + "] for symbol [" + symbol + "]")

        # Query Binance
        pair = self.format_pair(symbol)
        params = {
            "symbol": pair,
            "orderId": orderId
        }
        api_order = self.request("GET", endpoint, params=params)
        
        # Check Error
        if (api_order is None):
            raise ValueError("Failed to fetch order for account [" + self.ACC_NAME_LEVERAGE + "], pair [" + pair + "], order reference [" + str(orderId) + "]")
        if (api_order.get("code") is not None):
            raise ValueError("Failed to fetch order for account [" + self.ACC_NAME_LEVERAGE + "], pair [" + pair + "], order reference [" + str(orderId) + "] with code [" + str(api_order.get("code")) + "] and error [" + api_order.get("msg") + "]")
        
        # Check if the order has FILLED, PARTIALLY_FILLED, CANCELLED status 
        if (api_order["status"] not in self.ACCECTED_STATUSES):
            logger.warning("Order for account [" + self.ACC_NAME_LEVERAGE + "], pair [" + pair + "], order reference [" + str(orderId) + "] has status [" + str(api_order.get("status")) + "] which is not accecpted, skipping...")
            return None
        
        return self.parse_order(api_order)
    
    def get_all_leverage_orders_from(self, start_time) -> list[Order]:
        """
        Get all margin orders from the exchange from the start time
        https://binance-docs.github.io/apidocs/spot/en/#query-margin-account-39-s-all-orders-user_data
        """
        # TODO Margin read all orders require symbol as part of the request, so we can't get all orders
        pass