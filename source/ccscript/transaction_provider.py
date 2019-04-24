import datetime
import json
import ccdata

from common_struct import *


class TransactionProvider:

    # 生成一个买币交易，使用币的当前价格
    def compose_buy_transaction(balance, coin_id, cash_value):
    
        if (cash_value <= 0):
            print("TransactionProvider: cash value is 0, skip it.")
            return None
    
        coin_prices = ccdata.get_one(coin_id, "D", "close")
        
        nowtime = datetime.datetime.now()
        buy_amount = cash_value / coin_prices[-1]
        
        balance.add_coin_position(coin_id, buy_amount)
        balance.cash_balance -= cash_value
        if (balance.cash_balance < 0):
            balance.cash_balance = 0
        
        transaction = AccountTransaction(nowtime, AccountTransaction.Buying, coin_id, buy_amount, cash_value)
        print("TransactionProvider: composed transaction: " + transaction.to_string())
        return transaction
    
    
    # 生成一个卖币交易，使用币的当前价格
    def compose_sell_transaction(balance, coin_id, amount):
    
        if (amount <= 0):
            print("TransactionProvider: cash value is 0, skip it.")
            return None
    
        nowtime = datetime.datetime.now()
        
        coin_prices = ccdata.get_one(coin_id, "D", "close")
        total_price = coin_prices[-1] * amount
        balance.cash_balance += total_price
        balance.remove_coin_position(coin_id, amount)
    
        transaction = AccountTransaction(nowtime, AccountTransaction.Selling, coin_id, amount, total_price)
        print("TransactionProvider: composed transaction: " + transaction.to_string())
        return transaction
        
    
    # 生成一个卖币交易，使用币的当前价格，卖出当前持有的所有该币种
    def compose_sell_all_transaction(balance, coin_id):
    
        amount = balance.get_coin_position(coin_id)
        if (amount <= 0):
            return None
        
        return TransactionProvider.compose_sell_transaction(balance, coin_id, amount)

        
        
class AccountInfo:

    def __init__(self):
        pass
        
    def generate_info(last_transaction_time):
    
        info = AccountInfo()
        info.last_transaction_time = last_transaction_time
        return info

    
class AccountTransaction:

    Buying = 1
    Selling = 2
    
    def __init__(self, timestamp, transaction_type, coin_id, coin_amount, cash_value):
    
        self.timestamp = timestamp
        self.transaction_type = transaction_type
        self.coin_id = coin_id
        self.coin_amount = coin_amount
        self.cash_value = cash_value
    
    
    def parse_from_row(row):
    
        timestamp = datetime.datetime.strptime(row[0], "%Y_%m_%d_%H:%M:%S")
        transaction_type = row[1]
        coin_id = row[2]
        coin_amount = float(row[3])
        cash_value = row[4]
        return AccountTransaction(timestamp, transaction_type, coin_id, coin_amount, cash_value)
    
    
    def write_to_file(self, writer):
        writer.writerow([self.timestamp.strftime("%Y_%m_%d_%H:%M:%S"), str(self.transaction_type), self.coin_id, str(self.coin_amount), str(self.cash_value)])
    
    
    def header_row():
        return ['TimeStamp', 'Type', 'CoinId', 'Amount', "CashValue"]
        
        