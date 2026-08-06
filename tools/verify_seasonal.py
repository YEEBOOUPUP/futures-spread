# -*- coding: utf-8 -*-
"""验证日度季节性图数据构造：MM-DD 并集、每年点数、时间轴过滤"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, 'data', 'data.json'), encoding='utf-8'))
dates = d['dates']
s = d['series']
p01, p05 = s['P']['01']['close'], s['P']['05']['close']

joined = []
for i in range(min(len(p01), len(p05))):
    if p01[i] is None or p05[i] is None:
        continue
    joined.append((dates[i], p01[i] - p05[i]))

# 模拟时间轴范围过滤（例如 2018-01-01 ~ 2024-12-31）
d0, d1 = '2018-01-01', '2024-12-31'
filtered = [(dd, v) for dd, v in joined if d0 <= dd <= d1]
print(f'全量 {len(joined)} 天；范围过滤 {d0}~{d1} 后 {len(filtered)} 天')

# 日度季节性：MM-DD 并集
mmdd = sorted({dd[5:] for dd, _ in filtered})
by_year = {}
for dd, v in filtered:
    by_year.setdefault(dd[:4], {})[dd[5:]] = v
years = sorted(by_year)
print(f'MM-DD 并集 {len(mmdd)} 个（首 {mmdd[0]} 尾 {mmdd[-1]}）')
print(f'年份数 {len(years)}: {years}')
for y in (years[0], years[-1]):
    pts = len(by_year[y])
    print(f'  {y}年 {pts} 个交易日点（首 {min(by_year[y])} 尾 {max(by_year[y])}）')
# 对齐检查：每年在并集上的点数
print(f'每年对齐到 {len(mmdd)} 个横轴位置的缺失(null)数示例:')
for y in (years[0], years[-1]):
    missing = len(mmdd) - len(by_year[y])
    print(f'  {y}年 null 数 = {missing}')
