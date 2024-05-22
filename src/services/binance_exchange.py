import time
import requests
import hmac
import hashlib
import urllib.parse

from src.logger_config import setup_logger
from src.services.exchange import Exchange

logger = setup_logger(__name__)

class BinanceExchange(Exchange):
    BASE_URL = "https://api.binance.com"

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
        self.ACC_NAME_MARGIN = name + " Margin"
        self.KEY=key
        self.SECRET=secret
    
    def format_pair(self, pair):
        """
        Format the pair for Binance
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

    def query_spot_order(self, symbol, orderId):
        """
        Query a spot order
        https://binance-docs.github.io/apidocs/spot/en/#query-order-user_data
        """
        endpoint = "/api/v3/order"

        logger.info("Querying spot order [" + orderId + "] for symbol [" + symbol + "]")

        params = {
            "symbol": symbol,
            "orderId": orderId
        }
        return self.request("GET", endpoint, params=params)

    def query_margin_order(self, symbol, orderId):
        """
        Query a margin order
        https://binance-docs.github.io/apidocs/spot/en/#query-margin-account-39-s-order-user_data
        """
        endpoint = "/sapi/v1/margin/order"

        logger.info("Querying margin order [" + orderId + "] for symbol [" + symbol + "]")

        params = {
            "symbol": symbol,
            "orderId": orderId
        }
        return self.request("GET", endpoint, params=params)
    