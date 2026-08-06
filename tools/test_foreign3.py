# -*- coding: utf-8 -*-
"""获取新浪外盘期货全部品种代码"""
import akshare as ak

try:
    df = ak.futures_foreign_commodity_subscribe_exchange_symbol()
    print('外盘品种:', len(df), '行')
    print(df.to_string())
except Exception as e:
    print('失败:', type(e).__name__, str(e)[:150])
