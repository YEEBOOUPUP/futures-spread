# -*- coding: utf-8 -*-
"""探测东财外盘品种分组（620 合约 → 品种 + 月份）"""
import os
import re
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
import akshare as ak

spot = ak.futures_global_spot_em()
# 代码解析：字母前缀 + 数字/字母后缀
groups = {}
for _, row in spot.iterrows():
    code = str(row['代码'])
    name = str(row['名称'])
    m = re.match(r'^([A-Z]+)(\d{2}[A-Z]|00Y|00Z|00N|0\d)', code)
    if not m:
        continue
    prefix, suffix = m.group(1), m.group(2)
    # 品种名：名称去数字（"大豆2809"→"大豆"）
    pname = re.sub(r'[0-9]+', '', name).replace('当月连续', '').replace('连续', '').strip()
    groups.setdefault(prefix, {'name': pname, 'months': set()})
    if suffix not in ('00Y', '00Z', '00N'):
        mo = re.search(r'\d{2}([A-Z])$', suffix)
        if mo:
            groups[prefix]['months'].add(mo.group(1))

print('外盘品种数:', len(groups))
for prefix in sorted(groups):
    g = groups[prefix]
    print(f'{prefix}\t{g["name"]}\t活跃月份字母: {"".join(sorted(g["months"])) or "(仅连续)"}')
