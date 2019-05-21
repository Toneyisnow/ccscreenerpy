# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import pandas as pd

import talib

from strategy import *
from market_provider import *
from indices_provider import *


'''
本策略通过计算ATR唐奇安通道和MA线, 并:
上穿唐奇安通道且短MA在长MA上方则开多仓,下穿唐奇安通道且短MA在长MA下方则开空仓
若有 多/空 仓位则分别:
价格 跌/涨 破唐奇安平仓通道 上/下 轨则全平仓位,否则
根据 跌/涨 破持仓均价 -/+ x(x=0.5,1,1.5,2)倍ATR把仓位
'''

class TurtleStrategy(QuantifyStrategy):
    
    def __init__(self, strategyId, strategy_config):
        QuantifyStrategy.__init__(self, strategyId, strategy_config)
        self.data_path = 'ccdatastore/Strategy/TurtleStrategy/'
    

    # Portfolio is the current positions/cash balance for one account
    # AccountInfo contains some information for that account needed for the strategy to consider, e.g. LastTransactionTime
    # Returns: <transaction list>
    def execute_decision(self, portfolio, account_info):
    
        if (self._is_too_soon_from_last_transaction(account_info)):
            print("TurtleStrategy: too soon from last transaction, ignore it.")
            return None

        DON_OPEN = self.get_DON_OPEN()
        DON_CLOSE = self.get_DON_CLOSE()
        MA_SHORT = self.get_MA_SHORT()
        MA_LONG  = self.get_MA_LONG()
        TAR = self.get_TAR()
        RATIO = self.get_RATIO()

        new_transactions = []
        coin_count = len(self._config.coin_id_list())
        for coin_id in self._config.coin_id_list():

            print('TurtleStrategy: calculating value for coin {}.'.format(coin_id))
                    
            close_prices = MarketProvider.get_last_n_price(coin_id, 101, "close")
            high_prices = MarketProvider.get_last_n_price(coin_id, 101, "high")
            low_prices = MarketProvider.get_last_n_price(coin_id, 101, "low")

            current_price = MarketProvider.get_current_price(coin_id)
            
            # 计算ATR
            atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod = TAR)[-1]
            
            # 计算唐奇安开仓和平仓通道
            upper_band = talib.MAX(close_prices[:-1], timeperiod = DON_OPEN)[-1]
            lower_band = talib.MIN(close_prices[:-1], timeperiod = DON_CLOSE)[-1]
            
            # 计算开仓的资金比例
            percent = RATIO / float(coin_count)
            
            # 若没有仓位则开仓
            position = portfolio.get_coin_position(coin_id)
            
            if not position:

                print('TurtleStrategy: no position currently.')
                
                # 计算长短ma线.DIF
                ma_short = talib.MA(close_prices, timeperiod=(MA_SHORT + 1))[-1]
                ma_long = talib.MA(close_prices, timeperiod=(MA_LONG + 1))[-1]
                dif = ma_short - ma_long

                # 获取当前价格
                # 上穿唐奇安通道且短ma在长ma上方则开仓
                if (current_price > upper_band and dif > 0):
                    print('TurtleStrategy: Create position for coin {} with percentage {}.'.format(coin_id, percent))
                    transaction = MarketProvider.order_target_percent(portfolio, coin_id, percent)
                    if transaction:
                        new_transactions.append(transaction)
                    
            # 价格跌破唐奇安平仓通道全平仓位止损
            elif current_price < lower_band:
                print('TurtleStrategy: Sell all for coin {}.'.format(coin_id))
                transaction = MarketProvider.compose_sell_all_transaction(portfolio, coin_id)
                if transaction:
                    new_transactions.append(transaction)

            # 根据涨跌幅调整持仓比例
            else:

                print('TurtleStrategy: adjust position.')
                average_price = np.mean(close_prices[-DON_OPEN:-1])
                    
                # 获取持仓的资金
                current_value = MarketProvider.calculate_portfolio_coin_value(portfolio, coin_id)
                portfolio_value = MarketProvider.calculate_portfolio_total_value(portfolio)
                
                # 获取平仓的区间
                band = average_price - np.array([200, 2, 1.5, 1, 0.5, -100]) * atr
                grid_percent = float(pd.cut([current_price], band, labels=[0, 0.25, 0.5, 0.75, 1])[0]) * percent

                # 选择现有百分比和区间百分比中较小的值(避免开仓)
                target_percent = np.minimum(current_value / portfolio_value, grid_percent)
                if target_percent != 1.0:
                    print('TurtleStrategy: Adjust the coin position to target percent: {}'.format(target_percent))
                    transaction = MarketProvider.order_target_percent(portfolio, coin_id, target_percent)
                    if transaction:
                        new_transactions.append(transaction)
            
        return new_transactions

    
    @staticmethod
    def default_config(coin_id_list, interval_in_minutes):
        
        config = StrategyConfig.generate_config(coin_id_list, interval_in_minutes)
        config.set_property("DON_OPEN", 20)
        config.set_property("DON_CLOSE", 10)
        config.set_property("MA_SHORT", 10)
        config.set_property("MA_LONG", 60)
        config.set_property("TAR", 20)
        config.set_property("RATIO", 0.9)

        return config
        

    @staticmethod
    def specific_config(coin_id_list, interval_in_minutes, don_open, don_close, ma_short, ma_long, tar, ratio):
        
        config = StrategyConfig.generate_config(coin_id_list, interval_in_minutes)
        config.set_property("DON_OPEN", don_open)
        config.set_property("DON_CLOSE", don_close)
        config.set_property("MA_SHORT", ma_short)
        config.set_property("MA_LONG", ma_long)
        config.set_property("TAR", tar)
        config.set_property("RATIO", ratio)

        return config
        
    def get_DON_OPEN(self):
        return self._config.get_property("DON_OPEN")

    def get_DON_CLOSE(self):
        return self._config.get_property("DON_CLOSE")

    def get_MA_SHORT(self):
        return self._config.get_property("MA_SHORT")

    def get_MA_LONG(self):
        return self._config.get_property("MA_LONG")

    def get_TAR(self):
        return self._config.get_property("TAR")

    def get_RATIO(self):
        return self._config.get_property("RATIO")



class TurtleBtcStrategy(TurtleStrategy):
    def __init__(self):
        TurtleStrategy.__init__(self, "Turtle_Btc", TurtleStrategy.default_config(["BTC"], 1440))


class TurtleEthStrategy(TurtleStrategy):
    def __init__(self):
        TurtleStrategy.__init__(self, "Turtle_Eth", TurtleStrategy.default_config(["ETH"], 1440))


class TurtleBtcEthStrategy(TurtleStrategy):
    def __init__(self):
        TurtleStrategy.__init__(self, "Turtle_BtcEth", TurtleStrategy.default_config(["BTC", "ETH"], 1440))


class TurtleBtcEthLtcXrpZecStrategy(TurtleStrategy):
    def __init__(self):
        TurtleStrategy.__init__(self, "Turtle_BtcEthLtcXrpZec", TurtleStrategy.default_config(["Btc", "Eth", "Ltc", "Xrp", "Zec"], 1440))

