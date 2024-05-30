import time

from src.services.exchange import Exchange

def get_exchange_type(account: str, exchanges: dict[str, Exchange]) -> tuple[Exchange, str]:
    """
    Get the exchange
    [<ACCOUNT_NAME> <TYPE>]
    """        
    # Determine the exchange
    exchange = None
    for exchange_name in exchanges:
        if account.startswith(exchange_name):
            exchange = exchanges[exchange_name]
    return exchange, account.split(" ")[2]

def get_rounded_time() -> int:
    """
    Get the current time rounded to the previous quarter hour in epoch time
    """
    current_time = time.time()
    return (int(current_time - (current_time % 900)) - 900) * 1000