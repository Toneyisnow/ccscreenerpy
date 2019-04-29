import datetime

class QuantifyStrategy:
    
    def __init__(self, strategy_id, strategy_config):
        self._strategy_id = strategy_id
        self._config = strategy_config
        self._data_path = 'ccdatastore/Strategy/'
        
    def _is_too_soon_from_last_transaction(self, account_info):
        return datetime.datetime.now() < account_info.last_transaction_time + self._config.minimum_transaction_interval()
        
    
    def _get_data_file_name(self, timestamp):
        return self._data_path + timestamp.strftime("%Y_%m_%d_%H_") + self._strategy_id + '.csv'

    
    # 返回： <TransactionList>
    def execute_decision(self, portfolio, account_info):
        return None
        
        
class StrategyConfig:

    MINIMUM_TRANSACTION_INTERVAL = "MINIMUM_TRANSACTION_INTERVAL"
    COIN_ID_LIST = "COIN_ID_LIST"
    
    def __init__(self):
        self.__dict = {}
        
    @staticmethod
    def generate_config(coin_id_list, interval_in_minutes):
        
        config = StrategyConfig()
        
        config.__dict[StrategyConfig.COIN_ID_LIST] = coin_id_list
        config.__dict[StrategyConfig.MINIMUM_TRANSACTION_INTERVAL] = datetime.timedelta(minutes = interval_in_minutes)
        
        return config
        
    def minimum_transaction_interval(self):
        return (self.__dict[StrategyConfig.MINIMUM_TRANSACTION_INTERVAL] if self.__dict != None else None)
        
        
    def coin_id_list(self):
        return (self.__dict[StrategyConfig.COIN_ID_LIST] if self.__dict != None else None)
    