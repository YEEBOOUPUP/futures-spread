# -*- coding: utf-8 -*-
"""列出"日报（国外）"图表中引用"国际油脂油料相关价差"的全部（指标列 + 年度系列）"""
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
SHEET = '国际油脂油料相关价差'
zf = zipfile.ZipFile(PATH)
rels = zf.read('xl/worksheets/_rels/sheet5.xml.rels').decode('utf-8')
drawing = 'xl/drawings/' + re.search(r'Target="(\.\./drawings/drawing\d+\.xml)"', rels).group(1).split('/')[-1]
dx = zf.read(drawing).decode('utf-8')
drels = zf.read('xl/drawings/_rels/' + drawing.split('/')[-1] + '.rels').decode('utf-8')
chart_rels = re.findall(r'Id="([^"]*)"[^>]*Target="(\.\./charts/(chart\d+\.xml))"', drels)
anchors = re.findall(r'<xdr:from>.*?<xdr:row>(\d+)</xdr:row>.*?</xdr:from>.*?r:id="([^"]*)"', dx, re.S)
rid2row = {rid: int(r) + 1 for r, rid in anchors}

items = []
for rel_id, target, chart_no in chart_rels:
    cx = zf.read('xl/charts/' + chart_no).decode('utf-8')
    if SHEET not in cx:
        continue
    row = rid2row.get(rel_id, '?')
    # 所有 series 的 val 引用（列 + 年份行段）
    vals = re.findall(r'<c:val>.*?<c:numRef>.*?<c:f>%s!\$([A-Z]+)\$(\d+):\$[A-Z]+\$(\d+)</c:f>' % re.escape(SHEET), cx, re.S)
    cats = re.findall(r'<c:cat>.*?<c:f>[^!]*!\$[A-Z]+\$(\d+):\$[A-Z]+\$(\d+)</c:f>', cx, re.S)
    items.append((row, chart_no, vals, cats))

items.sort()
seen = set()
for row, chart_no, vals, cats in items:
    key = tuple(v[0] for v in vals)
    cols = sorted(set(v[0] for v in vals))
    years = sorted(int(v[1]) for v in vals)
    cat_rng = (cats[0] if cats else ('?', '?'))
    print('锚点R%-4d %s 列=%s 年份起行=%s cat=%s~%s series数=%d' % (row, chart_no, cols, years, cat_rng[0], cat_rng[1], len(vals)))
print('\n共 %d 个图表引用 %s' % (len(items), SHEET))
zf.close()
