import datetime
import json

class Portfolio:

    COIN_ID = "coin_id"
    AMOUNT = "amount"
    
    def __init__(self, cash_balance, coin_positions = {}):
        self.__cash_balance = cash_balance
        
        if (len(coin_positions.keys()) == 0):
            self.__coin_positions = {}
        else:
            self.__coin_positions = coin_positions
        
        
    def get_cash_balance(self):
        return self.__cash_balance
    
    
    def add_coin_position(self, new_coin_id, amount):
    
        if (new_coin_id in self.__coin_positions):
            self.__coin_positions[new_coin_id] += amount
    
        else:
            self.__coin_positions[new_coin_id] = amount
    
    
    def remove_coin_position(self, coin_id, amount):
    
        if (coin_id in self.__coin_positions):
            
            if (self.__coin_positions[coin_id] > amount):
                self.__coin_positions[coin_id] -= amount
            elif (self.__coin_positions[coin_id] == amount):
                self.clean_coin_position(coin_id)
            else:
                return
        else:
            return
            

    def change_cash_balance(self, delta):
        self.__cash_balance += delta
        if (self.__cash_balance < 0):
            self.__cash_balance = 0
    

    def clean_coin_position(self, coin_id):
        self.__coin_positions.pop(coin_id, None)
    
    
    def get_coin_position(self, coin_id):
    
        if (coin_id in self.__coin_positions):
            return self.__coin_positions[coin_id]
        else:
            return 0
            
        
    def get_coin_ids(self):
        return self.__coin_positions.keys()
    
    
    def get_coin_positions(self):
        return self.__coin_positions
    

    def get_coin_positions_percentage(self):
        # Calculate the value percentage per coin, in order to return to CCSCREENER

        return self.__coin_positions
    

    def serialize_positions(self):
        return json.dumps(self.__coin_positions)
    
    
    @staticmethod
    def deserialize_positions(str_value):
        return json.loads(str_value)

        
        
class AccountInfo:

    def __init__(self):
        pass
        
    @staticmethod
    def generate_info(last_transaction_time):
    
        info = AccountInfo()
        info.last_transaction_time = last_transaction_time
        return info

    
class AccountTransaction:

    Buying = 1
    Selling = 2
    
    def __init__(self, timestamp, transaction_type, coin_id, coin_amount, cash_value):
    
        self.timestamp = timestamp
        self.transaction_type = transaction_type
        self.coin_id = coin_id
        self.coin_amount = coin_amount
        self.cash_value = cash_value
    
    
    @staticmethod
    def parse_from_row(row):
    
        timestamp = datetime.datetime.strptime(row[0], "%Y_%m_%d_%H:%M:%S")
        transaction_type = row[1]
        coin_id = row[2]
        coin_amount = row[3]
        cash_value = row[4]
        return AccountTransaction(timestamp, transaction_type, coin_id, coin_amount, cash_value)
    
    
    def write_to_csv(self, csvwriter):
        csvwriter.writerow([self.timestamp.strftime("%Y_%m_%d_%H:%M:%S"), str(self.transaction_type), self.coin_id, str(self.coin_amount), str(self.cash_value)])
    
    
    def to_string(self):
        return "{}: Time=[{}],CoinId=[{}],Amount=[{}],Price=[{}],TotalValue=[{}]".format("Buying" if (self.transaction_type == AccountTransaction.Buying) else "Selling", self.timestamp.strftime("%Y_%m_%d_%H:%M:%S"), self.coin_id, str(self.coin_amount), str(self.cash_value/self.coin_amount), str(self.cash_value))
    
    
    @staticmethod
    def header_row():
        return ['TimeStamp', 'Type', 'CoinId', 'Amount', "CashValue"]
        
        