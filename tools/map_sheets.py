# -*- coding: utf-8 -*-
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
zf = zipfile.ZipFile(PATH)
rels = zf.read('xl/_rels/workbook.xml.rels').decode('utf-8')
m = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]*)"', rels))
wb = zf.read('xl/workbook.xml').decode('utf-8')
for mm in re.finditer(r'<sheet name="([^"]*)"[^>]*r:id="(rId\d+)"', wb):
    name, rid = mm.group(1), mm.group(2)
    print('%s -> %s' % (name, m.get(rid)))
zf.close()
