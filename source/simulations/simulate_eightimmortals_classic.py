import sys
import talib
import operator
sys.path.append('ccscripts')

from ccdata import *

from common_struct import *
from indices_provider import *



MAX_HOLDING_COIN = 3

# 准备数据信息
# Time: from 3/1/2017 to 3/1/2018
start_day_index = -779
end_day_index = -413

# Time: from 3/1/2018 to 3/1/2019
start_day_index = -412
end_day_index = -57

indices_provider = IndicesProvider()
cci30_data = indices_provider.get_cci30_indices(datetime.datetime.utcnow())
if (cci30_data == None):
    print("Error while retrieving cci30 data.")

ma40 = talib.MA(cci30_data["close"], timeperiod=40, matype=0)

coin_id_list = ["BTC", "ETH", "EOS", "BCH", "BNB", "XMR", "XRP", "LTC"]
coin_prices = {}

coin_price = get_one("USDT","D","close")
coin_prices["USDT"] = coin_price
    
for coin_id in coin_id_list:
    coin_price = get_one(coin_id,"D","close")
    coin_prices[coin_id] = coin_price



#ma40 = ma40[startDayIndex:endDayIndex]
#cci30_data["open"] = cci30_data["open"][startDayIndex:endDayIndex]
#cci30_data["high"] = cci30_data["high"][startDayIndex:endDayIndex]
#cci30_data["low"] = cci30_data["low"][startDayIndex:endDayIndex]
#cci30_data["close"] = cci30_data["close"][startDayIndex:endDayIndex]



# 生成一个买币交易，使用币的当前价格
def compose_buy_transaction(balance, day_index, coin_id, cash_value):

    if (cash_value <= 0):
        #print("TransactionProvider: cash value is 0, skip it.")
        return None
    
    nowtime = datetime.datetime.now() + datetime.timedelta(days = day_index)
    buy_amount = cash_value / coin_prices[coin_id][day_index]
    
    balance.add_coin_position(coin_id, buy_amount)
    balance.cash_balance -= cash_value
    if (balance.cash_balance < 0):
        balance.cash_balance = 0
    
    transaction = AccountTransaction(nowtime, AccountTransaction.Buying, coin_id, buy_amount, cash_value)
    print("Day {}: transaction: {}".format(day_index, transaction.to_string()))
    return transaction


# 生成一个卖币交易，使用币的当前价格
def compose_sell_transaction(balance, day_index, coin_id, amount):

    if (amount <= 0):
        #print("TransactionProvider: cash value is 0, skip it.")
        return None

    nowtime = datetime.datetime.now() + datetime.timedelta(days = day_index)
    
    total_price = coin_prices[coin_id][day_index] * amount
    balance.cash_balance += total_price
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


# 选出当前势头最好的三个币
# 八仙过海： 近10个交易日中，选择出涨幅最大的币
def pick_top_coins(day_index):
    
    #print("Finding top 3 coins with highest increase within last 10 days. coin list: " + str(coin_id_list))
    
    coin_fluctuation = {}
    for coin_id in coin_id_list:
        if (day_index - 9 <= - len(coin_prices[coin_id])):
            continue
        coin_fluctuation[coin_id] = coin_prices[coin_id][day_index] - coin_prices[coin_id][day_index - 9]
    
    # 将所有候选币按照涨幅排序，选择出最后的三个
    sorted_data = sorted(coin_fluctuation.items(), key = operator.itemgetter(1))
    return [sorted_data[-1][0], sorted_data[-2][0], sorted_data[-3][0]]
    
    

