# -*- coding: utf-8 -*-
"""端到端一致性检查：index.html id 与 app.js 引用、JS 文件存在性"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

html = open(os.path.join(BASE, 'index.html'), encoding='utf-8').read()
js = open(os.path.join(BASE, 'js', 'app.js'), encoding='utf-8').read()

ids_in_js = set(re.findall(r"\$\('([\w]+)'\)", js))
ids_in_html = set(re.findall(r'id="([\w]+)"', html))
missing = ids_in_js - ids_in_html
print('app.js 引用的 id 数:', len(ids_in_js))
print('index.html 定义的 id 数:', len(ids_in_html))
print('缺失:', sorted(missing) if missing else '无，全部匹配 OK')

for f in ['js/parser.js', 'js/data.js', 'js/app.js', 'css/style.css', 'data/data.json']:
    p = os.path.join(BASE, f)
    print(f, '存在' if os.path.exists(p) else '缺失!')
