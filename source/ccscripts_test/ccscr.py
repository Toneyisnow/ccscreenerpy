import sys, logging
import requests
import traceback
from multiprocessing import Process

import asyncio, time
from datetime import datetime

sys.path.append('ccscripts')

from account import AccountManager
from prediction_manager import PredictionManager

    
url = 'http://host.prod.quant1:5555/sync_portfolio'


def timer_job_run():

    logging.basicConfig(stream = sys.stderr, level = logging.INFO)

    trigger_all_strategies()
    trigger_all_predictions()



#
# 策略名称列表：
#   
#   Wheeling_BtcEth
#   Wheeling_BtcUsdt
#   Wheeling_BtcEthUsdtLtcXrpZec

#   EightImmortals_Classic
#   EightImmortals_Nine

#   Gridding_Btc
#   Gridding_BtcEth
#   Gridding_BtcEthLtcXrpZec
def trigger_all_strategies():

    manager = AccountManager()
    #user_eight_classic
    #user_eight_nine
    #user_wheeling_btceth
    #user_wheeling_btcusdt
    #user_wheeling_btcusdtltcxrpzec
    #user_gridding_btc
    #user_gridding_btceth
    #user_gridding_btcethltcxrpzec

    stras = {}
    stras["user_eight_classic"] = 532
    stras["user_eight_nine"] = 533
    stras["user_wheeling_btceth"] = 534
    stras["user_wheeling_btcusdt"] = 535
    stras["user_wheeling_btcusdtltcxrpzec"] = 536
    stras["user_gridding_btc"] = 537
    stras["user_gridding_btceth"] = 538
    stras["user_gridding_btcethltcxrpzec"] = 539
    #manager.register_new_account(account_id, "ccscreener_stras", 500000, "EightImmortals_Classic")

    for k in stras:
        stra_id = stras[k]
        print("## ", stra_id)
        account = manager.get_account_data(k)
        _, portfolio, portfolio_percentage = account.make_decision()
        print("## ", portfolio_percentage)
        tmp=portfolio_percentage
        for k in tmp:
            tmp[k] = tmp[k] * 100
        if (portfolio != None):
            args = {}
            args["id"] = stra_id
            args["detail"] = tmp
            try:
                requests.post(url, json = args)
            except:
                traceback.print_exc()

            
# Trigger the LSTM Strategies to predict
def trigger_all_predictions():

    manager = PredictionManager()
    manager.trigger_predictions()


timer_job_run()
