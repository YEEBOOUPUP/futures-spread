# -*- coding: utf-8 -*-
"""线上验证：龙虎榜升级（上移/日期/净榜）+ 视图 bug 修复"""
import json
import time
import urllib.request

base = 'https://YEEBOOUPUP.github.io/futures-spread/'
v = '?v=' + time.time().hex()


def get(path):
    return urllib.request.urlopen(base + path + v, timeout=30).read().decode('utf-8')


html = get('index.html')
app = get('js/app.js')
print('龙虎榜视图按钮:', 'data-view="rank"' in html)
print('日期下拉:', 'rankDateSel' in html)
print('净多/净空榜元素:', 'rankNetLongBody' in html and 'rankNetShortBody' in html)
print('龙虎榜在汇总卡之前(上移):', html.find('rankCard') < html.find('summaryGrid'))
print('视图bug修复(限定.mode-switch):', "querySelectorAll('.mode-switch .mode-btn')" in app)
print('净榜渲染函数:', 'renderNetCol' in app)

rank = json.loads(get('data/rank/P.json'))
day = rank['data'][rank['dates'][0]]
print('线上 P 龙虎榜: %d 天, 最新 %s, 合约 %s' % (len(rank['dates']), rank['dates'][0], day['contract']))
print('  净多前1:', day['netLong'][0]['name'], day['netLong'][0]['net'])
print('  净空前1:', day['netShort'][0]['name'], day['netShort'][0]['net'])
print('  成交量前1:', day['vol'][0]['name'], day['vol'][0]['value'])
