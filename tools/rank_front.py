# -*- coding: utf-8 -*-
"""龙虎榜前端改造：上移到图表工具下方 + 日期下拉 + 净多/净空榜单"""
import re

p = 'index.html'
html = open(p, encoding='utf-8').read()

# 1) 删除现有 rankCard 与 rankEmpty（保持顺序整洁，稍后统一插入）
start = html.find('    <div class="rank-card" id="rankCard"')
end = html.find('</div>\n', html.find('<div class="rank-empty" id="rankEmpty"'))
# 更稳妥：正则删除两个块
html = re.sub(r'    <div class="rank-card" id="rankCard".*?\n    </div>\n', '', html, count=1, flags=re.S)
html = re.sub(r'    <div class="rank-empty" id="rankEmpty".*?\n    </div>\n', '', html, count=1, flags=re.S)

# 2) 新版 rankCard（含日期下拉 + 5 个榜单）
rank_new = '''    <div class="rank-card" id="rankCard" style="display:none">
      <div class="rank-head">
        <span class="rank-title">持仓龙虎榜</span>
        <label class="rank-date-label">日期
          <select id="rankDateSel" class="rank-date-sel"></select>
        </label>
        <span class="rank-meta" id="rankMeta">—</span>
        <span class="rank-note">前 20 名会员（新浪）</span>
      </div>
      <div class="rank-tables">
        <div class="rank-col">
          <div class="rank-col-title">成交量排名</div>
          <table class="rank-table"><thead><tr><th>名次</th><th>会员</th><th>成交量</th><th>增减</th></tr></thead><tbody id="rankVolBody"></tbody></table>
        </div>
        <div class="rank-col">
          <div class="rank-col-title">多单排名</div>
          <table class="rank-table"><thead><tr><th>名次</th><th>会员</th><th>多单持仓</th><th>增减</th></tr></thead><tbody id="rankLongBody"></tbody></table>
        </div>
        <div class="rank-col">
          <div class="rank-col-title">空单排名</div>
          <table class="rank-table"><thead><tr><th>名次</th><th>会员</th><th>空单持仓</th><th>增减</th></tr></thead><tbody id="rankShortBody"></tbody></table>
        </div>
        <div class="rank-col">
          <div class="rank-col-title">净多排名</div>
          <table class="rank-table"><thead><tr><th>名次</th><th>会员</th><th>多单</th><th>空单</th><th>净多</th></tr></thead><tbody id="rankNetLongBody"></tbody></table>
        </div>
        <div class="rank-col">
          <div class="rank-col-title">净空排名</div>
          <table class="rank-table"><thead><tr><th>名次</th><th>会员</th><th>多单</th><th>空单</th><th>净空</th></tr></thead><tbody id="rankNetShortBody"></tbody></table>
        </div>
      </div>
    </div>
    <div class="rank-empty" id="rankEmpty" style="display:none">
      该品种暂无持仓龙虎榜数据（外盘品种无龙虎榜）
    </div>
'''

# 3) 插入到 chart-tools 之后、summaryGrid 之前（即"上方"）
anchor = '    <div class="summary-grid" id="summaryGrid"></div>'
assert anchor in html, 'summaryGrid 未找到'
html = html.replace(anchor, rank_new + '\n' + anchor, 1)

open(p, 'w', encoding='utf-8').write(html)
print('index.html 龙虎榜已上移 + 日期下拉 + 5 榜单')
for k in ['rankCard', 'rankDateSel', 'rankNetLongBody', 'rankNetShortBody', 'rankEmpty']:
    print(' ', k, ':', html.count('id="%s"' % k))
