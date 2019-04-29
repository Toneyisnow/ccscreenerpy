from multiprocessing.managers import SyncManager
import sys, time
import numpy as np
import pandas as pd
import copy
from pandas import Series,DataFrame

class MyManager(SyncManager):
    pass

MyManager.register("get_data")
MyManager.register("get_all_df")
MyManager.register("get_all")
MyManager.register("get_one")
manager = MyManager(("127.0.0.1", 5000), authkey=str.encode("password","utf-8"))
manager.connect()


def update_variable(var,new_data):
    the_dict = manager.get_data()
    the_dict.update([(var,new_data)])
    return True

def get_variable(var):
    the_dict = manager.get_data()
    return the_dict.get(var)

def get_all_df(dtype,field):
    the_rs = manager.get_all_df(dtype,field)
    new_df=the_rs.copy()
    return new_df

def get_coins():
    the_dict = manager.get_data()
    return the_dict.get("meta_coins")

def get_metas():
    the_dict = manager.get_data()
    return the_dict.get("meta_snapshot")

def get_one(_coin,dtype="D",field="close"):
    coin=_coin
    coin=coin.upper()
    rs = manager.get_one(coin,dtype,field)
    rs=copy.deepcopy(rs)
    return rs

def get_all(dtype="D",field="close"):
    rs = manager.get_all(dtype,field)
    return rs

def test():
    the_dict = manager.get_data()
    return the_dict.get("meta_snapshot")

