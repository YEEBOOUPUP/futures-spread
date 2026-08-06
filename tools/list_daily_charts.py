# -*- coding: utf-8 -*-
"""列出"日报（国外）"（sheet5→drawing6）全部图表：锚点行 + 数据列引用"""
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
zf = zipfile.ZipFile(PATH)
rels = zf.read('xl/worksheets/_rels/sheet5.xml.rels').decode('utf-8')
m = re.search(r'Target="(\.\./drawings/drawing\d+\.xml)"', rels)
drawing = 'xl/drawings/' + m.group(1).split('/')[-1]
print('drawing:', drawing)
dx = zf.read(drawing).decode('utf-8')
drels = zf.read('xl/drawings/_rels/' + drawing.split('/')[-1] + '.rels').decode('utf-8')
chart_rels = re.findall(r'Id="([^"]*)"[^>]*Target="(\.\./charts/(chart\d+\.xml))"', drels)
anchors = re.findall(r'<xdr:from>.*?<xdr:row>(\d+)</xdr:row>.*?</xdr:from>.*?r:id="([^"]*)"', dx, re.S)
rid2row = {rid: int(r) + 1 for r, rid in anchors}
items = []
for rel_id, target, chart_no in chart_rels:
    cx = zf.read('xl/charts/' + chart_no).decode('utf-8')
    val = re.search(r'<c:val>.*?<c:f>([^<]*)</c:f>', cx, re.S)
    val_ref = val.group(1) if val else None
    row = rid2row.get(rel_id, '?')
    items.append((row, chart_no, val_ref))
items.sort()
for row, chart_no, val_ref in items:
    print('锚点R%-4d %s val=%s' % (row, chart_no, val_ref))
print('图表总数:', len(items))
zf.close()
