# -*- coding: utf-8 -*-
"""验证 app.js 语法 + 数据链路一致性"""
import json
import os
import esprima

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

src = open(os.path.join(BASE, 'js', 'app.js'), encoding='utf-8').read()
esprima.parseScript(src)
print('app.js 语法 OK')

d = json.load(open(os.path.join(BASE, 'data', 'data.json'), encoding='utf-8'))
prods = sorted(d['products'].keys())
for p in prods:
    info = d['products'][p]
    ok = '主力' in info['contracts'] and p in d['series']
    print(f"品种 {p} ({info['name']}) 合约 {len(info['contracts'])} 个 指标 {info['metrics']} 一致性:{ok}")
    assert ok
print('数据链路 OK：品种代码与 products/series 键一致，全部包含主力合约')
