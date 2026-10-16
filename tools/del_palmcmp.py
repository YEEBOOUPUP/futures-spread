# -*- coding: utf-8 -*-
"""删除"马棕P月差对比"模式（按钮 + 控件）"""
p = 'index.html'
html = open(p, encoding='utf-8').read()

# 1) 模式按钮
btn = '      <button class="mode-btn" data-mode="palmcmp">马棕P月差对比</button>\n'
assert btn in html, '按钮未找到'
html = html.replace(btn, '', 1)

# 2) palmCmpControl 控件块
import re
m = re.search(r'    <div class="flow-control" id="palmCmpControl".*?</div>\n', html, re.S)
assert m, 'palmCmpControl 未找到'
html = html.replace(m.group(0), '', 1)

open(p, 'w', encoding='utf-8').write(html)
print('已删除马棕P月差对比')
print('残留 palmcmp:', html.count('palmcmp'), '| palmCmp:', html.count('palmCmp'))
print('剩余模式按钮:')
for mm in re.finditer(r'data-mode="(\w+)">([^<]*)<', html):
    print('  ', mm.group(1), mm.group(2))
