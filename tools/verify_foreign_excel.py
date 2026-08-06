# -*- coding: utf-8 -*-
"""验证外盘导入数据"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for code in ['F_FCPO', 'F_BO']:
    f = json.load(open(os.path.join(BASE, 'data', code + '.json'), encoding='utf-8'))
    print(f'=== {code} ===')
    print('dates:', len(f['dates']), f['dates'][0], '~', f['dates'][-1])
    for label in list(f['series'])[:4]:
        arr = f['series'][label]['close']
        print(f'  {label}: 尾={arr[-1]} (2026-08-06), 首={next((v for v in arr if v is not None), None)}')
idx = json.load(open(os.path.join(BASE, 'data', 'index.json'), encoding='utf-8'))
print('\nF_FCPO 条目:', idx['products'].get('F_FCPO'))
print('F_BO 条目:', idx['products'].get('F_BO'))
print('外盘品种数:', sum(1 for p in idx['products'].values() if p.get('foreign')))
print('总品种数:', len(idx['products']))
