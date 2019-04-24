import datetime

class QuantifyStrategy:
    
    def __init__(self, strategyId, strategy_config):
        self.strategyId = strategyId
        self.config = strategy_config
        self.data_path = 'ccdatastore/Strategy/'
        
    def is_too_soon_from_last_transaction(self, account_info):
        return datetime.datetime.now() < account_info.last_transaction_time + self.config.minimum_transaction_interval()
        
    
    def get_data_file_name(self, timestamp):
        return self.data_path + timestamp.strftime("%Y_%m_%d_%H_") + self.strategyId + '.csv'

    
    # 返回： <TransactionList>
    def execute_with_balance(self, balance, account_info):
        return None
        
        
class StrategyConfig:

    MINIMUM_TRANSACTION_INTERVAL = "MINIMUM_TRANSACTION_INTERVAL"
    COIN_ID_LIST = "COIN_ID_LIST"
    
    def __init__(self):
        self.dict = {}
        
    def generate_config(coin_id_list, interval_in_minutes):
        
        config = StrategyConfig()
        
        config.dict[StrategyConfig.COIN_ID_LIST] = coin_id_list
        config.dict[StrategyConfig.MINIMUM_TRANSACTION_INTERVAL] = datetime.timedelta(minutes = interval_in_minutes)
        
        return config
        
    def minimum_transaction_interval(self):
        return (self.dict[StrategyConfig.MINIMUM_TRANSACTION_INTERVAL] if self.dict != None else None)
        
        
    def coin_id_list(self):
        return (self.dict[StrategyConfig.COIN_ID_LIST] if self.dict != None else None)
    