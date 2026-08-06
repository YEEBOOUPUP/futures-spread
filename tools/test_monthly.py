# -*- coding: utf-8 -*-
"""探测外盘月度合约数据源"""
import akshare as ak
import inspect

# 1. 东财外盘历史（可能含月份合约）
print('=== futures_global_hist_em ===')
try:
    print('签名:', inspect.signature(ak.futures_global_hist_em))
except Exception as e:
    print('签名失败:', e)
for sym in ['ZSD', 'ZSM', 'BO', 'FCPO', 'GC', 'CL']:
    try:
        df = ak.futures_global_hist_em(symbol=sym)
        print(f'{sym}: {len(df)} 行, 列={list(df.columns)[:8]}')
        if len(df):
            print(f'  首={df.iloc[0, 0]} 尾={df.iloc[-1, 0]}')
            print(df.tail(1).to_string())
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:90]}')
