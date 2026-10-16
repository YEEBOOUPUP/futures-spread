# -*- coding: utf-8 -*-
"""修复视图按钮误触发 setMode（选择器限定 .mode-switch）"""
import esprima

p = 'js/app.js'
js = open(p, encoding='utf-8').read()

# 1) 事件绑定限定模式按钮
old1 = """    document.querySelectorAll('.mode-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { setMode(btn.dataset.mode); });
    });"""
new1 = """    document.querySelectorAll('.mode-switch .mode-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { setMode(btn.dataset.mode); });
    });"""
assert old1 in js, '绑定未找到'
js = js.replace(old1, new1, 1)

# 2) setMode 里的 active 切换限定模式按钮
old2 = """  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll('.mode-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.mode === mode);
    });"""
new2 = """  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll('.mode-switch .mode-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.mode === mode);
    });"""
assert old2 in js, 'setMode 未找到'
js = js.replace(old2, new2, 1)

open(p, 'w', encoding='utf-8').write(js)
esprima.parseScript(js)
print('视图按钮 bug 已修复，语法 OK')
