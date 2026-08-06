# -*- coding: utf-8 -*-
"""检查 openctp prices/instruments 中是否含外盘（ExchangeID 分布）"""
import json
import urllib.request


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


# prices 全量统计
p = fetch('http://dict.openctp.cn/prices?types=futures')
if p.get('rsp_code') == 0:
    from collections import Counter
    exch = Counter()
    for it in p['data']:
        exch[str(it.get('ExchangeID', '?'))] += 1
    print('prices 合约数:', len(p['data']))
    print('交易所分布:', dict(exch))
    # 找外盘样例
    for it in p['data']:
        if str(it.get('ExchangeID', '')) in ('CBOT', 'NYMEX', 'COMEX', 'CME'):
            print('外盘样例:', {k: it.get(k) for k in ('ExchangeID', 'InstrumentID', 'InstrumentName', 'ProductID', 'ClosePrice', 'LastPrice')})
            break
else:
    print('prices 失败:', p)
