# -*- coding: utf-8 -*-
"""实测新浪外盘全部 30 个品种的历史数据"""
import akshare as ak

symbols = ['FEF', 'FCPO', 'RSS3', 'RS', 'BTC', 'CT', 'NID', 'PBD', 'SND', 'ZSD',
           'AHD', 'CAD', 'S', 'W', 'C', 'BO', 'SM', 'TRB', 'HG', 'NG',
           'CL', 'SI', 'GC', 'LHC', 'OIL', 'XAU', 'XAG', 'XPT', 'XPD', 'EUA']

for sym in symbols:
    try:
        df = ak.futures_foreign_hist(symbol=sym)
        n = len(df)
        if n:
            print(f'{sym}: OK {n} 行, {df.iloc[0]["date"]} ~ {df.iloc[-1]["date"]}, 尾close={df.iloc[-1]["close"]}')
        else:
            print(f'{sym}: 空')
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}')
