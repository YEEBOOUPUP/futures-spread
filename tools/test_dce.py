# -*- coding: utf-8 -*-
"""尝试直连大商所 DCE 日行情接口（修复 akshare 失效问题）"""
import urllib.request
import urllib.parse

url = 'http://www.dce.com.cn/publicweb/quotesdata/exportDayQuotesChData.html'
form = {
    'year': '2026', 'month': '8', 'day': '6',
    'exportType': '1',
}
data = urllib.parse.urlencode(form).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://www.dce.com.cn/publicweb/quotesdata/dayQuotesCh.html',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'http://www.dce.com.cn',
}
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        print('HTTP', r.status, 'Content-Type:', r.headers.get('Content-Type'))
        print('长度:', len(body))
        # 尝试解码（可能是 gbk xls 或 json）
        try:
            txt = body.decode('gbk', errors='replace')
            print('--- GBK 解码前 600 字符 ---')
            print(txt[:600])
        except Exception as e:
            print('GBK 解码失败:', e)
except Exception as e:
    print('请求失败:', type(e).__name__, str(e)[:200])
