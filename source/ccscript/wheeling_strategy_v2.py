from ccdata import *
from pathlib import Path
import datetime
import numpy
import talib
from strategy import *
from transaction_provider import *


class WheelingStrategy(QuantifyStrategy):
    
    def __init__(self, strategyId, strategy_config):
        QuantifyStrategy.__init__(self, strategyId, strategy_config)
        self.data_path = 'ccdatastore/Strategy/WheelingStrategy/'
    
    
    # Balance is the current positions/cash balance for one accountInfo
    # AccountInfo contains some information for that account needed for the strategy to consider, e.g. LastTransactionTime
    def execute_with_balance(self, balance, account_info):
    
        if (self.is_too_soon_from_last_transaction(account_info)):
            return None
    
    
        selected_coin_index = -1
        selected_ppo = -10
        selected_price = 0
        
        coin_id_list = self.config.coin_id_list()
        
        # Initial the prices and PPO values
        for cindex in range(len(coin_id_list)):
            coin_price = get_one(coin_id_list[cindex],"D","close")
            coin_price = coin_price[-20:]
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
            if (len(balance.get_coin_ids()) > 0):
                for coin_id in balance.get_coin_ids():
                    transaction = TransactionProvider.compose_sell_all_transaction(balance, coin_id)
                    if (transaction != None):
                        new_transactions.append(transaction)
                    
            
        else:
            # Sell the coins not selected, and buy selected with cash value
            if (len(balance.get_coin_ids()) > 0):
                holding_coin_ids = list(balance.get_coin_ids()).copy()
                for coin_id in holding_coin_ids:
                    if (selected_coin_id == coin_id or balance.get_coin_position(coin_id) <= 0):
                        continue
                    transaction = TransactionProvider.compose_sell_all_transaction(balance, coin_id)
                    if (transaction != None):
                        new_transactions.append(transaction)
                        
            
            # Buy new coin with cash
            if (selected_coin_index >= 0 and selected_price > 0):
                transaction = TransactionProvider.compose_buy_transaction(balance, selected_coin_id, balance.get_cash_balance())
                if (transaction != None):
                    new_transactions.append(transaction)
            
            
        return new_transactions
        
        

class BtcEthWheelingStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "BtcEth", StrategyConfig.generate_config(["BTC", "ETH"], 1440))


class BtcUsdtWheelingStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "BtcUsdt", StrategyConfig.generate_config(["BTC", "USDT"], 1440))


class BtcEthUsdtLtcWheelingStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "BtcEthUsdtLtc", StrategyConfig.generate_config(["BTC", "ETH", "USDT", "LTC"], 1440))


class BtcEthUsdtLtcXrpZecWheelingStrategy(WheelingStrategy):
    def __init__(self):
        WheelingStrategy.__init__(self, "BtcEthUsdtLtcXrpZec", StrategyConfig.generate_config(["BTC", "ETH", "USDT", "LTC", "XRP", "ZEC"], 1440))
