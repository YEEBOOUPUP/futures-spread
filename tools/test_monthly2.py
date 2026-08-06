# -*- coding: utf-8 -*-
"""测试新浪外盘月份合约（CBOT 标准月份代码）"""
import akshare as ak

# 美豆月份：F=1月 H=3月 K=5月 N=7月 U=9月 X=11月；26=2026年
tests = [
    ('ZSX25', '美豆 2025年11月'), ('ZSF26', '美豆 2026年1月'), ('ZSH26', '美豆 2026年3月'),
    ('ZSK26', '美豆 2026年5月'), ('ZSN26', '美豆 2026年7月'), ('ZSU26', '美豆 2026年9月'),
    ('ZSL6', '美豆油 2026年7月(推测)'), ('BOM6', '美豆油 2026年6月(推测)'),
]
for sym, desc in tests:
    try:
        df = ak.futures_foreign_hist(symbol=sym)
        print(f'{sym} [{desc}]: {len(df)} 行' + (f', {df.iloc[0]["date"]} ~ {df.iloc[-1]["date"]}' if len(df) else ' (空)'))
    except Exception as e:
        print(f'{sym} [{desc}]: 失败 {type(e).__name__}: {str(e)[:70]}')
