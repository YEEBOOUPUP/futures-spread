# -*- coding: utf-8 -*-
"""
rank_fetch.py — 采集持仓龙虎榜（新浪期货持仓排名）

数据源：新浪期货「成交持仓」页
  https://vip.stock.finance.sina.com.cn/q/view/vFutures_Positions_cjcc.php

  ⚠ 该页必须按【合约】查询：t_breed=合约代码（如 P2701）、t_date=YYYY-MM-DD。
     - 传品种代码（如 P）只会返回一行"合计"，没有前 20 名榜单；
     - 用错误的参数名（symbol=/date=）会静默回退到默认品种的缓存页，
       导致所有品种、所有日期拿到同一份数据。
  因此本脚本先用 openctp 行情快照选出每个品种的【主力合约】（持仓量最大），
  再逐日抓该合约的成交量 / 多单持仓 / 空单持仓三个前 20 名榜单。

输出：data/rank/{品种}.json
  { "dates": ["YYYYMMDD", ... 降序],
    "data": { "YYYYMMDD": {
        "contract": "P2701",
        "vol":   [{"rank":1,"name":"东证期货","value":138854,"chg":-27643}, ...],
        "long":  [...], "short": [...],
        "netLong":  [{"rank":1,"name":"...","long":..,"short":..,"net":..}, ...],
        "netShort": [...] } } }

用法：
  python collector/rank_fetch.py            # 最近 20 个交易日（默认）
  python collector/rank_fetch.py 20261016   # 指定单日
  python collector/rank_fetch.py --days 5   # 自定义天数
"""
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html import unescape

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')
RANK_DIR = os.path.join(DATA_DIR, 'rank')

POS_URL = 'https://vip.stock.finance.sina.com.cn/q/view/vFutures_Positions_cjcc.php'
PRICES_URL = 'http://dict.openctp.cn/prices?types=futures'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://finance.sina.com.cn',
}
KEEP_DAYS = 20          # 每个品种保留最近交易日数
HISTORY_DAYS = 20       # 默认采集历史天数
MIN_ROWS = 10           # 榜单少于该行数视为无效（品种页/空页）
WORKERS = 3             # 并发抓取的品种数
DELAY = 0.2             # 同一品种相邻请求间隔（秒）


# ---------------------------------------------------------------- 工具

def fetch_text(url, encoding='gbk', tries=3, timeout=30):
    """带重试的下载 + 解码"""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode(encoding, errors='ignore')
        except Exception as e:                      # noqa: BLE001
            last = e
            if i < tries - 1:
                time.sleep(1.0 + i)
    raise last


def fetch_json(url, timeout=60):
    return json.loads(fetch_text(url, encoding='utf-8', timeout=timeout))


def num(v):
    if v is None:
        return None
    s = str(v).replace(',', '').replace('，', '').strip()
    if not s or not re.match(r'^[-+]?\d+(\.\d+)?$', s):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def strip_tags(html):
    return unescape(re.sub(r'<[^>]+>', '', html or '')).replace('\xa0', ' ').strip()


# ---------------------------------------------------------------- 解析

def parse_rank_tables(body):
    """从页面取出 3 个排行榜：[成交量榜, 多单持仓榜, 空单持仓榜]"""
    out = []
    for tab in re.findall(r'<table[^>]*class="listT".*?</table>', body, re.S):
        if '会员简称' not in tab:
            continue
        rows = []
        for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tab, re.S):
            tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
            if len(tds) < 4:
                continue
            rows.append({
                'rank': num(strip_tags(tds[0])),
                'name': strip_tags(tds[1]),
                'value': num(strip_tags(tds[2])),
                'chg': num(strip_tags(tds[3])),
            })
        rows = [x for x in rows if x['rank'] is not None and x['name']]
        out.append(rows)
    return out if len(out) >= 3 else None


def calc_net(long_rows, short_rows):
    """按会员合并多空榜 → 净多榜（净多降序）/ 净空榜（净空升序）"""
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


# ---------------------------------------------------------------- 主力合约

