import os
import json
import csv

from common_struct import *
from common_function import *
from strategy_manager import *


class Account:
    
    data_file_name_template = "ACCT_{0}.dat"
    transaction_file_name_template = "ACCT_{0}_Tran.dat"
    
    def __init__(self, account_id, nickname = None, initial_cash = 0, strategy_id = None, data_folder_path = None):
        self.account_id = account_id
        self.nickname = nickname
        self.strategy_id = strategy_id
        self.balance = AccountBalance(initial_cash)
        self.data_folder_path = data_folder_path
        
    
    def save_to_file(self):
        with open(self.get_data_file_name(), mode='w+') as output_file:
            writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([self.nickname, self.strategy_id, str(self.balance.get_cash_balance()), self.balance.serialize_positions()])
    

    def load_from_file(data_folder_path, account_id):
        data_file = Account.get_data_file_name_s(data_folder_path, account_id)
        if (not does_file_exist(data_file)):
            return None
            
        with open(data_file, mode='r') as input_file:
            reader = csv.reader(input_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            row = next(reader)
            
            account = Account(account_id)
            account.nickname = row[0]
            account.strategy_id = row[1]
            account.data_folder_path = data_folder_path
            
            cash_balance = float(row[2])
            coin_positions = AccountBalance.deserialize_positions(row[3])
            if (type(coin_positions) is str):
                coin_positions = {}
            
            account.balance = AccountBalance(cash_balance, coin_positions)
            return account
            
            
    def get_data_file_name(self):
        return os.path.join(self.data_folder_path, Account.data_file_name_template.format(self.account_id))
    
    def get_data_file_name_s(data_folder_path, account_id):
        return os.path.join(data_folder_path, Account.data_file_name_template.format(account_id))
    
    def get_transaction_file_name(self):
        return os.path.join(self.data_folder_path, Account.transaction_file_name_template.format(self.account_id))
    
    def change_strategy(self, strategy_id):
        self.strategy_id = strategy_id
    
    def make_decision(self):
    
        print("Begin making decision.")
        
        strategy = StrategyManager.get_strategy(self.strategy_id)
        if (strategy == None):
            print("Error: cannot find strategy with Id " + self.strategy_id)
            # Something wrong with strategy id, or cannot get strategy
            return None, self.balance
            
        info = AccountInfo.generate_info(self.get_last_transaction_time())
    
        new_transactions = strategy.execute_with_balance(self.balance, info)
        if (new_transactions == None or len(new_transactions) == 0):
            print("Strategy returned empty transactions.")
            return None, self.balance
        
        print("Strategy returned " + str(len(new_transactions)) + " new transactions, saving them into transaction history and update balance.")
        # 保存交易记录，并更新BALANCE信息到文件
        self.write_transactions_history(new_transactions)
        self.save_to_file()
    
        print("Account saved successfully.")
        return new_transactions, self.balance
    
    
    def write_transactions_history(self, transactions):
        # Append Write to file
        transaction_file = self.get_transaction_file_name()
        if (does_file_exist(transaction_file)):
            with open(transaction_file, mode='a') as output_file:
                writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for transaction in transactions:
                    transaction.write_to_csv(writer)
        else:
            with open(transaction_file, mode='w+') as output_file:
                writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(AccountTransaction.header_row())
                for transaction in transactions:
                    transaction.write_to_csv(writer)
                
    
    def get_transactions_history(self, max_count = 1000):
    
        transaction_history = []
        if (not does_file_exist(self.get_transaction_file_name())):
            return None
        
        with open(self.get_transaction_file_name(), mode='r') as input_file:
            reader = csv.reader(input_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            next(reader)
         
            for row in reader:
                trans = AccountTransaction.parse_from_row(row)
                transaction_history.append(trans)
        
            return transaction_history
        
    
    
    def get_last_transaction_time(self):
    
        transactions = self.get_transactions_history(1)
        if (transactions == None or len(transactions) <= 0):
            return datetime.datetime.now() - datetime.timedelta(days=30)
            
        return transactions[0].timestamp
        
        
        
        
class AccountManager:

    data_file_folder_path = "ccdatastore/Accounts/"
    registered_account_file_name = "__registered_accounts.csv"
    
    def __init__(self):
        self.all_accounts = []
        
        
    def register_new_account(self, account_id, nickname, initial_cash, strategy_id):
    
        if (account_id.isspace() or nickname.isspace()):
            return -1, "AccountId or Nickname is invalid."
        
        account_id = account_id.strip()
        nickname = nickname.strip()
        
        registered_account_file = os.path.join(AccountManager.data_file_folder_path, AccountManager.registered_account_file_name)
        if (does_file_exist(registered_account_file)):
            with open(registered_account_file, mode='r') as read_file:
                reader = csv.reader(read_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                # Skip the header
                row = next(reader)
                
                for row in reader:
                    existing_account_id = row[1]
                    if (existing_account_id.lower() == account_id.lower()):
                        # Account already exists
                        return -1, "The Account already exists."
                
        else:
            # If the file not exists, create the file with headers
            with open(registered_account_file, mode='w+') as output_file:
                writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["created_timestamp", "account_id"])
        
        # Check Parameters
        strategy = StrategyManager.get_strategy(strategy_id)
        if (strategy == None):
            return -1, "StrategyId is invalid."
         
        # Create the account data file
        account = Account(account_id, nickname, initial_cash, strategy_id, AccountManager.data_file_folder_path)
        account.save_to_file()
        
        # Append the account id into the file
        with open(registered_account_file, mode='a') as output_file:
            writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([datetime.datetime.now(), account_id])
    
        return 0, "Create Account Succeeded."
        
        
    def get_all_accounts(self):
    
        registered_account_file = os.path.join(AccountManager.data_file_folder_path, AccountManager.registered_account_file_name)
        if (does_file_exist(registered_account_file)):
            all_accounts = []
            with open(registered_account_file, mode='r') as read_file:
                reader = csv.reader(read_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                # Skip the header
                row = next(reader)
                
                for row in reader:
                    existing_account_id = row[1]
                    all_accounts.append(existing_account_id)
                
            return all_accounts
        else:
            return None
        
        
    def execute_make_decision(self):
        all_accounts = manager.get_all_accounts()
        for acct_id in all_accounts:
            account = self.get_account_data(acct_id)
            account.make_decision()
        
        
    def get_account_data(self, account_id):
        return Account.load_from_file(AccountManager.data_file_folder_path, account_id)
        
        
    def change_strategy(self, account_id, strategy_id):
    
        account = self.get_account_data(account_id)
        if (account == None):
            return -1
            
        account.change_strategy(strategy_id)
        account.save_to_file()
        return 0
        
    
    def get_all_positions(self, account_id):
        account = self.get_account_data(account_id)
        return account.get_all_positions()
        
        
    def get_transactions_history(self, account_id):
        account = self.get_account_data(account_id)
        return account.get_transactions_history()
        
    