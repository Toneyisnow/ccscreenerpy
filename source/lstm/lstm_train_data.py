import pandas as pd
from pandas import DataFrame as df
import csv

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from sklearn import preprocessing
import tensorflow as tf
import numpy as np


from data_generator import *
import ccdata



def lstm_train_run():

    high_prices = ccdata.get_one("BTC", "D", "high")
    low_prices = ccdata.get_one("BTC", "D", "low")
    
    high_prices = high_prices[1100:]
    low_prices = low_prices[1100:]

    TRAIN_DATA_SIZE = 700
    TEST_DATA_SIZE = 200

    #high_prices = np.asmatrix(high_prices, dtype = None)
    #low_prices = np.asmatrix(low_prices, dtype = None)

    ##
    #plt.figure(figsize = (18,9))
    #plt.plot(range(df.shape[0]),(df['Low']+df['High'])/2.0)
    #plt.xticks(range(0,df.shape[0],500),df['Date'].loc[::500],rotation=45)
    #plt.xlabel('Date',fontsize=18)
    #plt.ylabel('Mid Price',fontsize=18)
    #plt.show()

    # Step 1: Get Source Data
    mid_prices = (high_prices + low_prices) / 2.0
    train_data = mid_prices[:TRAIN_DATA_SIZE]
    test_data = mid_prices[TRAIN_DATA_SIZE:]


    #Step 2: Scale the data
    scaler = preprocessing.MinMaxScaler()
    scaler.fit(mid_prices.reshape(-1, 1))

    train_data = scaler.transform(train_data.reshape(-1, 1)).reshape(-1)
    test_data = scaler.transform(test_data.reshape(-1, 1)).reshape(-1)
    
    # Smoothing the train data
    EMA = 0.0
    gamma = 0.1
    for ti in range(TRAIN_DATA_SIZE):
        EMA = gamma * train_data[ti] + (1 - gamma) * EMA
        train_data[ti] = EMA

    all_mid_data = np.concatenate([train_data, test_data], axis = 0)


    # LSTM

    D = 1 
    num_unrollings = 50 
    batch_size = 40
    num_nodes = [20,20,15] 
    n_layers = len(num_nodes) 
    dropout = 0.2 

    tf.reset_default_graph()


    train_inputs, train_outputs = [],[]
    for ui in range(num_unrollings):
        train_inputs.append(tf.placeholder(tf.float32, shape=[batch_size, D],name='train_inputs_%d'%ui))
        train_outputs.append(tf.placeholder(tf.float32, shape=[batch_size, 1], name = 'train_outputs_%d'%ui))

    lstm_cells = [
    tf.contrib.rnn.LSTMCell(num_units=num_nodes[li],
                            state_is_tuple=True,
                            initializer= tf.contrib.layers.xavier_initializer()
                            )
    for li in range(n_layers)]

    drop_lstm_cells = [tf.contrib.rnn.DropoutWrapper(
    lstm, input_keep_prob=1.0,output_keep_prob=1.0-dropout, state_keep_prob=1.0-dropout
    ) for lstm in lstm_cells]
    drop_multi_cell = tf.contrib.rnn.MultiRNNCell(drop_lstm_cells)
    multi_cell = tf.contrib.rnn.MultiRNNCell(lstm_cells)

    w = tf.get_variable('w',shape=[num_nodes[-1], 1], initializer=tf.contrib.layers.xavier_initializer())
    b = tf.get_variable('b',initializer=tf.random_uniform([1],-0.1,0.1))


    c, h = [],[]
    initial_state = []
    for li in range(n_layers):
        c.append(tf.Variable(tf.zeros([batch_size, num_nodes[li]]), trainable=False))
        h.append(tf.Variable(tf.zeros([batch_size, num_nodes[li]]), trainable=False))
        initial_state.append(tf.contrib.rnn.LSTMStateTuple(c[li], h[li]))

    all_inputs = tf.concat([tf.expand_dims(t,0) for t in train_inputs],axis=0)

    all_lstm_outputs, state = tf.nn.dynamic_rnn(
        drop_multi_cell, all_inputs, initial_state=tuple(initial_state),
        time_major = True, dtype=tf.float32)

    all_lstm_outputs = tf.reshape(all_lstm_outputs, [batch_size*num_unrollings,num_nodes[-1]])
    all_outputs = tf.nn.xw_plus_b(all_lstm_outputs,w,b)
    split_outputs = tf.split(all_outputs,num_unrollings,axis=0)


    print('Defining training Loss')
    loss = 0.0
    with tf.control_dependencies([tf.assign(c[li], state[li][0]) for li in range(n_layers)]+
                                [tf.assign(h[li], state[li][1]) for li in range(n_layers)]):
        for ui in range(num_unrollings):
            loss += tf.reduce_mean(0.5*(split_outputs[ui]-train_outputs[ui])**2)

    print('Learning rate decay operations')
    global_step = tf.Variable(0, trainable=False)
    inc_gstep = tf.assign(global_step,global_step + 1)
    tf_learning_rate = tf.placeholder(shape=None,dtype=tf.float32)
    tf_min_learning_rate = tf.placeholder(shape=None,dtype=tf.float32)

    learning_rate = tf.maximum(
        tf.train.exponential_decay(tf_learning_rate, global_step, decay_steps=1, decay_rate=0.5, staircase=True),
        tf_min_learning_rate)

    # Optimizer.
    print('TF Optimization operations')
    optimizer = tf.train.AdamOptimizer(learning_rate)
    gradients, v = zip(*optimizer.compute_gradients(loss))
    gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
    optimizer = optimizer.apply_gradients(zip(gradients, v))

    print('All done')

    print('Defining prediction related TF functions')
    sample_inputs = tf.placeholder(tf.float32, shape=[1,D])
    sample_c, sample_h, initial_sample_state = [],[],[]
    for li in range(n_layers):
        sample_c.append(tf.Variable(tf.zeros([1, num_nodes[li]]), trainable=False))
        sample_h.append(tf.Variable(tf.zeros([1, num_nodes[li]]), trainable=False))
        initial_sample_state.append(tf.contrib.rnn.LSTMStateTuple(sample_c[li],sample_h[li]))

    reset_sample_states = tf.group(*[tf.assign(sample_c[li],tf.zeros([1, num_nodes[li]])) for li in range(n_layers)],
                                *[tf.assign(sample_h[li],tf.zeros([1, num_nodes[li]])) for li in range(n_layers)])

    sample_outputs, sample_state = tf.nn.dynamic_rnn(multi_cell, tf.expand_dims(sample_inputs,0),
                                    initial_state=tuple(initial_sample_state),
                                    time_major = True,
                                    dtype=tf.float32)

    with tf.control_dependencies([tf.assign(sample_c[li],sample_state[li][0]) for li in range(n_layers)]+
                                [tf.assign(sample_h[li],sample_state[li][1]) for li in range(n_layers)]):  
        sample_prediction = tf.nn.xw_plus_b(tf.reshape(sample_outputs,[1,-1]), w, b)

    print('All done')



    # Run LSTM
    epochs = 40
    valid_summary = 1 
    n_predict_once = 30
    train_seq_length = train_data.size
    train_mse_ot = [] 
    test_mse_ot = [] 
    predictions_over_time = []
    session = tf.InteractiveSession()
    tf.global_variables_initializer().run()
    loss_nondecrease_count = 0
    loss_nondecrease_threshold = 2 

    print('Initialized')
    average_loss = 0
    data_gen = DataGeneratorSeq(train_data, batch_size, num_unrollings) 
    x_axis_seq = []
    test_points_seq = np.arange(TRAIN_DATA_SIZE - TEST_DATA_SIZE, TRAIN_DATA_SIZE + TEST_DATA_SIZE, 5).tolist() 
    for ep in range(epochs):       

        print("Start epochs {}".format(ep))

        # ========================= Training =====================================
        for step in range(train_seq_length//batch_size):
            u_data, u_labels = data_gen.unroll_batches()
            feed_dict = {}
            for ui,(dat,lbl) in enumerate(zip(u_data,u_labels)):            
                feed_dict[train_inputs[ui]] = dat.reshape(-1,1)
                feed_dict[train_outputs[ui]] = lbl.reshape(-1,1)

            feed_dict.update({tf_learning_rate: 0.0001, tf_min_learning_rate:0.000001})
            _, l = session.run([optimizer, loss], feed_dict=feed_dict)
            average_loss += l
            # print("step={}".format(step))

        # ============================ Validation ==============================
        if (ep + 1) % valid_summary == 0:

            average_loss = average_loss/(valid_summary*(train_seq_length//batch_size))

            # The average loss
            if (ep + 1) % valid_summary == 0:
                print('Average loss at step %d: %f' % (ep+1, average_loss))

            train_mse_ot.append(average_loss)
            average_loss = 0 # reset loss
            predictions_seq = []
            mse_test_loss_seq = []

            # ===================== Updating State and Making Predicitons ========================
            for w_i in test_points_seq:

                mse_test_loss = 0.0
                our_predictions = []

                if (ep + 1) - valid_summary == 0:
                    # Only calculate x_axis values in the first validation epoch
                    x_axis=[]

                # Feed in the recent past behavior of stock prices
                # to make predictions from that point onwards
                for tr_i in range(w_i-num_unrollings + 1, w_i - 1):
                    current_price = all_mid_data[tr_i]
                    feed_dict[sample_inputs] = np.array(current_price).reshape(1, 1)    
                    _ = session.run(sample_prediction,feed_dict=feed_dict)

                feed_dict = {}
                current_price = all_mid_data[w_i-1]
                feed_dict[sample_inputs] = np.array(current_price).reshape(1, 1)
                # Make predictions for this many steps
                # Each prediction uses previous prediciton as it's current input
                for pred_i in range(n_predict_once):

                    # Out of index range
                    if w_i + pred_i >= TRAIN_DATA_SIZE + TEST_DATA_SIZE:
                        continue

                    pred = session.run(sample_prediction,feed_dict=feed_dict)
                    our_predictions.append(np.asscalar(pred))
                    feed_dict[sample_inputs] = np.asarray(pred).reshape(-1, 1)

                    if (ep + 1) - valid_summary == 0:
                        # Only calculate x_axis values in the first validation epoch
                        x_axis.append(w_i + pred_i)
                        mse_test_loss += 0.5*(pred-all_mid_data[w_i+pred_i])**2

                session.run(reset_sample_states)
                predictions_seq.append(np.array(our_predictions))
                mse_test_loss /= n_predict_once
                mse_test_loss_seq.append(mse_test_loss)

                if (ep + 1) - valid_summary == 0:
                    x_axis_seq.append(x_axis)

            current_test_mse = np.mean(mse_test_loss_seq)

            # Learning rate decay logic
            if len(test_mse_ot) > 0 and current_test_mse > min(test_mse_ot):
                loss_nondecrease_count += 1
            else:
                loss_nondecrease_count = 0

            if loss_nondecrease_count > loss_nondecrease_threshold :
                session.run(inc_gstep)
                loss_nondecrease_count = 0
                print('Decreasing learning rate by 0.5')

            test_mse_ot.append(current_test_mse)
            print('Test MSE: %.5f'%np.mean(mse_test_loss_seq))
            predictions_over_time.append(predictions_seq)
            print('Finished Predictions')

    print('Training finished.')

    np.save("ccdatastore/Strategy/LSTM/predictions", predictions_over_time)
    np.save("ccdatastore/Strategy/LSTM/x_axis_seq", x_axis_seq)

    print('Result saved to files.')
