from common_function import *
from common_struct import *
from strategy import *
from strategy_manager import *
from wheeling_strategy import *
from account import *


#Register new account
manager = AccountManager()
result, message = manager.register_new_account("toneysui8", "Toney", 500000, "Wheeling_BtcUsdt")
if (result == 0):
    acct = manager.get_account_data("toneysui8")
    new_transactions, new_balance = acct.make_decision()
else:
    print(message)

    
# Get account and do daily/hourly decision
acct = manager.get_account_data("toneysui8")
new_transactions, new_balance = acct.make_decision()

if (new_transactions == None or len(new_transactions) == 0):
    print("Just Stand by and do nothing.")
else:
    print("Do following transactions:")
    for tran in new_transactions:
        print("time:" + tran.timestamp.strftime("%m/%d/%Y,%H:%M:%S") + " type:" + ("Buying" if tran.transaction_type == 1 else "Selling") + " coin:" + tran.coin_id + " amount:" + str(tran.coin_amount) + " total value:" + str(tran.cash_value))


# Get transaction history for an account
transactions = acct.get_transactions_history(1000)


# Just call one line to let all accounts do daily/hourly decision
manager.execute_make_decision()


# Get all registered account ids
all_accounts = manager.get_all_accounts()
for acc in all_accounts:
    print("Account Id:" + acc)

    
