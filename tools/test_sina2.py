# -*- coding: utf-8 -*-
"""测试新浪历史合约深度与郑商所代码格式"""
import akshare as ak

tests = [
    ('P1501', '大商所2015年01合约（历史）'),
    ('Y1505', '大商所2015年05合约（历史）'),
    ('OI2609', '郑商所 年4位格式'),
    ('OI609', '郑商所 交易所格式'),
    ('OI1601', '郑商所2016年01合约（历史）'),
    ('RM1605', '郑商所2016年05合约（历史）'),
    ('M1509', '豆粕2015年09合约（历史）'),
]
for sym, desc in tests:
    try:
        df = ak.futures_zh_daily_sina(symbol=sym)
        print(f'{sym} [{desc}]: {len(df)} 行', end='')
        if len(df):
            print(f', 首={df.iloc[0]["date"]} 尾={df.iloc[-1]["date"]}')
        else:
            print(' (空)')
    except Exception as e:
        print(f'{sym} [{desc}]: 失败 {type(e).__name__}: {str(e)[:80]}')
