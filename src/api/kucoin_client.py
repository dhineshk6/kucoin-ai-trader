from typing import Dict, List
import time
from kucoin_futures.client import Market, Trade, User
from config.config import Config

class KuCoinClient:
    def __init__(self):
        self.market_client = Market()
        self.trade_client = Trade(
            key=Config.API_KEY,
            secret=Config.API_SECRET,
            passphrase=Config.API_PASSPHRASE
        )
        self.user_client = User(
            key=Config.API_KEY,
            secret=Config.API_SECRET,
            passphrase=Config.API_PASSPHRASE
        )

    def get_active_symbols(self) -> List[str]:
        """Get active trading symbols with sufficient volume"""
        contracts = self.market_client.get_contracts_list()
        active_symbols = []
        
        for contract in contracts:
            if float(contract['turnover24h']) >= Config.MIN_VOLUME_USD:
                active_symbols.append(contract['symbol'])
        
        return active_symbols

    def get_account_balance(self) -> float:
        """Get account balance in USDT"""
        account_info = self.user_client.get_account_overview()
        return float(account_info['availableBalance'])

    def place_order(self, symbol: str, side: str, leverage: int, 
                   size: float, price: float = None) -> Dict:
        """Place a new order"""
        order_params = {
            'symbol': symbol,
            'side': side,
            'leverage': leverage,
            'size': size,
        }
        
        if price:
            order_params['price'] = price
            order_params['type'] = 'limit'
        else:
            order_params['type'] = 'market'
            
        return self.trade_client.create_order(**order_params)