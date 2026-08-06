# -*- coding: utf-8 -*-
"""调试：列出所有 sheet 的 rels 与 chart 链接"""
import re
import zipfile

PATH = r'C:\Users\10172\OneDrive\Desktop\油脂产业整理-王一波\数据库\油脂油料数据库.xlsx'
zf = zipfile.ZipFile(PATH)
names = zf.namelist()
print('charts 文件:', [n for n in names if '/charts/' in n][:10])
print('rels 文件数:', len([n for n in names if '_rels/' in n]))
# 找 日报（国外） 对应的 sheet 文件
for n in sorted(names):
    if re.match(r'xl/worksheets/sheet\d+\.xml$', n):
        print(n)
zf.close()
