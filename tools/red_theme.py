# -*- coding: utf-8 -*-
"""图表主色改红 + 语法验证"""
import esprima

p = 'js/app.js'
content = open(p, encoding='utf-8').read()
old1 = "borderColor: '#2563eb',\n      backgroundColor: 'rgba(37, 99, 235, .08)',"
new1 = "borderColor: '#d92c2c',\n      backgroundColor: 'rgba(217, 44, 44, .07)',"
assert old1 in content
content = content.replace(old1, new1, 1)
old2 = "borderColor: '#2563eb', borderDash: [4, 4], pointRadius: 0, borderWidth: 1, yAxisID: 'y1'"
new2 = "borderColor: '#d92c2c', borderDash: [4, 4], pointRadius: 0, borderWidth: 1, yAxisID: 'y1'"
assert old2 in content
content = content.replace(old2, new2, 1)
open(p, 'w', encoding='utf-8').write(content)
print('图表主色已改红')

esprima.parseScript(open(p, encoding='utf-8').read())
print('app.js 语法 OK')
