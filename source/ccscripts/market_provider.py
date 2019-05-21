import datetime
import json
import ccdata

from common_struct import *


#
# 与币价相关的所有操作，例如：查询价格历史数据，计算当前币值，生成买卖交易
#

class MarketProvider:

    # 获取指定币的当前价格
    @staticmethod
    def get_current_price(coin_id):
        coin_prices = ccdata.get_one(coin_id, "D", "close")
        if (coin_prices.any() == None or len(coin_prices) == 0):
            return None

        return coin_prices[-1]


    # 获取指定币的最后N天的价格（包含今天）. dtype: open/close/high/low
    @staticmethod
    def get_last_n_price(coin_id, n, dtype = "close"):
        coin_prices = ccdata.get_one(coin_id, "D", dtype)
        if (coin_prices.any() == None or len(coin_prices) < n):
            return None

        return coin_prices[-n:]


    # 生成一个买币交易，使用币的当前价格
    @staticmethod
    def compose_buy_transaction(portfolio, coin_id, cash_value):
    
        if (cash_value <= 0):
            print("MarketProvider: cash value is 0, skip it.")
            return None
    
        coin_price = MarketProvider.get_current_price(coin_id)
        if (coin_price == None or coin_price <= 0):
            print("MarketProvider: coin price invalid for [{}], skip it.".format(coin_id))
            return None
    
        nowtime = datetime.datetime.now()
        buy_amount = cash_value / coin_price
        
        portfolio.add_coin_position(coin_id, buy_amount)
        portfolio.change_cash_balance(-cash_value)
        
        transaction = AccountTransaction(nowtime, AccountTransaction.Buying, coin_id, buy_amount, cash_value)
        print("MarketProvider: composed transaction: " + transaction.to_string())
        return transaction
    
    
    # 生成一个卖币交易，使用币的当前价格
    @staticmethod
    def compose_sell_transaction(portfolio, coin_id, amount):
    
        if (amount <= 0):
            print("MarketProvider: cash value is 0, skip it.")
            return None
    
        nowtime = datetime.datetime.now()
        
        coin_price = MarketProvider.get_current_price(coin_id)
        if (coin_price == None or coin_price <= 0):
            print("MarketProvider: coin price invalid for [{}], skip it.".format(coin_id))
            return None
        
        total_price = coin_price * amount
        portfolio.change_cash_balance(total_price)
        portfolio.remove_coin_position(coin_id, amount)
    
        transaction = AccountTransaction(nowtime, AccountTransaction.Selling, coin_id, amount, total_price)
        print("MarketProvider: composed transaction: " + transaction.to_string())
        return transaction
        
    
    # 生成一个卖币交易，使用币的当前价格，卖出当前持有的所有该币种
    @staticmethod
    def compose_sell_all_transaction(balance, coin_id):
    
        amount = balance.get_coin_position(coin_id)
        if (amount <= 0):
            return None
        
        return MarketProvider.compose_sell_transaction(balance, coin_id, amount)

    
    # 买入或卖出指定币种，使得该币的持有价值为portfolio总价值的percentage。如果持有现金不够，则用所有现金买入
    @staticmethod
    def order_target_percent(portfolio, coin_id, percentage):
        
        total_value = MarketProvider.calculate_portfolio_total_value(portfolio)
        coin_value = MarketProvider.calculate_portfolio_coin_value(portfolio, coin_id)
        target_value = total_value * percentage
        price = MarketProvider.get_current_price(coin_id)
        if not price:
            print("MarketProvider: error retrieving price for coin {}.".format(coin_id))
            return None

        if (target_value < coin_value):
            #卖出
            amount = (coin_value - target_value) / price
            return MarketProvider.compose_sell_transaction(portfolio, coin_id, amount)
        elif (target_value > coin_value):
            #买入
            buy_value = min(portfolio.get_cash_balance(), target_value - coin_value)
            return MarketProvider.compose_buy_transaction(portfolio, coin_id, buy_value)   


    # 计算当前持仓的市值比例，返回值示例：{'BTC':0.3, 'ETH':0.1}
    @staticmethod
    def calculate_portfolio_percentage(portfolio):

        total_price = portfolio.get_cash_balance()
        percentage = {}
        for coin_id in portfolio.get_coin_ids():
            coin_price = MarketProvider.get_current_price(coin_id)
            if (coin_price == None or coin_price <= 0):
                # 如果出现查询失败，暂且跳过
                continue

            percentage[coin_id] = portfolio.get_coin_position(coin_id) * coin_price
            total_price += percentage[coin_id]
            
        for coin_id in percentage.keys():
            percentage[coin_id] /= total_price

        return percentage


    # 计算当前持仓的总市值
    @staticmethod
    def calculate_portfolio_total_value(portfolio):
        
        total_value = portfolio.get_cash_balance()
        for coin_id in portfolio.get_coin_ids():
            total_value += MarketProvider.calculate_portfolio_coin_value(portfolio, coin_id)
        return total_value


    # 计算当前持仓的某币种的市值
    @staticmethod
    def calculate_portfolio_coin_value(portfolio, coin_id):

        position = portfolio.get_coin_position(coin_id)
        if not position:
            return 0

        price = MarketProvider.get_current_price(coin_id)
        return position * price



