import sys, logging, time
from multiprocessing import Process

import asyncio
from datetime import datetime

from lstm_prediction import *
from lstmv2_prediction import *


class PredictionManager:

    def __init__(self):
        pass

    # Trigger the LSTM Predictions to predict
    def trigger_predictions_bak(self):

        logging.info("PredictionManager: Start trigger_predictions...")
        
        start = time.time()
        loop = asyncio.get_event_loop()
        
        tasks = [
            asyncio.ensure_future(self.start_lstm_prediction()),
            asyncio.ensure_future(self.start_lstmv2_prediction())
            ]

        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

        end = time.time()
        
        logging.info("PredictionManager: End trigger_predictions. Total time: {}".format(end - start))


    def start_lstm_prediction(self):
        lstm = LSTMPrediction()
        lstm.analysis()


    def start_lstmv2_prediction(self):
        lstm = LSTMV2Prediction()
        lstm.analysis()


    def trigger_predictions(self):

        procs = []
        proc = Process(target = self.start_lstm_prediction)  # instantiating without any argument
        procs.append(proc)
        proc.start()
        proc = Process(target = self.start_lstmv2_prediction)  # instantiating without any argument
        procs.append(proc)
        proc.start()

        # complete the processes
        for proc in procs:
            proc.join()