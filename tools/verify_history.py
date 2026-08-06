# -*- coding: utf-8 -*-
"""小范围验证：重建 P/Y/OI/M/RM 五个品种（新浪 2019+），与现有 Excel 数据对比"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'collector'))
import history_fill as hf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. 只处理 5 个核心品种
products = hf.get_products()
core = {k: products[k] for k in ['P', 'Y', 'OI', 'M', 'RM'] if k in products}
print('核心品种:', {k: (v['name'], sorted(v['months'])) for k, v in core.items()})

series = hf.build_product_series(core, 2026, log=lambda *a, **k: print(*a))

# 2. 与现有 Excel 数据对比（P 01 月）
excel = json.load(open(os.path.join(BASE, 'data', 'data.json'), encoding='utf-8'))
excel_dates = excel['dates']
excel_p01 = excel['series']['P']['01']['close']
print('\n--- P 01月 close 对比（抽样 6 个日期）---')
new_p01 = series.get('P', {}).get('01', {})
sample_dates = [d for d in excel_dates if d >= '2019-01-01'][::300][:6]
ok = 0
for d in sample_dates:
    old = excel_p01[excel_dates.index(d)]
    new = new_p01.get(d)
    match = '✓' if (old is not None and new is not None and abs(old - new) < 1.0) else '✗'
    if match == '✓':
        ok += 1
    print(f'  {d}: Excel={old}  新浪={new}  {match}')
print(f'对比通过 {ok}/{len(sample_dates)}')

# 3. 统计重建结果
for code in ['P', 'Y', 'OI', 'M', 'RM']:
    s = series.get(code, {})
    days = len(set().union(*[set(v.keys()) for v in s.values()])) if s else 0
    print(f'{code}: 月份={sorted(s.keys())} 交易日≈{days}')

# 4. 输出重建文件（供后续全量脚本参考格式）
outdir = os.path.join(BASE, 'data', 'v2test')
os.makedirs(outdir, exist_ok=True)
for code in ['P', 'Y', 'OI', 'M', 'RM']:
    s = series.get(code, {})
    if not s:
        continue
    dates = sorted(set().union(*[set(v.keys()) for v in s.values()]))
    out = {'dates': dates, 'series': {m: {'close': [s[m].get(d) for d in dates]} for m in s}}
    with open(os.path.join(outdir, code + '.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
print('\n验证文件已输出到 data/v2test/')
