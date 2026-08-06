# -*- coding: utf-8 -*-
"""验证时间快捷键：从最新日期回推 N 个月，检查在交易日序列中锁定的范围"""
import json
import os
from datetime import datetime, timedelta
from calendar import monthrange


def shift_date(date_str, months):
    y, m, d = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
    m += months
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    d = min(d, monthrange(y, m)[1])
    return f'{y}-{m:02d}-{d:02d}'


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, 'data', 'data.json'), encoding='utf-8'))
dates = d['dates']
last = dates[-1]
print('最新交易日:', last, ' 交易日总数:', len(dates))

for months in (1, 6, 12):
    start = shift_date(last, -months)
    i = next((idx for idx, x in enumerate(dates) if x >= start), len(dates))
    print(f'最近{months}月: 目标起始 {start} → 锁定 {dates[i]} ~ {last}  ({len(dates) - i} 个交易日)')
