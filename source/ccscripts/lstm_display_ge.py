import pandas as pd
from pandas import DataFrame as df

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from sklearn import preprocessing

import numpy as np

import tensorflow as tf

from data_generator import *


import csv


data = pd.read_csv("D:/Temp/lstm_test/price-volume-data-for-all-us-stocks-etfs/Data/Stocks/ge.us.txt")
df = data.sort_values('Date')

predictions_over_time = np.load("D:/Temp/lstm_test/predictions.npy")
x_axis_seq = np.load("D:/Temp/lstm_test/x_axis_seq.npy")
    

high_prices = df.loc[:,'High'].as_matrix()
low_prices = df.loc[:,'Low'].as_matrix()
mid_prices = (high_prices+low_prices)/2.0

train_data = mid_prices[:11000]
test_data = mid_prices[11000:]

scaler = preprocessing.MinMaxScaler()
train_data = train_data.reshape(-1,1)
test_data = test_data.reshape(-1,1)

smoothing_window_size = 2500
for di in range(0, 10000, smoothing_window_size):
    print("looping {}".format(di))
    scaler.fit(train_data[di:di + smoothing_window_size,:])
    train_data[di:di + smoothing_window_size,:] = scaler.transform(train_data[di:di + smoothing_window_size,:])


# You normalize the last bit of remaining data 
scaler.fit(train_data[di+smoothing_window_size:,:])
train_data[di+smoothing_window_size:,:] = scaler.transform(train_data[di+smoothing_window_size:,:])


train_data = train_data.reshape(-1)
test_data = scaler.transform(test_data).reshape(-1)


# Smoothing the train data
EMA = 0.0
gamma = 0.1
for ti in range(11000):
 EMA = gamma*train_data[ti] + (1-gamma)*EMA
 train_data[ti] = EMA

all_mid_data = np.concatenate([train_data, test_data],axis=0)




best_prediction_epoch = 18
plt.figure(figsize = (18,18))
plt.subplot(2,1,1)
plt.plot(range(df.shape[0]),all_mid_data,color='b')

#predictions with high alpha
start_alpha = 0.25
alpha  = np.arange(start_alpha,1.1,(1.0-start_alpha)/len(predictions_over_time[::3]))
for p_i, p in enumerate(predictions_over_time[::3]):
   for xval, yval in zip(x_axis_seq, p):
       plt.plot(xval, yval, color='r',alpha=alpha[p_i])

plt.title('Evolution of Test Predictions Over Time',fontsize=18)
plt.xlabel('Date',fontsize=18)
plt.ylabel('Mid Price',fontsize=18)
plt.xlim(8000, 15000)

plt.subplot(2, 1, 2)

plt.plot(range(df.shape[0]), all_mid_data, color='b')
for xval,yval in zip(x_axis_seq, predictions_over_time[best_prediction_epoch]):
   plt.plot(xval, yval, color='r')
   
plt.title('Best Test Predictions Over Time', fontsize=18)
plt.xlabel('Date', fontsize=18)
plt.ylabel('Mid Price', fontsize=18)
plt.xlim(8000, 15000)
plt.show()


