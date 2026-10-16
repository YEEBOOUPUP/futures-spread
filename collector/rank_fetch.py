# -*- coding: utf-8 -*-
"""
rank_fetch.py — 采集持仓龙虎榜（新浪期货持仓排名）
输出：data/rank/{品种}.json
  { dates: [YYYYMMDD 降序], data: { YYYYMMDD: { contract, vol, long, short, netLong, netShort } } }
  每个榜 = [{rank,name,value,chg}...]（净多/净空榜为 {rank,name,long,short,net}）
用法：
  python collector/rank_fetch.py            # 最近 20 个交易日
  python collector/rank_fetch.py 20261016   # 指定单日
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
KEEP_DAYS = 20          # 每个品种保留最近交易日数
HISTORY_DAYS = 20       # 默认采集历史天数


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
        t.columns = [clean(c) for c in t.columns]
        if '会员简称' not in list(t.columns):
            continue
        rows = []
        for _, r in t.iterrows():
            rows.append({
                'rank': num(r.get('名次')),
                'name': clean(r.get('会员简称')),
                'value': num(r.get('成交量', r.get('多单持仓', r.get('空单持仓')))),
                'chg': num(r.get('比上交易增减')),
            })
        rows = [x for x in rows if x['rank'] is not None and x['name']]
        out.append(rows)
    return out if len(out) >= 3 else None


def calc_net(long_rows, short_rows):
    """按会员合并多空榜 → 净持仓榜（净多降序 / 净空升序）"""
    m = {}
    for r in long_rows:
        m.setdefault(r['name'], {'long': 0, 'short': 0})['long'] += r['value'] or 0
    for r in short_rows:
        m.setdefault(r['name'], {'long': 0, 'short': 0})['short'] += r['value'] or 0
    rows = []
    for name, v in m.items():
        net = v['long'] - v['short']
        if net != 0:
            rows.append({'name': name, 'long': v['long'], 'short': v['short'], 'net': net})
    net_long = sorted([x for x in rows if x['net'] > 0], key=lambda x: -x['net'])[:20]
    net_short = sorted([x for x in rows if x['net'] < 0], key=lambda x: x['net'])[:20]
    for i, x in enumerate(net_long, 1):
        x['rank'] = i
    for i, x in enumerate(net_short, 1):
        x['rank'] = i
    return net_long, net_short


def fetch_one(prod, date):
    req = urllib.request.Request(URL.format(p=prod, d=date), headers=HEADERS)
    body = urllib.request.urlopen(req, timeout=30).read().decode('gbk', errors='ignore')
    tables = parse_tables(body)
    if not tables:
        return None
    m = re.search(r'%s\d{3,4}' % re.escape(prod), body, re.IGNORECASE)
    contract = m.group(0).upper() if m else prod
    net_long, net_short = calc_net(tables[1], tables[2])
    return {'contract': contract, 'vol': tables[0], 'long': tables[1], 'short': tables[2],
            'netLong': net_long, 'netShort': net_short}


def main():
    os.makedirs(RANK_DIR, exist_ok=True)
    index = json.load(open(INDEX_FILE, encoding='utf-8'))
    products = sorted([k for k, v in index['products'].items() if not v.get('foreign')])
    # 交易日列表
    p = json.load(open(os.path.join(DATA_DIR, 'P.json'), encoding='utf-8'))
    trade_dates = [d.replace('-', '') for d in p['dates']]
    if len(sys.argv) > 1:
        dates = [sys.argv[1]]
    else:
        dates = trade_dates[-HISTORY_DAYS:]

    for prod in products:
        fpath = os.path.join(RANK_DIR, prod + '.json')
        store = {'dates': [], 'data': {}}
        if os.path.exists(fpath):
            try:
                old = json.load(open(fpath, encoding='utf-8'))
                if isinstance(old.get('data'), dict):
                    store = old
                elif old.get('date'):                     # 兼容旧单日结构
                    store = {'dates': [old['date']], 'data': {old['date']: old}}
            except Exception:
                pass
        for d in dates:
            if d in store['data']:
                continue
            try:
                one = fetch_one(prod, d)
                if one:
                    store['data'][d] = one
                    if d not in store['dates']:
                        store['dates'].append(d)
            except Exception as e:
                print('[%s %s] 失败: %s' % (prod, d, str(e)[:60]))
        store['dates'] = sorted(store['dates'], reverse=True)[:KEEP_DAYS]
        keep = set(store['dates'])
        store['data'] = {k: v for k, v in store['data'].items() if k in keep}
        if store['dates']:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(store, f, ensure_ascii=False, separators=(',', ':'))
    ok = sum(1 for prod in products if os.path.exists(os.path.join(RANK_DIR, prod + '.json')))
    print('龙虎榜采集完成：%d 品种，日期 %s ~ %s' % (ok, dates[0], dates[-1]))


if __name__ == '__main__':
    main()
