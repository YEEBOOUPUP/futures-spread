# -*- coding: utf-8 -*-
"""解析"日报（国外）"图表（用 sheetId 定位文件），输出锚点行+标题+数据引用"""
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
zf = zipfile.ZipFile(PATH)
wb = zf.read('xl/workbook.xml').decode('utf-8')
# name -> sheetId（文件编号）
sheet_map = {}
for m in re.finditer(r'<sheet name="([^"]*)"[^>]*sheetId="(\d+)"[^>]*r:id="([^"]*)"', wb):
    name, sid, rid = m.group(1), int(m.group(2)), m.group(3)
    sheet_map[name] = (sid, rid)
for nm in ['日报（国外）', '国外油脂利润流']:
    print(nm, '->', sheet_map.get(nm))

TARGET = '日报（国外）'
sid, _ = sheet_map[TARGET]
rels = zf.read('xl/worksheets/_rels/sheet%d.xml.rels' % sid).decode('utf-8')
m = re.search(r'Target="(\.\./drawings/drawing\d+\.xml)"', rels)
drawing = 'xl/drawings/' + m.group(1).split('/')[-1]
print('drawing:', drawing)
dx = zf.read(drawing).decode('utf-8')
drels = zf.read('xl/drawings/_rels/' + drawing.split('/')[-1] + '.rels').decode('utf-8')
chart_rels = re.findall(r'Id="([^"]*)"[^>]*Target="(\.\./charts/(chart\d+\.xml))"', drels)
anchors = re.findall(r'<xdr:from>.*?<xdr:row>(\d+)</xdr:row>.*?</xdr:from>.*?r:id="([^"]*)"', dx, re.S)
rid2row = {rid: int(r) + 1 for r, rid in anchors}


def parse_series(cx):
    out = []
    for s in re.finditer(r'<c:ser>.*?</c:ser>', cx, re.S):
        ser = s.group(0)
        name = None
        mm = re.search(r'<c:tx>.*?<c:v>([^<]*)</c:v>', ser, re.S) or re.search(r'<c:tx>.*?<c:f>([^<]*)</c:f>', ser, re.S)
        if mm:
            name = mm.group(1)
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
    for sname, cat, val in series[:8]:
        print('  series %r: cat=%s | val=%s' % (sname, cat, val))
    if len(series) > 8:
        print('  ... 共 %d 个 series' % len(series))
zf.close()
