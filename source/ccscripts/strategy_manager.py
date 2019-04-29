from wheeling_strategy_v2 import *
from eightimmortals_strategy import *
from gridding_strategy import *

class StrategyManager:
    
    def __init__(self):
        pass
        
    @staticmethod
    def get_strategy(strategy_id):
    
        try:
            return {
                'Wheeling_BtcEth': WheelingBtcEthStrategy(),
                'Wheeling_BtcUsdt': WheelingBtcUsdtStrategy(),
                'Wheeling_BtcEthUsdtLtc': WheelingBtcEthUsdtLtcStrategy(),
                'Wheeling_BtcEthUsdtLtcXrpZec': WheelingBtcEthUsdtLtcXrpZecStrategy(),
            
                'EightImmortals_Classic': EightImmortalsClassicStrategy(),
                'EightImmortals_Nine': EightImmortalsNineStrategy(),

                'Gridding_Btc': GriddingBtcStrategy(),
                'Gridding_BtcEth': GriddingBtcEthStrategy(),
                'Gridding_BtcEthLtcXrpZec': GriddingBtcEthLtcXrpZecStrategy(),
                

            }[strategy_id]
        except:
            return None