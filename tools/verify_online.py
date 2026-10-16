# -*- coding: utf-8 -*-
"""线上验证：龙虎榜视图 + bat 修复 + 数据"""
import json
import time
import urllib.request

base = 'https://YEEBOOUPUP.github.io/futures-spread/'
v = '?v=' + time.time().hex()


def get(path):
    return urllib.request.urlopen(base + path + v, timeout=30).read().decode('utf-8')


html = get('index.html')
app = get('js/app.js')
rank = json.loads(get('data/rank/P.json'))

print('线上 龙虎榜视图按钮:', 'data-view="rank"' in html)
print('线上 rankEmpty 提示:', 'rankEmpty' in html)
print('线上 rank 视图逻辑:', "state.view === 'rank'" in app)
print('线上 P 龙虎榜:', rank['contract'], '| 多单第1', rank['long'][0]['name'], rank['long'][0]['value'])
print('线上 红色主题:', '--accent: #d92c2c' in get('css/style.css'))
print('线上 Pico CDN:', 'pico.red.min.css' in html)
