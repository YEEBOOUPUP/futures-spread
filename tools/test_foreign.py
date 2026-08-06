# -*- coding: utf-8 -*-
"""测试新浪外盘期货数据（akshare futures_foreign_commodity_hist）"""
import akshare as ak

# 常见外盘品种：美豆 ZSD / 美豆油 ZSO / 美豆粕 ZSM / 玉米 ZSC / 马棕油 FCPO 等
for sym in ['ZSD', 'ZSO', 'ZSM', 'FCPO', 'OIL']:
    try:
        df = ak.futures_foreign_commodity_hist(symbol=sym)
        cols = list(df.columns)
        print(f'{sym}: {len(df)} 行, 列={cols}')
        if len(df):
            print(f'  首={df.iloc[0]["date"]} 尾={df.iloc[-1]["date"]}')
            print(df.tail(2).to_string())
    except Exception as e:
        print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:120]}')
