import sys
sys.path.append('ccscripts')

from account import AccountManager


manager = AccountManager()
manager.register_new_account("toneysui", "Toney", 500000, "EightImmortals_Classic")

acct = manager.get_account_data("toneysui")
transactions, balance = acct.make_decision()


print(transactions)

