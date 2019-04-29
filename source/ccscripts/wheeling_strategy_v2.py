from pathlib import Path
import datetime
import numpy
import talib

from strategy import *
from transaction_provider import *
from market_provider import *

class WheelingStrategy(QuantifyStrategy):
    
    def __init__(self, strategy_id, strategy_config):
        QuantifyStrategy.__init__(self, strategy_id, strategy_config)
        self._data_path = 'ccdatastore/Strategy/WheelingStrategy/'
    
    
    # Balance is the current positions/cash balance for one accountInfo
    # AccountInfo contains some information for that account needed for the strategy to consider, e.g. LastTransactionTime
    def execute_decision(self, portfolio, account_info):
    
        if (self._is_too_soon_from_last_transaction(account_info)):
            return None
    
    
        selected_coin_index = -1
        selected_ppo = -10
        selected_price = 0
        
        coin_id_list = self._config.coin_id_list()
        
        # Initial the prices and PPO values
        for cindex in range(len(coin_id_list)):
            coin_price = MarketProvider.get_last_n_price(coin_id_list[cindex], 20)
            coin_ppo = talib.PPO(coin_price, fastperiod=3, slowperiod=6, matype=0)
            if (selected_coin_index < 0) or (selected_ppo < coin_ppo[-1]):
                selected_coin_index = cindex
                selected_ppo = coin_ppo[-1]
                selected_price = coin_price[-1]
                
        selected_coin_id = coin_id_list[selected_coin_index]
        
        #return selected_coin_index, selected_coin_id, selected_ppo, selected_price
        
        new_transactions = []
        
        if (selected_ppo < -9.0):
        
            # Not good, sell all coins to cash
            if (len(portfolio.get_coin_ids()) > 0):
                for coin_id in portfolio.get_coin_ids():
                    transaction = MarketProvider.compose_sell_all_transaction(portfolio, coin_id)
                    if (transaction != None):
                        new_transactions.append(transaction)
                    
            
        else:
            # Sell the coins not selected, and buy selected with cash value
            if (len(portfolio.get_coin_ids()) > 0):
                holding_coin_ids = list(portfolio.get_coin_ids()).copy()
                for coin_id in holding_coin_ids:
                    if (selected_coin_id == coin_id or portfolio.get_coin_position(coin_id) <= 0):
                        continue
                    transaction = MarketProvider.compose_sell_all_transaction(portfolio, coin_id)
                    if (transaction != None):
                        new_transactions.append(transaction)
                        
            
            # Buy new coin with cash
            if (selected_coin_index >= 0 and selected_price > 0):
                transaction = MarketProvider.compose_buy_transaction(portfolio, selected_coin_id, portfolio.get_cash_balance())
                if (transaction != None):
                    new_transactions.append(transaction)
            
            
        return new_transactions
        
        

class WheelingBtcEthStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "Wheeling_BtcEth", StrategyConfig.generate_config(["BTC", "ETH"], 1440))


class WheelingBtcUsdtStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "Wheeling_BtcUsdt", StrategyConfig.generate_config(["BTC", "USDT"], 1440))


class WheelingBtcEthUsdtLtcStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "Wheeling_BtcEthUsdtLtc", StrategyConfig.generate_config(["BTC", "ETH", "USDT", "LTC"], 1440))


class WheelingBtcEthUsdtLtcXrpZecStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "Wheeling_BtcEthUsdtLtcXrpZec", StrategyConfig.generate_config(["BTC", "ETH", "USDT", "LTC", "XRP", "ZEC"], 1440))
