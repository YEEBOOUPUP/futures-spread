# -*- coding: utf-8 -*-
"""检查外盘品种构成，清理新浪 F_ 中被东财覆盖的重复品种"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(BASE, 'data', 'index.json')
idx = json.load(open(INDEX, encoding='utf-8'))

foreign = {c: p for c, p in idx['products'].items() if p.get('foreign')}
print('外盘品种总数:', len(foreign))

# 东财品种（有月份合约）vs 新浪（仅主力）
em = {c: p for c, p in foreign.items() if len(p['contracts']) > 1}
sina = {c: p for c, p in foreign.items() if len(p['contracts']) == 1}
print('东财月度品种:', len(em))
print('新浪连续品种:', len(sina))

# 新浪 → 东财对应关系（删除新浪重复）
SINA_REMOVE = {
    'F_ZSD': 'F_ZS', 'F_BO': 'F_ZL', 'F_SM': 'F_ZM', 'F_W': 'F_ZW', 'F_C': 'F_ZC',
    'F_CT': 'F_CT', 'F_FCPO': 'F_MPM', 'F_CL': 'F_CL', 'F_GC': 'F_GC',
    'F_HG': 'F_HG', 'F_SI': 'F_SI', 'F_NG': 'F_NG', 'F_RSS3': 'F_RT',
}
removed = []
for s, em_code in SINA_REMOVE.items():
    if s in idx['products']:
        del idx['products'][s]
        removed.append(s)
        # 删除数据文件
        fp = os.path.join(BASE, 'data', s + '.json')
        if os.path.exists(fp):
            os.remove(fp)

json.dump(idx, open(INDEX, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('删除新浪重复品种:', removed)

# 最终外盘清单
foreign2 = {c: p for c, p in idx['products'].items() if p.get('foreign')}
print('\n=== 最终外盘品种（%d 个）===' % len(foreign2))
for c in sorted(foreign2):
    p = foreign2[c]
    print(f'{c}\t{p["name"]}\t合约数={len(p["contracts"])}')
print('\n总品种数:', len(idx['products']))