def to_sina_symbol(inst):
    """openctp 合约代码 → 新浪合约代码

    郑商所（CZCE）在 openctp 里用 3 位月份（OI701 = 2027-01），
    新浪/其他交易所都用 4 位（OI2701），这里统一补足。
    如 'OI701' → 'OI2701'，'RM611' → 'RM2611'
    """
    m = re.match(r'^([A-Z]+)(\d{3,4})$', inst)
    if not m:
        return inst
    code, d = m.group(1), m.group(2)
    if len(d) == 3:
        year = (datetime.now().year // 10) * 10 + int(d[0])
        if year < datetime.now().year - 1:
            year += 10
        d = '%02d%s' % (year % 100, d[1:])
    return code + d


def pick_main_contracts():
    """openctp 行情快照 → {品种代码: 主力合约}（同品种持仓量最大者）"""
    data = fetch_json(PRICES_URL)
    if data.get('rsp_code') != 0:
        raise RuntimeError('openctp prices 接口失败: %s' % data.get('rsp_message'))
    best = {}   # code -> (open_interest, sina_symbol)
    for it in data.get('data', []):
        if str(it.get('ProductClass')) != '1':
            continue
        code = str(it.get('ProductID') or '').upper()
        inst = to_sina_symbol(str(it.get('InstrumentID') or '').upper())
        oi = it.get('OpenInterest') or 0
        if not code or not inst:
            continue
        if code not in best or oi > best[code][0]:
            best[code] = (oi, inst)
    return {k: v[1] for k, v in best.items()}


def fetch_one(inst, date8):
    """抓某合约某日的龙虎榜；无效（空/合计页）返回 None"""
    ds = '%s-%s-%s' % (date8[:4], date8[4:6], date8[6:8])
    body = fetch_text('%s?t_breed=%s&t_date=%s' % (POS_URL, inst, ds))
    tables = parse_rank_tables(body)
    if not tables:
        return None
    vol, long_, short = tables
    if len(long_) < MIN_ROWS and len(short) < MIN_ROWS:
        return None                      # 品种"合计"页只有 1 行
    net_long, net_short = calc_net(long_, short)
    return {
        'contract': inst,
        'vol': vol,
        'long': long_,
        'short': short,
        'netLong': net_long,
        'netShort': net_short,
    }


# ---------------------------------------------------------------- 主流程

def main():
    os.makedirs(RANK_DIR, exist_ok=True)
    index = json.load(open(INDEX_FILE, encoding='utf-8'))
    products = sorted(k for k, v in index['products'].items() if not v.get('foreign'))

    p = json.load(open(os.path.join(DATA_DIR, 'P.json'), encoding='utf-8'))
    trade_dates = [d.replace('-', '') for d in p['dates']]

    args = sys.argv[1:]
    days = HISTORY_DAYS
    if '--days' in args:
        try:
            days = int(args[args.index('--days') + 1])
        except (IndexError, ValueError):
            sys.exit('--days 需要整数参数')
    workers = WORKERS
    if '--workers' in args:
        try:
            workers = max(1, int(args[args.index('--workers') + 1]))
        except (IndexError, ValueError):
            sys.exit('--workers 需要整数参数')
    single = [a for a in args if re.match(r'^\d{8}$', a)]
    dates = single if single else trade_dates[-days:]
    if not dates:
        sys.exit('没有可用的交易日（data/P.json 为空？）')

    print('主力合约识别中（openctp）...')
    main_c = pick_main_contracts()
    missing = [c for c in products if c not in main_c]
    if missing:
        print('  无行情、跳过的品种：%s' % ','.join(missing))

    def work(prod):
        """抓一个品种的缺失日期，写回 data/rank/{品种}.json"""
        inst = main_c.get(prod)
        if not inst:
            return (prod, None, 0, 0, [])
        fpath = os.path.join(RANK_DIR, prod + '.json')
        store = {'dates': [], 'data': {}}
        if os.path.exists(fpath):
            try:
                old = json.load(open(fpath, encoding='utf-8'))
                if isinstance(old.get('data'), dict):
                    store = old
                elif old.get('date'):                       # 兼容旧单日结构
                    store = {'dates': [old['date']], 'data': {old['date']: old}}
            except Exception:                               # noqa: BLE001
                pass
        got = 0
        errs = []
        miss = 0
        for d in sorted(dates, reverse=True):               # 新→旧，先保证最近的数据
            cur = store['data'].get(d)
            if cur and cur.get('contract') == inst:         # 同合约同日期，已有
                continue
            try:
                one = fetch_one(inst, d)
            except Exception as e:                          # noqa: BLE001
                one = None
                errs.append('%s:%s' % (d, str(e)[:40]))
            if one:
                store['data'][d] = one
                if d not in store['dates']:
                    store['dates'].append(d)
                got += 1
                miss = 0
            else:
                miss += 1
                if miss >= 2 and got == 0:
                    break                                   # 新浪未收录该品种/合约，不必再试
            time.sleep(DELAY)
        store['dates'] = sorted(store['dates'], reverse=True)[:KEEP_DAYS]
        keep = set(store['dates'])
        store['data'] = {k: v for k, v in store['data'].items() if k in keep}
        if store['dates']:
            store['data'] = {k: store['data'][k] for k in sorted(store['data'], reverse=True)}
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(store, f, ensure_ascii=False, separators=(',', ':'))
        elif os.path.exists(fpath) and not errs:
            os.remove(fpath)                                # 新浪未收录 → 不留空文件
        return (prod, inst, got, len(store['dates']), errs)

    ok = 0
    empty = 0
    failed = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for prod, inst, got, ndays, errs in ex.map(work, products):
            if inst is None:
                continue
            if got == 0:
                empty += 1
            ok += 1
            failed.extend('%s %s' % (prod, e) for e in errs)
            print('  %-4s %-7s 新增 %d 天（共 %d 天）' % (prod, inst, got, ndays))

    print('龙虎榜采集完成：%d 品种，目标 %d 天（%s ~ %s）' % (ok, len(dates), dates[0], dates[-1]))
    if empty:
        print('  其中 %d 个品种本次无新增' % empty)
    if failed:
        print('  失败 %d 次：%s' % (len(failed), '; '.join(failed[:8])))


if __name__ == '__main__':
    main()
