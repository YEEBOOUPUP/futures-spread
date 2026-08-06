# -*- coding: utf-8 -*-
"""验证重建后的 index.json 与品种文件"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open(os.path.join(BASE, 'data', 'index.json'), encoding='utf-8'))
print('updated_at:', idx['updated_at'])
print('品种数:', len(idx['products']))
for code in ['P', 'Y', 'OI', 'M', 'RM', 'RB', 'CU', 'I', 'IF']:
    p = idx['products'].get(code)
    if not p:
        continue
    f = json.load(open(os.path.join(BASE, 'data', p['file']), encoding='utf-8'))
    p01 = f['series'].get('01', {}).get('close', ['无'])
    print(f'{code} ({p["name"]}): 合约 {len(p["contracts"])} 个, dates {len(f["dates"])} 天, '
          f'首 {f["dates"][0]} 尾 {f["dates"][-1]}, 01合约尾 close={p01[-1]}')
total = sum(os.path.getsize(os.path.join(BASE, 'data', p['file'])) for p in idx['products'].values())
print('数据总量: %.1f MB' % (total / 1024 / 1024))
