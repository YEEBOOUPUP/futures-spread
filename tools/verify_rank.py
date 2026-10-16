# -*- coding: utf-8 -*-
"""验证前端语法/id 与龙虎榜数据（多日+净持仓结构）"""
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
print('龙虎榜元素:', all(('id="%s"' % x) in html for x in
    ['rankCard', 'rankDateSel', 'rankVolBody', 'rankLongBody', 'rankShortBody', 'rankNetLongBody', 'rankNetShortBody', 'rankEmpty']))
print('app.js 函数:', all(x in js for x in ['loadRank', 'renderRankCol', 'renderNetCol', 'fmtInt']))

p = json.load(open('data/rank/P.json', encoding='utf-8'))
day = p['data'][p['dates'][0]]
print('P 龙虎榜: %d 天, 最新 %s, 合约 %s' % (len(p['dates']), p['dates'][0], day['contract']))
print('  净多前1:', day['netLong'][0]['name'], day['netLong'][0]['net'])
print('  净空前1:', day['netShort'][0]['name'], day['netShort'][0]['net'])
