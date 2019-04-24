from wheeling_strategy_v2 import *
from eightimmortals_strategy import *


class StrategyManager:
    
    def __init__(self):
        pass
        
    def get_strategy(strategy_id):
    
        try:
            return {
                'Wheeling_BtcEth': BtcEthWheelingStrategy(),
                'Wheeling_BtcUsdt': BtcUsdtWheelingStrategy(),
                'Wheeling_BtcEthUsdtLtc': BtcEthUsdtLtcWheelingStrategy(),
                'Wheeling_BtcEthUsdtLtcXrpZec': BtcEthUsdtLtcXrpZecWheelingStrategy(),
            
                'EightImmortals_Classic': EightImmortalsClassicStrategy(),
                'EightImmortals_Nine': EightImmortalsNineStrategy()
                
            }[strategy_id]
        except:
            return None