# -*- coding: utf-8 -*-
"""测试 ak.futures_foreign_hist（外盘历史）"""
import akshare as ak
import inspect

try:
    print('签名:', inspect.signature(ak.futures_foreign_hist))
except Exception as e:
    print('签名获取失败:', e)

for sym in ['ZSD', 'ZSO', 'ZSM', 'FCPO']:
    try:
        df = ak.futures_foreign_hist(symbol=sym)
        print(f'{sym}: {len(df)} 行, 列={list(df.columns)}')
        if len(df):
            print(f'  首={df.iloc[0]["date"]} 尾={df.iloc[-1]["date"]}')
            print(df.tail(2).to_string())
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:120]}')
