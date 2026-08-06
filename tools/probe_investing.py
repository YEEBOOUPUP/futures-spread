# -*- coding: utf-8 -*-
"""探索英为财情页面结构：pair_id、月份合约、历史数据接口"""
import re
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
PROXIES = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}

url = 'https://cn.investing.com/commodities/us-soybeans'
try:
    r = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=30)
    print('HTTP', r.status_code, '长度', len(r.text))
    html = r.text
    # 找 pair_id
    for pat in [r'pairId["\']?\s*[:=]\s*["\']?(\d+)', r'"pairId":\s*(\d+)', r'pair_id["\']?\s*[:=]\s*["\']?(\d+)']:
        m = re.findall(pat, html)
        if m:
            print('pairId 候选:', m[:5])
            break
    # 找月份合约链接（期货到期月份）
    months = re.findall(r'href="(/commodities/[^"]*(?:c\d+|futures)[^"]*)"[^>]*>([^<]{2,20})<', html)
    print('月份/合约链接样本:', months[:10])
    # 找 API 端点
    apis = re.findall(r'https?://api\.investing\.com[^"\']*', html)
    print('API 引用:', apis[:5])
    # 找期货到期月份数据（页面上"期货"表格）
    fut = re.findall(r'(20\d{2})\s*(?:年)?\s*(\d{1,2})月?', html)
    print('年份月份出现:', fut[:10])
except Exception as e:
    print('失败:', type(e).__name__, str(e)[:150])
