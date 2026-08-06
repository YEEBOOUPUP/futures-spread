# -*- coding: utf-8 -*-
"""获取东财外盘全部品种代码（含月份合约）"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
import akshare as ak

try:
    df = ak.futures_global_spot_em()
    print('东财外盘品种:', len(df), '行')
    print('列:', list(df.columns))
    print(df.head(20).to_string())
except Exception as e:
    print('失败:', type(e).__name__, str(e)[:150])
