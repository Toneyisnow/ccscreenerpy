# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import pandas as pd

import talib
import sys
from ccdata import *

sys.path.append('ccscripts')
from strategy import *
from market_provider import *
from indices_provider import *


# 准备数据信息
# Time: from 3/1/2017 to 3/1/2018
start_day_index = -81
end_day_index = -1

coin_id_list = ["BTC", "ETH", "LTC", "XRP", "ZEC"]
close_prices_all = {}
high_prices_all = {}
low_prices_all = {}


coin_price = get_one("USDT","D","close")
close_prices_all["USDT"] = coin_price

coin_price = get_one("USDT","D","high")
high_prices_all["USDT"] = coin_price

coin_price = get_one("USDT","D","low")
low_prices_all["USDT"] = coin_price

for coin_id in coin_id_list:
    coin_price = get_one(coin_id,"D","close")
    close_prices_all[coin_id] = coin_price
    coin_price = get_one(coin_id,"D","high")
    high_prices_all[coin_id] = coin_price
    coin_price = get_one(coin_id,"D","low")
    low_prices_all[coin_id] = coin_price


# 生成一个买币交易，使用币的当前价格
def compose_buy_transaction(balance, day_index, coin_id, cash_value):

    if (cash_value <= 0):
        #print("TransactionProvider: cash value is 0, skip it.")
        return None
    
    nowtime = datetime.datetime.now() + datetime.timedelta(days = day_index)
    buy_amount = cash_value / close_prices_all[coin_id][day_index]
    
    balance.add_coin_position(coin_id, buy_amount)
    balance.change_cash_balance(-cash_value)
    
    transaction = AccountTransaction(nowtime, AccountTransaction.Buying, coin_id, buy_amount, cash_value)
    print("Day {}: transaction: {}".format(day_index, transaction.to_string()))
    return transaction


# 生成一个卖币交易，使用币的当前价格
def compose_sell_transaction(balance, day_index, coin_id, amount):

    if (amount <= 0):
        #print("TransactionProvider: cash value is 0, skip it.")
        return None

    nowtime = datetime.datetime.now() + datetime.timedelta(days = day_index)
    
    total_price = close_prices_all[coin_id][day_index] * amount
    balance.change_cash_balance(total_price)
    balance.remove_coin_position(coin_id, amount)

    transaction = AccountTransaction(nowtime, AccountTransaction.Selling, coin_id, amount, total_price)
    print("Day {}: transaction: {}".format(day_index, transaction.to_string()))
    return transaction
    

# 生成一个卖币交易，使用币的当前价格，卖出当前持有的所有该币种
def compose_sell_all_transaction(balance, day_index, coin_id):
    
        amount = balance.get_coin_position(coin_id)
        if (amount <= 0):
            return None
        
        return compose_sell_transaction(balance, day_index, coin_id, amount)


    
# 买入或卖出指定币种，使得该币的持有价值为portfolio总价值的percentage。如果持有现金不够，则用所有现金买入
def order_target_percent(portfolio, day_index, coin_id, percentage):
    
    total_value = calculate_portfolio_total_value(portfolio, day_index)
    coin_value = calculate_portfolio_coin_value(portfolio, day_index, coin_id)
    target_value = total_value * percentage
    price = close_prices_all[coin_id][day_index]
    if not price:
        print(" error retrieving price for coin {}.".format(coin_id))
        return None

    if (target_value < coin_value):
        #卖出
        amount = (coin_value - target_value) / price
        return compose_sell_transaction(portfolio, day_index, coin_id, amount)
    elif (target_value > coin_value):
        #买入
        buy_value = min(portfolio.get_cash_balance(), target_value - coin_value)
        return compose_buy_transaction(portfolio, day_index, coin_id, buy_value)   


# 计算当前持仓的市值比例，返回值示例：{'BTC':0.3, 'ETH':0.1}
def calculate_portfolio_percentage(portfolio, day_index):

        total_price = portfolio.get_cash_balance()
        percentage = {}
        for coin_id in portfolio.get_coin_ids():
            coin_price = close_prices_all[coin_id][day_index]
            if (coin_price == None or coin_price <= 0):
                # 如果出现查询失败，暂且跳过
                continue

            percentage[coin_id] = portfolio.get_coin_position(coin_id) * coin_price
            total_price += percentage[coin_id]
            
        for coin_id in percentage.keys():
            percentage[coin_id] /= total_price

        return percentage


# 计算当前持仓的总市值
def calculate_portfolio_total_value(portfolio, day_index):
    
    total_value = portfolio.get_cash_balance()
    for coin_id in portfolio.get_coin_ids():
        total_value += calculate_portfolio_coin_value(portfolio, day_index, coin_id)
    return total_value


