# -*- coding: utf-8 -*-
"""验证前端语法/id 与龙虎榜数据"""
import json
import os
import re

import esprima

esprima.parseScript(open('js/app.js', encoding='utf-8').read())
print('app.js 语法 OK')

html = open('index.html', encoding='utf-8').read()
js = open('js/app.js', encoding='utf-8').read()
ids = set(re.findall(r"\$\('([\w]+)'\)", js))
missing = ids - set(re.findall(r'id="([\w]+)"', html))
print('缺失 id:', missing if missing else '无 ✓')
print('龙虎榜区块:', all(x in html for x in ['rankCard', 'rankVolBody', 'rankLongBody', 'rankShortBody', 'hotPicks']))
print('app.js 龙虎榜函数:', all(x in js for x in ['loadRank', 'renderRankCol', 'fmtInt']))

files = os.listdir('data/rank')
print('龙虎榜数据文件:', len(files), '个')
p = json.load(open('data/rank/P.json', encoding='utf-8'))
print('P 合约:', p['contract'], '| 多单前1:', p['long'][0]['name'], p['long'][0]['value'])
