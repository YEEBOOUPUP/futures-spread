# -*- coding: utf-8 -*-
"""测试强制代理访问东财历史接口"""
import requests

url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
params = {
    'secid': '101.ZS26Z',
    'klt': '101', 'fqt': '1', 'lmt': '10', 'end': '20500000', 'iscca': '1',
    'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64',
    'ut': 'f057cbcbce2a86e2866ab8877db1d059', 'forcect': '1',
}
proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
try:
    r = requests.get(url, params=params, proxies=proxies, timeout=20)
    j = r.json()
    if j.get('data') and j['data'].get('klines'):
        k = j['data']['klines'][-1]
        print('成功! 代码:', j['data']['code'], '名称:', j['data']['name'])
        print('最新K线:', k)
    else:
        print('返回无数据:', str(j)[:200])
except Exception as e:
    print('失败:', type(e).__name__, str(e)[:150])
