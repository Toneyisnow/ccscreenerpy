from bvt import *


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


BVTTests.register_account_test()

BVTTests.update_account_test()

BVTTests.account_make_decision_test()

BVTTests.wheeling_strategy_test()

BVTTests.eightimmortals_strategy_test()

BVTTests.gridding_strategy_test()
