import requests
import csv
import numpy as np

from common_function import *
 

class IndicesProvider:

    INDICES_DATA_STORE_FOLDER = "ccdatastore/Raw/indices/"

    def __init__(self):
        self.cci30_provider = Cci30IndicesProvier(IndicesProvider.INDICES_DATA_STORE_FOLDER)
    
    def get_cci30_indices(self, date):
        return self.cci30_provider.get_cci30_indices(date)
    
    
class Cci30IndicesProvier:

    DATA_NAME_TEMPLATE = "cci30indices/cci30indices_{}.csv"

    URL = "https://cci30.com/ajax/getDataForIndexChart.php"
    
    def __init__(self, data_folder):
        self.data_folder = data_folder
    
    
    def get_cci30_indices(self, date):
        data_file = self.get_data_file_full_name(date)
        if (not does_file_exist(data_file)):
            try:
                response = requests.get(url = Cci30IndicesProvier.URL)
                if (response.status_code == 200):
                    with open(data_file, mode='w') as output_file:
                        output_file.write(response.text)
            except:
                print("Something wrong while retrieving data from {}".format(Cci30IndicesProvier.URL))
                return None
        
        cci30_open = []
        cci30_close = []
        cci30_high = []
        cci30_low = []
        
        with open(data_file, mode='r') as input_file:
            reader = csv.reader(input_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                cci30_open.insert(0, row[1])
                cci30_high.insert(0, row[2])
                cci30_low.insert(0, row[3])
                cci30_close.insert(0, row[4])
            

        cci30_open_array = np.asarray(cci30_high, dtype=float, order=None)
        cci30_high_array = np.asarray(cci30_high, dtype=float, order=None)
        cci30_low_array = np.asarray(cci30_low, dtype=float, order=None)
        cci30_close_array = np.asarray(cci30_close, dtype=float, order=None)
        
        cci30_data = { "open":cci30_open_array, "high":cci30_high_array, "low":cci30_low_array, "close":cci30_close_array }
        return cci30_data
        
        
    def get_data_file_full_name(self, date):
        return self.data_folder + Cci30IndicesProvier.DATA_NAME_TEMPLATE.format(date.strftime("%Y%m%d"))
    
    
    
    