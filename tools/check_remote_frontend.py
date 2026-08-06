# -*- coding: utf-8 -*-
"""检查线上前端文件与本地是否一致"""
import time
import urllib.request

BASE = 'https://YEEBOOUPUP.github.io/futures-spread/'


def fetch(p):
    return urllib.request.urlopen(BASE + p + '?v=' + time.time().hex(), timeout=30).read().decode('utf-8')


for p in ['index.html', 'js/app.js', 'js/data.js']:
    remote = fetch(p)
    local = open(p.replace('js/', 'js/'), encoding='utf-8').read() if p != 'index.html' else open('index.html', encoding='utf-8').read()
    same = remote == local
    print(p, '线上', len(remote), '字节 vs 本地', len(local), '字节 ->', '一致' if same else '不一致')

# 线上 app.js 关键特征
app = fetch('js/app.js')
print('\n线上 app.js:')
print('  有 createProductPicker:', 'createProductPicker' in app)
print('  有 legAProduct 残留:', "$('legAProduct')" in app)
print('  有 initSelector:', 'initSelector' in app)
html = fetch('index.html')
print('线上 index.html:')
print('  有 legAProductInput:', 'legAProductInput' in html)
print('  有 legAProductList:', 'legAProductList' in html)
