# -*- coding: utf-8 -*-
"""调试 futures_global_hist_em（设代理）"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
import akshare as ak

for sym in ['ZS26Z', 'ZS00Y', 'ZW26U', 'FCPO0']:
    try:
        df = ak.futures_global_hist_em(symbol=sym)
        print(f'{sym}: {len(df)} 行, 列={list(df.columns)[:6]}')
        if len(df):
            print(f'  首={df.iloc[0,0]} 尾={df.iloc[-1,0]}')
            print(df.tail(1).to_string())
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:120]}')
