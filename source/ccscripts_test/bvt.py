import sys

# 用于测试代码
sys.path.append('ccscripts_dev')

import uuid

from account import AccountManager
from lstm_train_function import *




class BVTTests:

    @staticmethod
    def register_account_test():
        print("Staring register_account_test.")
        account_id = BVTTests.__register_account("EightImmortals_Classic")
        BVTTests.__decommission_account(account_id)
        print("Passed.")


    @staticmethod
    def update_account_test():
        print("Staring update_account_test.")
        account_id = BVTTests.__register_account("EightImmortals_Classic")

        manager = AccountManager()
        account = manager.get_account_data(account_id)
        account.change_strategy("EightImmortals_Nine")
        account.save_to_file()

        BVTTests.__decommission_account(account_id)
        print("Passed.")


    @staticmethod
    def account_make_decision_test():
        print("Staring account_make_decision_test.")
        account_id = BVTTests.__register_account("EightImmortals_Classic")

        manager = AccountManager()
        account = manager.get_account_data(account_id)
        transactions, portfolio, portfolio_percentage = account.make_decision()
        if (transactions != None):
            print("New transactions count:{}. Portfolio:[{} Cash={}]. Percentage:{}".format(len(transactions), portfolio.get_coin_positions(), portfolio.get_cash_balance(), portfolio_percentage))
        else:
            print("Empty transactions. Portfolio:[{} Cash={}]. Percentage:{}".format(portfolio.get_coin_positions(), portfolio.get_cash_balance(), portfolio_percentage))

        BVTTests.__decommission_account(account_id)
        print("Passed.")


    @staticmethod
    def wheeling_strategy_test():
        print("Staring wheeling_strategy_test.")
        BVTTests.__strategy_test("Wheeling_BtcEth")
        print("Passed.")


    @staticmethod
    def eightimmortals_strategy_test():
        print("Staring eightimmortals_strategy_test.")
        BVTTests.__strategy_test("EightImmortals_Classic")
        print("Passed.")


    @staticmethod
    def gridding_strategy_test():
        print("Staring gridding_strategy_test.")
        BVTTests.__strategy_test("Gridding_BtcEthLtcXrpZec")
        print("Passed.")


    @staticmethod
    def turtle_strategy_test():
        print("Staring turtle_strategy_test.")
        BVTTests.__strategy_test("Turtle_BtcEthLtcXrpZec")
        print("Passed.")


    @staticmethod
    def lstm_test():
        print("Staring lstm_test.")
        lstm = LSTMStrategy()
        lstm.update_coin_list(['BTC', 'ETH', 'LTC'])

        # this method should be called at least every 1 hour
        lstm.analysis()
        print("Finished lstm analysis.")
        
        result, timestamp = lstm.read_result()
        print("Passed.")


    @staticmethod
    def __register_account(strategy_id):
        manager = AccountManager()
        randomid = str(uuid.uuid4())
        account_id = "test" + randomid[:6]
        manager.register_new_account(account_id, "ToneyTesting", 500000, strategy_id)
        return account_id


    @staticmethod
    def __decommission_account(account_id):
        pass


    @staticmethod
    def __strategy_test(strategy_id):
        account_id = BVTTests.__register_account(strategy_id)

        manager = AccountManager()
        account = manager.get_account_data(account_id)
        transactions, portfolio, portfolio_percentage = account.make_decision()
        if (transactions != None):
            print("New transactions count:{}. Portfolio:[{} Cash={}]. Percentage:{}".format(len(transactions), portfolio.get_coin_positions(), portfolio.get_cash_balance(), portfolio_percentage))
        else:
            print("Empty transactions. Portfolio:[{} Cash={}]. Percentage:{}".format(portfolio.get_coin_positions(), portfolio.get_cash_balance(), portfolio_percentage))

        BVTTests.__decommission_account(account_id)

