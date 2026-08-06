# -*- coding: utf-8 -*-
"""实测新浪期货日线接口"""
import akshare as ak

for sym in ['P2601', 'p2601', 'OI609', 'm2609', 'RB2610']:
    try:
        df = ak.futures_zh_daily_sina(symbol=sym)
        cols = list(df.columns)
        print(f'{sym}: {len(df)} 行, 列={cols}')
        print(f'  首={df.iloc[0]["date"]} 尾={df.iloc[-1]["date"]}')
        print(df.tail(2).to_string())
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:120]}')