# 计算当前持仓的某币种的市值
def calculate_portfolio_coin_value(portfolio, day_index, coin_id):

    position = portfolio.get_coin_position(coin_id)
    if not position:
        return 0

    price = close_prices_all[coin_id][day_index]
    return position * price

        
# Portfolio is the current positions/cash balance for one account
# AccountInfo contains some information for that account needed for the strategy to consider, e.g. LastTransactionTime
# Returns: <transaction list>
def execute_decision(portfolio, day_index):
    
    DON_OPEN = 20
    DON_CLOSE = 10
    MA_SHORT = 10
    MA_LONG  = 60
    TAR = 20
    RATIO = 0.9

    new_transactions = []
    coin_count = len(coin_id_list)
    for coin_id in coin_id_list:

        #print('TurtleStrategy: calculating value for coin {}.'.format(coin_id))
        
        try:
            close_prices = close_prices_all[coin_id][day_index - 100: day_index]
            high_prices = high_prices_all[coin_id][day_index - 100: day_index]
            low_prices = low_prices_all[coin_id][day_index - 100: day_index]
            current_price = close_prices_all[coin_id][day_index]
        except:
            continue
        
        try:
            # 计算ATR
            atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod = TAR)[-1]
            # 计算唐奇安开仓和平仓通道
            upper_band = talib.MAX(close_prices[:-1], timeperiod = DON_OPEN)[-1]
            lower_band = talib.MIN(close_prices[:-1], timeperiod = DON_CLOSE)[-1]
        except:
            continue
        
        
        # 计算开仓的资金比例
        percent = RATIO / float(coin_count)
        
        # 若没有仓位则开仓
        position = portfolio.get_coin_position(coin_id)
        
        if not position:

            #print('TurtleStrategy: no position currently.')
            
            # 计算长短ma线.DIF
            ma_short = talib.MA(close_prices, timeperiod=(MA_SHORT + 1))[-1]
            ma_long = talib.MA(close_prices, timeperiod=(MA_LONG + 1))[-1]
            dif = ma_short - ma_long

            # 获取当前价格
            # 上穿唐奇安通道且短ma在长ma上方则开仓
            if (current_price > upper_band and dif > 0):
                print('TurtleStrategy: Create position for coin {} with percentage {}.'.format(coin_id, percent))
                transaction = order_target_percent(portfolio, day_index, coin_id, percent)
                if transaction:
                    new_transactions.append(transaction)
                
        # 价格跌破唐奇安平仓通道全平仓位止损
        elif current_price < lower_band:
            print('TurtleStrategy: Sell all for coin {}.'.format(coin_id))
            transaction = compose_sell_all_transaction(portfolio, day_index, coin_id)
            if transaction:
                new_transactions.append(transaction)

        # 根据涨跌幅调整持仓比例
        else:

            print('TurtleStrategy: adjust position.')
            average_price = np.mean(close_prices[-DON_OPEN:-1])
                
            # 获取持仓的资金
            current_value = calculate_portfolio_coin_value(portfolio, day_index, coin_id)
            portfolio_value = calculate_portfolio_total_value(portfolio, day_index)
            
            # 获取平仓的区间
            band = average_price - np.array([200, 2, 1.5, 1, 0.5, -100]) * atr
            grid_percent = float(pd.cut([current_price], band, labels=[0, 0.25, 0.5, 0.75, 1])[0]) * percent

            # 选择现有百分比和区间百分比中较小的值(避免开仓)
            target_percent = np.minimum(current_value / portfolio_value, grid_percent)
            if target_percent != 1.0:
                print('TurtleStrategy: Adjust the coin position to target percent: {}'.format(target_percent))
                transaction = order_target_percent(portfolio, day_index, coin_id, target_percent)
                if transaction:
                    new_transactions.append(transaction)
        
    return new_transactions
    

portfolio = Portfolio(500000)
result_transactions = []
for day_index in range(start_day_index, end_day_index):

    trans = execute_decision(portfolio, day_index)
    if trans != None:
        result_transactions += trans
    
    
print('TimeStamp,Type,CoinId,Amount,CashValue')            
for transaction in result_transactions:
    print("{},{},{},{},{}".format(transaction.timestamp, transaction.transaction_type, transaction.coin_id, transaction.coin_amount, transaction.cash_value))

    
total_value = portfolio.get_cash_balance()
for coin_id in portfolio.get_coin_ids():
    total_value += portfolio.get_coin_position(coin_id) * close_prices_all[coin_id][end_day_index]


print("Total Value: {}. Balance: cash={}. positions={}".format(total_value, portfolio.get_cash_balance(), portfolio.serialize_positions()))

