# -*- coding: utf-8 -*-
"""DCE 反爬处理：先 GET 拿 Cookie 再 POST"""
import http.cookiejar
import urllib.request
import urllib.parse

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. 先访问行情页拿 cookie
try:
    opener.open(urllib.request.Request(
        'http://www.dce.com.cn/publicweb/quotesdata/dayQuotesCh.html',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}), timeout=20)
    print('GET 行情页成功, cookies:', [c.name for c in cj])
except Exception as e:
    print('GET 行情页失败:', type(e).__name__, str(e)[:100])

# 2. POST 拉数据
url = 'http://www.dce.com.cn/publicweb/quotesdata/exportDayQuotesChData.html'
form = {'year': '2026', 'month': '8', 'day': '6', 'exportType': '1'}
data = urllib.parse.urlencode(form).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://www.dce.com.cn/publicweb/quotesdata/dayQuotesCh.html',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
}
try:
    r = opener.open(urllib.request.Request(url, data=data, headers=headers), timeout=30)
    body = r.read()
    print('HTTP', r.status, '长度:', len(body), 'CT:', r.headers.get('Content-Type'))
    txt = body.decode('gbk', errors='replace')
    print(txt[:500])
except Exception as e:
    print('POST 失败:', type(e).__name__, str(e)[:200])
