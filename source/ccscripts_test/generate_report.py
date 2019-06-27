import sys
sys.path.append('ccscripts')
from common_function import *
from common_struct import *
from strategy import *
from strategy_manager import *
from market_provider import *
from wheeling_strategy import *
from account import *


manager = AccountManager()

account_list = [
    'user_eight_classic'
    ,'user_eight_nine'
    ,'user_gridding_btc'
    ,'user_gridding_btceth'
    ,'user_gridding_btcethltcxrpzec'
    ,'user_turtle_btc_201903'
    ,'user_turtle_eth_201903'
    ,'user_turtle_btceth_201903'
    ,'user_turtle_btcethltcxrpzec_201903'
    ,'user_wheeling_btceth'
    ,'user_wheeling_btcusdt'
    ,'user_wheeling_btcusdtltcxrpzec'
]

result_table = []

for acct_id in account_list:
    acct = manager.get_account_data(acct_id)
    portf = acct.portfolio
    details = "{} Cash:{}".format(portf.get_coin_positions(), portf.get_cash_balance())
    value = MarketProvider.calculate_portfolio_total_value(portf)
    result = [acct_id, details, value, (value - 500000) / 500000]
    result_table += result
    
print(result_table)