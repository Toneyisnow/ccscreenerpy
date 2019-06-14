import csv
import logging, sys
import time, datetime, os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from sklearn.preprocessing import MinMaxScaler

import ccdata
from common_function import *

logging.basicConfig(stream = sys.stderr, level = logging.INFO)

class LSTMV2Prediction:

    _data_file_folder_path = "ccdatastore/Prediction/LSTMV2/"
    _prediction_result_file_template = "prediction_result_{}.dat"
    _indicator_file_template = "_ind_{}.running"

    def __init__(self):
        self._coin_list = ['BTC', 'ETH', 'XRP', 'BCH', 'EOS', 'LTC', 'BNB', 'BSV', 'XLM', 'ADA'
                         , 'TRX', 'XMR', 'DASH', 'MIOTA', 'ATOM', 'XTZ', 'ETC', 'NEO', 'XEM', 'MKR'
                         , 'ONT', 'ZEC', 'BTG', 'CRO', 'BAT', 'VET', 'DOGE', 'LINK', 'BTT', 'OMG'
                         , 'QTUM', 'HOT', 'DCR', 'WAVES', 'BCD', 'LSK', 'NANO', 'REP', 'AOA', 'RVN'
                         , 'ZRX', 'ICX', 'BTS', 'CGB', 'BCN', 'PAX', 'ZIL', 'HT', 'XVG', 'IOST'
                         ]
        self._default_data_size = 2000

    # This is used for testing purpose
    def update_coin_list(self, coin_list):
        self._coin_list = coin_list

    # Result will return 2 data: 
    # coin_delta_dict: A sorted dictionary of <coin, delta>, with -1 < delta < 1, from bad to good
    # timestamp: The timestamp of this data generated, e.g. '2019053002'
    def read_result(self):
        
        now_time = datetime.datetime.now()
        check_point_time = now_time

        result_found = False
        while check_point_time > now_time - datetime.timedelta(days = 1):

            check_point_time_string = check_point_time.strftime("%Y%m%d%H")
            prediction_result_file_name = LSTMV2Prediction._prediction_result_file_template.format(check_point_time_string)
            indicator_file_name = LSTMV2Prediction._indicator_file_template.format(check_point_time_string)

            prediction_result_file_full_name = os.path.join(LSTMV2Prediction._data_file_folder_path, prediction_result_file_name)
            indicator_file_full_name = os.path.join(LSTMV2Prediction._data_file_folder_path, indicator_file_name)
        
            if (does_file_exist(prediction_result_file_full_name) and not does_file_exist(indicator_file_full_name)):
                result_found = True
                break

            check_point_time = check_point_time - datetime.timedelta(hours = 1)

        if not result_found:
            logging.error("No prediction result found in the last 1 day.")
            return None

        coin_delta_dict = {}
        with open(prediction_result_file_full_name, mode='r') as input_file:
            reader = csv.reader(input_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                coin_id = row[0]
                delta = row[1]
                coin_delta_dict[coin_id] = delta

        sorted_delta_result = sorted(coin_delta_dict.items(), key = lambda kv:(kv[1], kv[0]))
        sorted_delta_result = sorted_delta_result[::-1]   

        return sorted_delta_result, check_point_time.strftime("%Y%m%d%H")

    def analysis(self):

        timestring = datetime.datetime.now().strftime("%Y%m%d%H")
        prediction_result_file_name = LSTMV2Prediction._prediction_result_file_template.format(timestring)
        indicator_file_name = LSTMV2Prediction._indicator_file_template.format(timestring)

        prediction_result_file_full_name = os.path.join(LSTMV2Prediction._data_file_folder_path, prediction_result_file_name)
        indicator_file_full_name = os.path.join(LSTMV2Prediction._data_file_folder_path, indicator_file_name)
        
        if (does_file_exist(indicator_file_full_name)):
            # There is already a process running, skip this run
            logging.info("Running indicator file detected, there is already a process running, skip this run.")
            return

        with open(indicator_file_full_name, mode='w') as write_file:
            write_file.write("0")

        # If there is already a prediction result, delete it
        if (does_file_exist(prediction_result_file_full_name)):
            try:
                os.remove(prediction_result_file_full_name)
            except:
                logging.error("Removing existing prediction file failed: ", sys.exc_info()[0])

        logging.info("Start LSTM V2 run.")

        for coin_id in self._coin_list:
            try:
                predicted_value, actual_value = self.make_prediction(coin_id, self._default_data_size)
                delta_value = actual_value - predicted_value
                with open(prediction_result_file_full_name, mode='a+') as write_file:
                    writer = csv.writer(write_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([coin_id, delta_value])
            except:
                # Ignore all of the exceptions during the coin run
                logging.error("Error: ", sys.exc_info()[0])
                
        logging.info("Finish LSTM V2 run. Clean up temp files.")
        if (does_file_exist(indicator_file_full_name)):
            try:
                os.remove(indicator_file_full_name)
            except:
                logging.error("Removing indicator file failed: ", sys.exc_info()[0])


    def make_prediction(self, coin_id, TOTAL_DATA_SIZE):

        logging.info("Start Prediction for coin {}...".format(coin_id))
        
        start_time = time.time()

        TRAINING_PERIOD_SIZE = 60
        TEST_DATA_SIZE = 24
        TRAIN_DATA_SIZE = TOTAL_DATA_SIZE - TEST_DATA_SIZE
    

        high_prices = ccdata.get_one("ETH", "1h", "high")
        low_prices = ccdata.get_one("ETH", "1h", "low")

        high_prices = high_prices[-TOTAL_DATA_SIZE:]
        low_prices = low_prices[-TOTAL_DATA_SIZE:]

        high_prices = np.array(high_prices).astype(float)
        low_prices = np.array(low_prices).astype(float)
        
        mid_prices = (high_prices + low_prices) / 2.0
        if len(mid_prices) <= TRAIN_DATA_SIZE:
            # If the data is not enough, just return empty values
            return 0, 0

        sc = MinMaxScaler(feature_range = (0, 1))
        mid_prices = sc.fit_transform(mid_prices.reshape(-1, 1))
        training_set = mid_prices[:TRAIN_DATA_SIZE]

        # Initialize the training data
        X_train = []
        y_train = []
        for i in range(TRAINING_PERIOD_SIZE, TRAIN_DATA_SIZE):
            X_train.append(training_set[i - TRAINING_PERIOD_SIZE : i, 0])
            y_train.append(training_set[i, 0])
        X_train, y_train = np.array(X_train), np.array(y_train)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        # Start the LSTM engine
        regressor = Sequential()

        regressor.add(LSTM(units = 50, return_sequences = True, input_shape = (X_train.shape[1], 1)))
        regressor.add(Dropout(0.2))

        regressor.add(LSTM(units = 50, return_sequences = True))
        regressor.add(Dropout(0.2))

        regressor.add(LSTM(units = 50, return_sequences = True))
        regressor.add(Dropout(0.2))

        regressor.add(LSTM(units = 50))
        regressor.add(Dropout(0.2))

        regressor.add(Dense(units = 1))
        regressor.compile(optimizer = 'adam', loss = 'mean_squared_error')
        regressor.fit(X_train, y_train, epochs = 3, batch_size = 32)


        # Do the prediction
        extended_test_set = mid_prices[-TEST_DATA_SIZE - TRAINING_PERIOD_SIZE:]

        X_test = []
        for i in range(TRAINING_PERIOD_SIZE, TEST_DATA_SIZE + TRAINING_PERIOD_SIZE):
            X_test.append(extended_test_set[i - TRAINING_PERIOD_SIZE:i, 0])
            
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        predicted_stock_price = regressor.predict(X_test)


        real_price = mid_prices[-1]
        predicted_price = predicted_stock_price[-1]

        return predicted_price, real_price


