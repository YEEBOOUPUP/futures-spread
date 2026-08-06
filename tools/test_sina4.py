# -*- coding: utf-8 -*-
"""确认新浪历史深度边界（2015-2020）"""
import akshare as ak

for sym in ['P1601', 'P1801', 'P2001', 'P1505', 'M1505', 'Y1501', 'OI1501']:
    try:
        df = ak.futures_zh_daily_sina(symbol=sym)
        print(f'{sym}: {len(df)} 行' + (f', 首={df.iloc[0]["date"]} 尾={df.iloc[-1]["date"]}' if len(df) else ' (空)'))
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:60]}')
