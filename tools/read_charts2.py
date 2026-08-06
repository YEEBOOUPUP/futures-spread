# -*- coding: utf-8 -*-
"""解析"日报（国外）"R18 起所有图表：位置(锚点行) + 标题 + series 源数据引用"""
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
zf = zipfile.ZipFile(PATH)

# 1) sheet 名 → sheet 文件编号
wb = zf.read('xl/workbook.xml').decode('utf-8')
names = re.findall(r'<sheet name="([^"]*)"[^>]*r:id="rId(\d+)"', wb)
name2file = {}
for i, (name, rid) in enumerate(names, 1):
    name2file[name] = i
print('日报（国外）sheet 文件: sheet%d.xml' % name2file['日报（国外）'])

# 2) sheet → drawing
sheet_no = name2file['日报（国外）']
rels = zf.read('xl/worksheets/_rels/sheet%d.xml.rels' % sheet_no).decode('utf-8')
m = re.search(r'Target="(\.\./drawings/drawing\d+\.xml)"', rels)
drawing = 'xl/drawings/' + m.group(1).split('/')[-1]
print('drawing:', drawing)

# 3) drawing → chart 列表 + 锚点
dx = zf.read(drawing).decode('utf-8')
drels = zf.read('xl/drawings/_rels/' + drawing.split('/')[-1].replace('.xml', '.xml.rels')).decode('utf-8')
chart_rels = re.findall(r'Id="([^"]*)"[^>]*Target="(\.\./charts/(chart\d+\.xml))"', drels)
print('charts:', [c for _, c, _ in chart_rels])

# drawing XML：每个图形两列锚（from/row）与 rId 的对应
anchors = re.findall(r'<xdr:from>.*?<xdr:row>(\d+)</xdr:row>.*?</xdr:from>.*?r:id="([^"]*)"', dx, re.S)
rid2row = {rid: int(r) + 1 for r, rid in anchors}
print('锚点行:', rid2row)


def parse_series(chart_xml):
    out = []
    for s in re.finditer(r'<c:ser>.*?</c:ser>', chart_xml, re.S):
        ser = s.group(0)
        name = None
        m = re.search(r'<c:tx>.*?<c:v>([^<]*)</c:v>', ser, re.S)
        if not m:
            m = re.search(r'<c:tx>.*?<c:f>([^<]*)</c:f>', ser, re.S)
        if m:
            name = m.group(1)
        cat = re.search(r'<c:cat>.*?<c:f>([^<]*)</c:f>', ser, re.S)
        val = re.search(r'<c:val>.*?<c:f>([^<]*)</c:f>', ser, re.S)
        out.append((name, cat.group(1) if cat else None, val.group(1) if val else None))
    return out


for rel_id, target, chart_no in chart_rels:
    cx = zf.read('xl/charts/' + chart_no).decode('utf-8')
    title = None
    mt = re.search(r'<c:tx>.*?<c:v>([^<]*)</c:v>', cx, re.S)
    if mt:
        title = mt.group(1)
    row = rid2row.get(rel_id, '?')
    series = parse_series(cx)
    print('\n图表 %s (rId=%s 锚点R%d) 标题: %s' % (chart_no, rel_id, row, title))
    for sname, cat, val in series:
        print('  series %r: cat=%s | val=%s' % (sname, cat, val))
zf.close()
