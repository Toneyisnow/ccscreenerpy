# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import pandas as pd

import talib

'''
本策略通过计算CZCE.FG801和SHFE.rb1801的ATR.唐奇安通道和MA线,并:
上穿唐奇安通道且短MA在长MA上方则开多仓,下穿唐奇安通道且短MA在长MA下方则开空仓
若有 多/空 仓位则分别:
价格 跌/涨 破唐奇安平仓通道 上/下 轨则全平仓位,否则
根据 跌/涨 破持仓均价 -/+ x(x=0.5,1,1.5,2)倍ATR把仓位
回测数据为:CZCE.FG801和SHFE.rb1801的1min数据
回测时间为:2017-09-15 09:15:00到2017-10-01 15:00:00
'''

def init(context):
    # context.parameter分别为唐奇安开仓通道.唐奇安平仓通道.短ma.长ma.ATR的参数
    context.parameter = [55, 20, 10, 60, 20]
    context.tar = context.parameter[4]
    # context.goods交易的品种
    context.goods = ['CZCE.FG801', 'SHFE.rb1801']
    # context.ratio交易最大资金比率
    context.ratio = 0.8
    # 订阅context.goods里面的品种, bar频率为1min
    subscribe(symbols=context.goods, frequency='60s', count=101)
    # 止损的比例区间


def on_bar(context, bars):
    
    DON_OPEN = 20
    DON_CLOSE = 10
    MA_SHORT = 10
    MA_LONG = 60
    TAR = 20
    RATIO = 0.8

    bar = bars[0]
    symbol = bar['symbol']
    recent_data = context.data(symbol = symbol, frequency = '60s', count = 101, fields = 'close,high,low')
    close = recent_data['close'].values[-1]
    
    # 计算ATR
    atr = talib.ATR(recent_data['high'].values, recent_data['low'].values, recent_data['close'].values, timeperiod = TAR)[-1]
    
    # 计算唐奇安开仓和平仓通道
    upper_band = talib.MAX(recent_data['close'].values[:-1], timeperiod = DON_OPEN)[-1]
    lower_band = talib.MIN(recent_data['close'].values[:-1], timeperiod = DON_CLOSE)[-1]
    
    # 计算开仓的资金比例
    percent = RATIO / float(len(context.goods))
    
    # 若没有仓位则开仓
    position = context.account().position(symbol = symbol)
    
    if not position:

        # 计算长短ma线.DIF
        ma_short = talib.MA(recent_data['close'].values, timeperiod=(MA_SHORT + 1))[-1]
        ma_long = talib.MA(recent_data['close'].values, timeperiod=(MA_LONG + 1))[-1]
        dif = ma_short - ma_long

        # 获取当前价格
        # 上穿唐奇安通道且短ma在长ma上方则开仓
        if (close > upper_band and dif > 0):
            order_target_percent(symbol = symbol, percent = percent, order_type = OrderType_Market)
            print(symbol, '市价单开多仓到比例: ', percent)

    else:
        # 价格跌破唐奇安平仓通道全平仓位止损
        if close < lower_band:
            order_close_all()
            print(symbol, '市价单全平仓位')
        else:
            # 获取持仓均价
            vwap = position_long['vwap']
            
            # 获取持仓的资金
            money = position_long['cost']

            # 获取平仓的区间
            band = vwap - np.array([200, 2, 1.5, 1, 0.5, -100]) * atr
            grid_percent = float(pd.cut([close], band, labels=[0, 0.25, 0.5, 0.75, 1])[0]) * percent

            # 选择现有百分比和区间百分比中较小的值(避免开仓)
            target_percent = np.minimum(money / context.account().cash['nav'], grid_percent)
            if target_percent != 1.0:
                print(symbol, '市价单平多仓到比例: ', target_percent)
                order_target_percent(symbol = symbol, percent = target_percent)
    

