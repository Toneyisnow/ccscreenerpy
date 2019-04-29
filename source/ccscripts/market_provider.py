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


    # 获取指定币的最后N天的价格（包含今天）
    @staticmethod
    def get_last_n_price(coin_id, n):
        coin_prices = ccdata.get_one(coin_id, "D", "close")
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

    
    # 计算当前持仓的市值比例
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


        