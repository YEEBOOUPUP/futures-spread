# -*- coding: utf-8 -*-
"""读取 xlsx 内部图表 XML：找出"日报（国外）"R18 起每个图表的数据引用范围"""
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
NS = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}


def local_name(tag):
    return tag.split('}')[-1] if '}' in tag else tag


def parse_title(ser):
    """series 或 chart 的标题文本"""
    m = re.search(r'<c:tx>.*?</c:tx>', ser, re.S)
    if not m:
        return None
    tx = m.group(0)
    v = re.search(r'<c:v>([^<]*)</c:v>', tx)
    ref = re.search(r'<c:f>([^<]*)</c:f>', tx)
    return v.group(1) if v else (ref.group(1) if ref else None)


def parse_series(chart_xml):
    """返回 [(series_name, cat_ref, val_ref)]"""
    out = []
    for s in re.finditer(r'<c:ser>.*?</c:ser>', chart_xml, re.S):
        ser = s.group(0)
        name = parse_title(ser)
        cat = re.search(r'<c:cat>.*?<c:numRef>.*?<c:f>([^<]*)</c:f>', ser, re.S) or \
              re.search(r'<c:cat>.*?<c:strRef>.*?<c:f>([^<]*)</c:f>', ser, re.S)
        val = re.search(r'<c:val>.*?<c:numRef>.*?<c:f>([^<]*)</c:f>', ser, re.S)
        out.append((name, cat.group(1) if cat else None, val.group(1) if val else None))
    return out


zf = zipfile.ZipFile(PATH)
# 1) workbook.xml → sheet 名 → rId
wb = zf.read('xl/workbook.xml').decode('utf-8')
sheets = re.findall(r'<sheet name="([^"]*)"[^>]*r:id="(rId\d+)"', wb)
rid2name = {rid: name for name, rid in sheets}
print('sheets:', rid2name)

# 2) 每个 sheet 的 rels → charts
for rid, name in rid2name.items():
    rels_path = 'xl/worksheets/_rels/sheet%d.xml.rels' % int(rid[3:])
    try:
        rels = zf.read(rels_path).decode('utf-8')
    except KeyError:
        continue
    chart_links = re.findall(r'Id="([^"]*)"[^>]*Target="(\.\./charts/chart\d+\.xml)"', rels)
    if not chart_links:
        continue
    print('\n=== sheet: %s ===' % name)
    for rel_id, target in chart_links:
        chart_path = 'xl/charts/' + target.split('/')[-1]
        cx = zf.read(chart_path).decode('utf-8')
        chart_title = parse_title(cx)
        series = parse_series(cx)
        print('  图表 %s (%s):' % (chart_path, chart_title))
        for sname, cat, val in series:
            print('    series: %r | cat=%s | val=%s' % (sname, cat, val))
zf.close()
