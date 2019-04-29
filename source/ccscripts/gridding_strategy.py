import operator
import datetime
import numpy
import talib
import csv

from pathlib import Path

from strategy import *
from market_provider import *
from indices_provider import *

#
# Gridding 策略：格栅加减仓
#
class GriddingStrategy(QuantifyStrategy):
    
    
    def __init__(self, strategy_id, strategy_config):
        QuantifyStrategy.__init__(self, strategy_id, strategy_config)
        self._data_path = 'ccdatastore/Strategy/GriddingStrategy/'
    
    # Balance is the current positions/cash balance for one account
    # AccountInfo contains some information for that account needed for the strategy to consider, e.g. LastTransactionTime
    # Returns: <transaction list>
    def execute_decision(self, portfolio, account_info):
    
        if (self._is_too_soon_from_last_transaction(account_info)):
            print("GriddingStrategy: too soon from last transaction, ignore it.")
            return None
    
        # 计算当前持仓的所有市值，计算平均仓位

        total_value = portfolio.get_cash_balance()
        total_space_count = len(self._config.coin_id_list()) + 1
        
        # 首先获取所有需要的币的当前价格
        coin_prices = {}
        coin_values = {}
        coin_price = MarketProvider.get_current_price("USDT")
            
        coin_list = list(set(portfolio.get_coin_ids()) | set(self._config.coin_id_list()) | set(["USDT"]))
        for coin_id in coin_list:
            coin_prices[coin_id] = MarketProvider.get_current_price(coin_id)
            coin_values[coin_id] = coin_prices[coin_id] * portfolio.get_coin_position(coin_id)
            total_value += coin_values[coin_id]

        even_value = total_value / total_space_count

        selling_coins = {}
        buying_coins = {}
        for coin_id in self._config.coin_id_list():
            
            if (coin_id == "USDT"):
                continue

            if (coin_values[coin_id] > even_value):
                # 判断币的涨幅是否满足卖出条件
                delta_ten_percent = int((coin_values[coin_id] - even_value) / even_value * 10) / 10
                if (delta_ten_percent > 0):
                    # 确定卖出该币
                    selling_coins[coin_id] = delta_ten_percent * even_value

            elif (coin_values[coin_id] < even_value):
                # 判断币的跌幅是否满足买入条件
                delta_ten_percent = int((even_value - coin_values[coin_id]) / even_value * 10) / 10
                if (delta_ten_percent > 0):
                    # 确定卖出该币
                    buying_coins[coin_id] = delta_ten_percent * even_value


        new_transactions = []
        # 执行卖出操作
        transaction = MarketProvider.compose_sell_all_transaction(portfolio, "USDT")
        if (transaction != None):
            new_transactions.append(transaction)
        
        for coin_id in selling_coins.keys():
            coin_amount = selling_coins[coin_id] / coin_prices[coin_id]
            transaction = MarketProvider.compose_sell_transaction(portfolio, coin_id, coin_amount)
            if (transaction != None):
                new_transactions.append(transaction)
        
        # 执行买入操作
        for coin_id in buying_coins.keys():
            if (portfolio.get_cash_balance() < buying_coins[coin_id]):
                continue
            transaction = MarketProvider.compose_buy_transaction(portfolio, coin_id, buying_coins[coin_id])
            if (transaction != None):
                new_transactions.append(transaction)
        
        # 剩余现金全部买入USDT
        if (portfolio.get_cash_balance() > 0):
            transaction = MarketProvider.compose_buy_transaction(portfolio, "USDT", portfolio.get_cash_balance())
            if (transaction != None):
                new_transactions.append(transaction)
            
        return new_transactions
    

class GriddingBtcStrategy(GriddingStrategy):
    def __init__(self):
        GriddingStrategy.__init__(self, "Gridding_Btc", StrategyConfig.generate_config(["BTC"], 1440))

        
class GriddingBtcEthStrategy(GriddingStrategy):
    def __init__(self):
        GriddingStrategy.__init__(self, "Gridding_BtcEth", StrategyConfig.generate_config(["BTC", "ETH"], 1440))


class GriddingBtcEthLtcXrpZecStrategy(GriddingStrategy):
    def __init__(self):
        GriddingStrategy.__init__(self, "Gridding_BtcEthLtcXrpZec", StrategyConfig.generate_config(["BTC", "ETH", "LTC", "XRP", "ZEC"], 1440))
