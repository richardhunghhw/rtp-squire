from datetime import datetime as dt
import time
import requests
import hmac
import hashlib

from src.helper import get_rounded_time
from src.logger_config import setup_logger
from src.services.exchange import Exchange, Order

logger = setup_logger(__name__)

class MexcExchange(Exchange):
    SPOT_BASE_URL = "https://api.mexc.com" # SpotV3
    FUTURES_BASE_URL = "https://contract.mexc.com"
    
    def __init__(self, name, key, secret):
        """
        Initialize the Mexc class
        """
        if (name is None):
            raise ValueError("Name is required")
        if (key is None):
            raise ValueError("Key is required")
        if (secret is None):
            raise ValueError("Secret is required")
        
        self.ACC_NAME_SPOT = name + " Spot"
        self.ACC_NAME_LEVERAGE = name + " Futures"
        self.api_key = key
        self.api_secret = secret
    
    def format_pair(self, pair) -> str:
        """
        Format the pair from [BTC/USDT] for Mexc [BTC_USDT]
        """
        return pair.replace("/", "_").upper()
    
    def get_signature(self, timestamp, params) -> str:
        """
        Generate a signature for the Mexc API
        """
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())]) if params is not None else ""
        sig_string = self.api_key + timestamp + query_string
        return hmac.new(self.api_secret.encode('utf-8'), sig_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def request(self, method, url, params=None, payload=None) -> dict:
        """
        Make a request to the Mexc API
        """
        timestamp = str(int(time.time() * 1000))
        headers = {
            "ApiKey": self.api_key,
            "Request-Time": timestamp,
            "Signature": self.get_signature(timestamp, params),
            "Content-Type": "application/json",
        }
        if params is not None:
            params["timestamp"] = timestamp
        
        logger.debug("Making a [" + method + "] request to [" + url + "] with params [" + str(params) + "] and payload [" + str(payload) + "]")
        
        if method == "GET":
            res = requests.get(url, headers=headers, params=params)
        else:
            raise ValueError("Invalid method")
        
        return res.json()
    
    def parse_order(self, api_order) -> Order:
        """
        Parse the order
        """
        timestamp = int(api_order["updateTime"]) / 1000
        order = {
            "order_id": api_order["orderId"],
            "datetime": dt.fromtimestamp(timestamp),
            "symbol": api_order["symbol"].replace("_", "/"),
            "side": "Buy" if api_order["side"] in [1, 2] else "Sell",
            "average": api_order["price"],
            "executed": api_order["vol"],
            "fee": api_order["takerFee"] + api_order["makerFee"],
            "fee_currency": api_order["feeCurrency"]
        }
        return order
    
    def query_spot_order(self, symbol, orderId) -> list[Order]:
        """
        Query a spot account order
        https://mexcdevelop.github.io/apidocs/spot_v3_en/#query-order
        TODO this is currently not working
        """
        endpoint = "/api/v1/order"
        url = self.SPOT_BASE_URL + endpoint
        
        logger.info("Querying spot order [" + orderId + "] for symbol [" + symbol + "]")
        
        # Query Mexc
        pair = self.format_pair(symbol)
        params = {
            "symbol": pair,
            "orderId": orderId,
        }
        api_order = self.request("GET", url, params=params)
        print(api_order)
        
        # Check Error
        if "code" not in api_order or api_order["code"] != 0:
            logger.error("Failed to fetch spot order for account [" + self.ACC_NAME_SPOT + "], pair [" + pair + "], order reference [" + orderId + "] with code [" + str(api_order["code"]) + "] and error [" + str(api_order["message"]) + "]")
            return None
        
        return self.parse_order(api_order)
            
    def get_all_spot_orders_from(self, start_time: int = None) -> list[Order]:
        """
        Get all spot orders from the exchange from the start time
        """
        # TODO Spot read all orders require symbol as part of the request, so we can't get all orders
        pass

    def query_leverage_order(self, symbol, orderId) -> Order:
        """
        Query a futures account order
        https://mexcdevelop.github.io/apidocs/contract_v1_en/#query-the-order-based-on-the-order-number
        """
        endpoint = "/api/v1/private/order/get/{order_id}"
        url = self.FUTURES_BASE_URL + endpoint.format(order_id=orderId)

        logger.info("Querying futures order [" + orderId + "] for symbol [" + symbol + "]")

        # Query Mexc
        api_order = self.request("GET", url)
        
        # Check Error
        if "code" not in api_order or api_order["code"] != 0:
            logger.error("Failed to fetch futures order for account [" + self.ACC_NAME_LEVERAGE + "], pair [" + symbol + "], order reference [" + orderId + "] with code [" + str(api_order["code"]) + "] and error [" + str(api_order["message"]) + "]")
            return None
        
        return self.parse_order(api_order["data"])
    
    def get_all_leverage_orders_from(self, start_time: int = None) -> list[Order]:
        """
        Get all futures orders from the exchange from the start time
        """
        # Check if the start time is None
        if (start_time is None):
            start_time = get_rounded_time()
        
        logger.info("Getting all futures orders starting from [" + str(start_time) + "]")
        
        # Get all orders
        api_orders = self.futures_client.history_orders(start_time=start_time)
        if "code" not in api_orders or api_orders["code"] != 0:
            logger.error("Failed to fetch orders with error [" + api_orders["message"] + "]")
            return None
        if api_orders is None or "data" not in api_orders or "resultList" not in api_orders["data"]:
            logger.info("No futures orders found since [" + str(start_time) + "]")
            return None
        
        # Parse the orders
        orders = []
        for order in api_orders["data"]["resultList"]:
            # Ignore order state 1, 4, and 5
            # Order state: 1 uninformed, 2 uncompleted, 3 completed, 4 cancelled, 5 invalid; multiple separate by ','
            if order["state"] in [1, 4, 5]:
                continue
            
            orders.append(self.parse_order(order))
        
        logger.info("Found [" + str(len(orders)) + "] futures orders since [" + str(start_time) + "]")
        return orders