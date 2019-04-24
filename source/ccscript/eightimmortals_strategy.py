import operator
import datetime
import numpy
import talib
import csv

from pathlib import Path

from ccdata import *
from strategy import *
from transaction_provider import *
from indices_provider import *

class EightImmortalsStrategy(QuantifyStrategy):
    
    SIGNAL_NONE = 0
    SIGNAL_BUY = 1
    SIGNAL_SELL = -1
    
    MAX_HOLDING_COIN = 3
    
    def __init__(self, strategyId, strategy_config):
        QuantifyStrategy.__init__(self, strategyId, strategy_config)
        self.data_path = 'ccdatastore/Strategy/EightImmortalsStrategy/'
    
    
    # Balance is the current positions/cash balance for one account
    # AccountInfo contains some information for that account needed for the strategy to consider, e.g. LastTransactionTime
    # Returns: <transaction list>
    def execute_with_balance(self, balance, account_info):
    
        if (self.is_too_soon_from_last_transaction(account_info)):
            print("EightImmortalsStrategy: too soon from last transaction, ignore it.")
            return None
    
        signal = self.query_signal()
        print("EightImmortalsStrategy: buy/sell signal is " + str(signal))
            
        if (signal == EightImmortalsStrategy.SIGNAL_BUY):
            return self.execute_buy(balance)
        
        elif (signal == EightImmortalsStrategy.SIGNAL_SELL):
            return self.execute_sell(balance)
            
        else:
            # Do nothing, stand by
            return None
    
        
    # 获取买入/卖出信号
    def query_signal(self):
        
        print("EightImmortalsStrategy: Begin query signal.")
        
        indices_provider = IndicesProvider()
        cci30_data = indices_provider.get_cci30_indices(datetime.datetime.utcnow())
        if (cci30_data == None):
            print("Error while retrieving cci30 data.")
            return EightImmortalsStrategy.SIGNAL_NONE
        
        ma40 = talib.MA(cci30_data["close"], timeperiod=40, matype=0)
        
        # 买入信号：
        # 1. T-2和T-1交易日中的综合指数均大于MA40
        # 2. T日的综合指数不被T-2日包含
        if (cci30_data["close"][-3] > ma40[-3] and cci30_data["close"][-2] > ma40[-2] and
            (cci30_data["high"][-1] > cci30_data["high"][-3] or cci30_data["low"][-1] < cci30_data["low"][-3])):
            return EightImmortalsStrategy.SIGNAL_BUY
            
        # 卖出信号：
        # 1. T-2和T-1交易日中的综合指数均小于MA40
        # 2. T日的综合指数不被T-2日包含
        elif (cci30_data["close"][-3] < ma40[-3] and cci30_data["close"][-2] < ma40[-2] and
              (cci30_data["high"][-1] > cci30_data["high"][-3] or cci30_data["low"][-1] < cci30_data["low"][-3])):
            return EightImmortalsStrategy.SIGNAL_SELL

        else:
            return EightImmortalsStrategy.SIGNAL_NONE
    
    
    # 用USDT买入币种
    # Returns: <transaction list>, <new_balance>
    def execute_buy(self, balance):
        
        print("EightImmortalsStrategy: Begin execute buy.")
        
        if (balance.cash_balance <= 0 and balance.get_coin_position("USDT") <= 0):
            # No Cash or USDT, just leave it
            print("EightImmortalsStrategy: No cash or USDT, just leave it.")
            return None
    
    
        # 选出当前势头最好的三个币
        top_coins = self.pick_top_coins()
        print("EightImmortalsStrategy: Got top coins: " + str(top_coins))
            
        
        # 和当前持有的币合并，最大的持有币种不超过MAX_HOLDING_COIN
        existing_coins = balance.get_coin_ids()
        print("EightImmortalsStrategy: Current holding coins: " + str(existing_coins))
        
        set_old = set(top_coins) & set(existing_coins)
        new_coins = list(set(top_coins) - set_old)
        set_new = new_coins[:EightImmortalsStrategy.MAX_HOLDING_COIN - len(existing_coins)] if EightImmortalsStrategy.MAX_HOLDING_COIN > len(existing_coins) else []
        candidate_coins = list(set_old) + set_new
        print("EightImmortalsStrategy: Buy candidate coins: " + str(candidate_coins))
        
        
        if (len(candidate_coins) == 0):
            # 没有空间买入新的币了，取消操作
            print("EightImmortalsStrategy: No space for new coins, cancel this operation")
            return None
    
        new_transactions = []
        
        # 卖出USDT
        print("EightImmortalsStrategy: sell all USDT.")
        transaction = TransactionProvider.compose_sell_all_transaction(balance, "USDT")
        if (transaction != None):
            new_transactions.append(transaction)
        
        # 平均买入新选定的币
        print("EightImmortalsStrategy: evenly buy candidate coins.")
        even_cash_value = balance.cash_balance / len(candidate_coins)
        for candidate_coin in candidate_coins:
            
            transaction = TransactionProvider.compose_buy_transaction(balance, candidate_coin, even_cash_value)
            if (transaction != None):
                new_transactions.append(transaction)
        
        print("EightImmortalsStrategy: completed buy operation, totally new transactions: " + str(len(new_transactions)))
        return new_transactions
        
    
    # 卖出当前持有的所有币，换取USDT
    #Returns: <transaction list>, <new_balance>
    def execute_sell(self, balance):
    
        print("EightImmortalsStrategy: Begin execute sell.")
        
        new_transactions = []
        holding_coin_ids = list(balance.get_coin_ids()).copy()
        for coin_id in holding_coin_ids:
         
            if (coin_id == "USDT" or balance.get_coin_position(coin_id) <= 0):
                continue
            
            print("EightImmortalsStrategy: selling coin " + coin_id + ".")
        
            # Sell the Coin
            transaction = TransactionProvider.compose_sell_all_transaction(balance, coin_id)
            if (transaction != None):
                new_transactions.append(transaction)  
            
        # 买入USDT
        print("EightImmortalsStrategy: buy USDT with all cashes.")
        transaction = TransactionProvider.compose_buy_transaction(balance, "USDT", balance.cash_balance)
        if (transaction != None):
            new_transactions.append(transaction)  
        
        print("EightImmortalsStrategy: completed sell operation, totally new transactions: " + str(len(new_transactions)))
        return new_transactions
        
        
    
    # 选出当前势头最好的三个币
    # 八仙过海： 近10个交易日中，选择出涨幅最大的币
    def pick_top_coins(self):
    
        coin_id_list = self.config.coin_id_list()
        
        # 如果币种不足，直接返回所有币种
        if (len(coin_id_list) <= 3):
            return coin_id_list
        
        coin_data = {}
        
        print("EightImmortalsStrategy: Finding top 3 coins with highest increase within last 10 days. coin list: " + str(coin_id_list))
        
        for coin_id in coin_id_list:
            coin_price = get_one(coin_id,"D","close")
            coin_data[coin_id] = coin_price[-1] - coin_price[-10]
        
        # 将所有候选币按照涨幅排序，选择出最后的三个
        sorted_data = sorted(coin_data.items(), key = operator.itemgetter(1))
        
        return [sorted_data[-1][0], sorted_data[-2][0], sorted_data[-3][0]]
        
    

class EightImmortalsClassicStrategy(EightImmortalsStrategy):
    def __init__(self):
        EightImmortalsStrategy.__init__(self, "EightImmortals_Classic", StrategyConfig.generate_config(["BTC", "ETH", "EOS", "BCH", "BNB", "XMR", "XRP", "LTC"], 2880))

        
class EightImmortalsNineStrategy(EightImmortalsStrategy):
    def __init__(self):
        EightImmortalsStrategy.__init__(self, "EightImmortals_Nine", StrategyConfig.generate_config(["BTC", "ETH", "EOS", "BCH", "BNB", "XMR", "XRP", "LTC", "TRX"], 2880))
