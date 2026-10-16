# -*- coding: utf-8 -*-
"""把 rankCard 从明细表后移到图表区后，并加 rankEmpty 提示"""
p = 'index.html'
html = open(p, encoding='utf-8').read()

# 1) 取出原 rankCard 块（table-wrap 后）
start = html.find('    <div class="rank-card" id="rankCard"')
end = html.find('  </section>', start)
assert start > 0 and end > start, 'rankCard 未找到'
rank_block = html[start:end].rstrip() + '\n'
html = html[:start] + html[end:]

# 2) 插入到 chart-wrap 之后
anchor = '''    <div class="chart-wrap">
      <canvas id="spreadChart"></canvas>
      <div class="chart-empty" id="chartEmpty">请选择品种与合约</div>
    </div>
'''
assert anchor in html
empty_tip = '''    <div class="rank-empty" id="rankEmpty" style="display:none">
      该品种暂无持仓龙虎榜数据（外盘品种无龙虎榜）
    </div>
'''
html = html.replace(anchor, anchor + '\n' + rank_block + empty_tip, 1)

open(p, 'w', encoding='utf-8').write(html)
print('rankCard 已移至 chart-wrap 后 + 加 rankEmpty')
print('检查:', html.count('id="rankCard"'), '个 rankCard;', html.count('id="rankEmpty"'), '个 rankEmpty')
