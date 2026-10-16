# -*- coding: utf-8 -*-
"""
rank_fetch.py — 采集持仓龙虎榜（新浪期货持仓排名，成交量/多单/空单前 20 名）
数据源：https://vip.stock.finance.sina.com.cn/q/view/vFutures_Positions_cjcc.php?symbol={品种}&date={交易日}
输出：data/rank/{品种}.json
  { date, contract, vol: [{rank,name,value,chg}...], long: [...], short: [...] }
用法：python collector/rank_fetch.py [日期YYYYMMDD]
"""
import io
import json
import os
import re
import sys
import urllib.request

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')
RANK_DIR = os.path.join(DATA_DIR, 'rank')
URL = 'https://vip.stock.finance.sina.com.cn/q/view/vFutures_Positions_cjcc.php?symbol={p}&date={d}'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://finance.sina.com.cn'}


def num(v):
    if v is None:
        return None
    s = str(v).replace(',', '').strip()
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def clean(v):
    return re.sub(r'\s+', '', str(v)) if v is not None else ''


def parse_tables(body):
    tables = pd.read_html(io.StringIO(body))
    out = []
    for t in tables:
        cols = [str(c) for c in t.columns]
        if '会员简称' not in cols:
            continue
        # 找到 名次/会员简称/量/增减 四列
        t.columns = [clean(c) for c in t.columns]
        rows = []
        for _, r in t.iterrows():
            rows.append({
                'rank': num(r.get('名次')),
                'name': clean(r.get('会员简称')),
                'value': num(r.get('成交量', r.get('多单持仓', r.get('空单持仓')))),
                'chg': num(r.get('比上交易增减')),
            })
        rows = [r for r in rows if r['rank'] is not None and r['name']]
        out.append(rows)
    # 三表顺序：成交量 / 多单 / 空单
    return out if len(out) >= 3 else None


def main():
    os.makedirs(RANK_DIR, exist_ok=True)
    index = json.load(open(INDEX_FILE, encoding='utf-8'))
    products = sorted([k for k, v in index['products'].items() if not v.get('foreign')])
    # 日期：参数或最近交易日（P 的最后日期）
    date = sys.argv[1] if len(sys.argv) > 1 else None
    if not date:
        p = json.load(open(os.path.join(DATA_DIR, 'P.json'), encoding='utf-8'))
        date = p['dates'][-1].replace('-', '')
    ok = 0
    for i, prod in enumerate(products, 1):
        try:
            req = urllib.request.Request(URL.format(p=prod, d=date), headers=HEADERS)
            body = urllib.request.urlopen(req, timeout=30).read().decode('gbk', errors='ignore')
            tables = parse_tables(body)
            if not tables:
                continue
            m = re.search(r'%s\d{3,4}' % re.escape(prod), body, re.IGNORECASE)
            contract = m.group(0).upper() if m else prod
            out = {'date': date, 'contract': contract,
                   'vol': tables[0], 'long': tables[1], 'short': tables[2]}
            with open(os.path.join(RANK_DIR, prod + '.json'), 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
            ok += 1
        except Exception as e:
            print('[%s] 失败: %s' % (prod, str(e)[:80]))
    print('龙虎榜采集完成：%d/%d 品种成功（%s）' % (ok, len(products), date))


if __name__ == '__main__':
    main()