# 用USDT买入币种
# Returns: <transaction list>
def execute_buy(balance, day_index):
    
    #print("Begin execute buy.")
    
    if (balance.cash_balance <= 0 and balance.get_coin_position("USDT") <= 0):
        # No Cash or USDT, just leave it
        #print("No cash or USDT, just leave it.")
        return None


    # 选出当前势头最好的三个币
    top_coins = pick_top_coins(day_index)
    #print("Got top coins: " + str(top_coins))
    
    
    # 和当前持有的币合并，最大的持有币种不超过MAX_HOLDING_COIN
    existing_coins = balance.get_coin_ids()
    #print("Current holding coins: " + str(existing_coins))
    
    set_old = set(top_coins) & set(existing_coins)
    set_new = top_coins[:MAX_HOLDING_COIN - len(existing_coins)] if MAX_HOLDING_COIN > len(existing_coins) else []
    candidate_coins = list(set_old) + set_new
    #print("Buy candidate coins: " + str(candidate_coins))
    
    
    if (len(candidate_coins) == 0):
        # 没有空间买入新的币了，取消操作
        #print("No space for new coins, cancel this operation")
        return None

    new_transactions = []
    
    # 卖出USDT
    #print("EightImmortalsStrategy: sell all USDT.")
    transaction = compose_sell_all_transaction(balance, day_index,"USDT")
    if (transaction != None):
        new_transactions.append(transaction)
    
    # 平均买入新选定的币
    #print("EightImmortalsStrategy: evenly buy candidate coins.")
    even_cash_value = balance.cash_balance / len(candidate_coins)
    for candidate_coin in candidate_coins:
        
        transaction = compose_buy_transaction(balance, day_index, candidate_coin, even_cash_value)
        if (transaction != None):
            new_transactions.append(transaction)
    
    #print("completed buy operation, totally new transactions: " + str(len(new_transactions)))
    return new_transactions
        

# 卖出当前持有的所有币，换取USDT
#Returns: <transaction list>
def execute_sell(balance, day_index):

    #print("Begin execute sell.")
    
    new_transactions = []
    
    holding_coin_ids = list(balance.get_coin_ids()).copy()
    for coin_id in holding_coin_ids:
        
        if (coin_id == "USDT" or balance.get_coin_position(coin_id) <= 0):
            continue
        
        #print("selling coin " + coin_id + ".")
    
        # Sell the Coin
        transaction = compose_sell_all_transaction(balance, day_index, coin_id)
        if (transaction != None):
            new_transactions.append(transaction)
        
    # 买入USDT
    #print("Buy USDT with all cashes.")
    transaction =compose_buy_transaction(balance, day_index, "USDT", balance.cash_balance)
    if (transaction != None):
        new_transactions.append(transaction)
    
    #print("Completed sell operation, totally new transactions: " + str(len(new_transactions)))
    return new_transactions
    
    

balance = AccountBalance(500000)
for day_index in range(start_day_index, end_day_index):
    # 买入信号：
    # 1. T-2和T-1交易日中的综合指数均大于MA40
    # 2. T日的综合指数不被T-2日包含
    if (cci30_data["close"][day_index - 2] > ma40[day_index - 2] and cci30_data["close"][day_index - 1] > ma40[day_index - 1] and
        (cci30_data["high"][day_index] > cci30_data["high"][day_index - 2] or cci30_data["low"][day_index] < cci30_data["low"][day_index - 2])):
        execute_buy(balance, day_index)
        
    # 卖出信号：
    # 1. T-2和T-1交易日中的综合指数均小于MA40
    # 2. T日的综合指数不被T-2日包含
    elif (cci30_data["close"][day_index - 2] < ma40[day_index - 2] and cci30_data["close"][day_index - 1] < ma40[day_index - 1] and
        (cci30_data["high"][day_index] > cci30_data["high"][day_index - 2] or cci30_data["low"][day_index] < cci30_data["low"][day_index - 2])):
        execute_sell(balance, day_index)
        

total_value = balance.get_cash_balance()
for coin_id in balance.get_coin_ids():
    total_value += balance.get_coin_position(coin_id) * coin_prices[coin_id][end_day_index]


print("Total Value: {}. Balance: cash={}. positions={}".format(total_value, balance.get_cash_balance(), balance.serialize_positions()))
 