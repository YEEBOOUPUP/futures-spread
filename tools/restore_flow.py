# -*- coding: utf-8 -*-
"""恢复"日度海外数据"（原国际利润流）功能到 app.js，并重命名"""
import re

TAG = 'tools/_app_flow_tag.js'
CUR = 'js/app.js'

tag = open(TAG, encoding='utf-8').read()
cur = open(CUR, encoding='utf-8').read()

# 1) state：加 profitFlow / flowIndicator
old_state = """    legA: { product: null, contract: null },
    legB: { product: null, contract: null },"""
new_state = """    legA: { product: null, contract: null },
    legB: { product: null, contract: null },
    profitFlow: null,      // data/profit_flow.json 缓存
    flowIndicator: null,   // 当前日度海外数据指标列"""
assert old_state in cur
cur = cur.replace(old_state, new_state, 1)

# 2) bindEvents：加 flowSel change
old_bind = """    $('showPricesChk').addEventListener('change', refreshResult);"""
new_bind = """    $('showPricesChk').addEventListener('change', refreshResult);
    $('flowSel').addEventListener('change', function () {
      state.flowIndicator = this.value;
      renderProfitFlow();
    });"""
assert old_bind in cur
cur = cur.replace(old_bind, new_bind, 1)

# 3) setMode：加入 flow 分支
old_setmode_start = """    var op = document.querySelector('.operator');
    if (op) op.textContent = mode === 'ratio' ? '÷' : '−';
    if (state.view === 'seasonal') initSeasonalRange();   // 切模式后重置季节性图滑块到全区间
    renderShortcuts();
    refreshResult();"""
new_setmode_flow = """    var isFlow = mode === 'flow';
    var legs = document.querySelector('.legs');
    if (legs) legs.style.display = isFlow ? 'none' : '';
    var fc = $('flowControl');
    if (fc) fc.style.display = isFlow ? '' : 'none';
    setFlowControls(isFlow);
    if (isFlow) {
      $('legHint').textContent = '日度海外数据：国际油脂油料相关价差的季节性图（每年一条线，最新年份红色加粗，点击图例可隐藏年份）';
      $('modeShortcuts').innerHTML = '';
      loadProfitFlow();
      return;
    }
    var op = document.querySelector('.operator');
    if (op) op.textContent = mode === 'ratio' ? '÷' : '−';
    if (state.view === 'seasonal') initSeasonalRange();   // 切模式后重置季节性图滑块到全区间
    renderShortcuts();
    refreshResult();"""
assert old_setmode_start in cur
cur = cur.replace(old_setmode_start, new_setmode_flow, 1)

# 4) 在 setMode 后插入 4 个 flow 函数（从 tag 提取，重命名文案）
m = re.search(r'  function setMode.*?\n  }\n', tag, re.S)
assert m, 'tag 中未找到 setMode'
# 从 tag 提取 flow 函数块：setFlowControls 到 renderProfitFlow 结束
m2 = re.search(r"  /\*\* 国际利润流模式下隐藏与品种图无关的控件（切回时恢复） \*/\n.*?\$\(['\"]chartEmpty['\"]\)\.style\.display = 'none';\n  \}\n", tag, re.S)
assert m2, 'tag 中未找到 flow 函数块'
flow_block = m2.group(0)
# 文案：国际利润流 → 日度海外数据
flow_block = flow_block.replace('国际利润流', '日度海外数据')

# 在 setMode 函数结束后的位置插入（当前文件的 setMode 之后）
anchor = "    renderShortcuts();\n    refreshResult();\n  }\n"
# 找当前 setMode 结束（第一个匹配后的下一个 \n  })
idx = cur.find(new_setmode_flow)
end_of_setmode = cur.find('\n  }\n', idx + len(new_setmode_flow))
assert end_of_setmode > 0
insert_at = end_of_setmode + len('\n  }\n')
cur = cur[:insert_at] + '\n' + flow_block + cur[insert_at:]

open(CUR, 'w', encoding='utf-8').write(cur)
print('app.js 已恢复日度海外数据功能')
print('flow 函数块行数:', flow_block.count('\n'))
