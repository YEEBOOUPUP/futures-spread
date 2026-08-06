# -*- coding: utf-8 -*-
"""测试新浪历史深度 + 其他数据源"""
import akshare as ak

print('--- 新浪历史深度测试 ---')
for sym in ['P2401', 'P2301', 'P2201', 'M2409']:
    try:
        df = ak.futures_zh_daily_sina(symbol=sym)
        print(f'{sym}: {len(df)} 行' + (f', 首={df.iloc[0]["date"]} 尾={df.iloc[-1]["date"]}' if len(df) else ' (空)'))
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}')

print('--- get_futures_daily 其他市场 ---')
for mkt in ['CZCE', 'SHFE', 'INE']:
    try:
        df = ak.get_futures_daily(start_date='20260805', end_date='20260805', market=mkt)
        print(f'{mkt}: {len(df)} 行, 列={list(df.columns)[:6]}')
    except Exception as e:
        print(f'{mkt}: 失败 {type(e).__name__}: {str(e)[:60]}')
