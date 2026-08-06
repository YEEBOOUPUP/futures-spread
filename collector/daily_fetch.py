# -*- coding: utf-8 -*-
"""
daily_fetch.py — 每个交易日收盘后，用 openctp 数据中心 prices 接口增量更新收盘价

流程：
  1. 读 data/index.json（品种/月份集合）与现有品种文件
  2. 调 openctp prices 接口（无需注册），对每个品种每月份选"当前存续、最近未交割"合约
  3. 收盘价 = ClosePrice（null 时回退 LastPrice）；按 TradingDay 幂等追加（已有该交易日则跳过）
  4. 写回各品种文件 + 更新 index.json 的 updated_at

用法：python collector/daily_fetch.py
说明：建议每日 15:30 后运行（收盘价已确定）。
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')
PRICES_URL = 'http://dict.openctp.cn/prices?types=futures'


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def parse_instrument(inst):
    """'P2701' → ('P', 2027, 1)；'OI609' → ('OI', 2026, 9)。失败返回 None"""
    m = re.match(r'^([A-Za-z]+)(\d{2})(\d{2})$', inst)
    if not m:
        return None
    code, yy, mm = m.group(1).upper(), int(m.group(2)), int(m.group(3))
    year = 2000 + yy
    return code, year, mm


def main():
    if not os.path.exists(INDEX_FILE):
        sys.exit('缺少 data/index.json，请先运行 collector/history_fill.py 重建历史')
    index = json.load(open(INDEX_FILE, encoding='utf-8'))
    today = datetime.now().strftime('%Y-%m-%d')

    data = fetch_json(PRICES_URL)
    if data.get('rsp_code') != 0:
        sys.exit('prices 接口失败: ' + str(data.get('rsp_message')))

    # 收集每品种每月份的"最近未交割"合约的收盘价
    picks = {}   # code -> {month: close}
    trading_day = None
    for item in data['data']:
        if item.get('ProductClass') != '1':
            continue
        parsed = parse_instrument(str(item.get('InstrumentID', '')))
        if not parsed:
            continue
        code, year, mm = parsed
        month = '%02d' % mm
        # 交割年月 = 20YY-MM
        if (year, mm) <= (datetime.now().year, datetime.now().month):
            continue          # 已交割/正在交割，跳过
        close = item.get('ClosePrice')
        if close is None or close == 0:
            close = item.get('LastPrice')
        if close is None:
            continue
        d = str(item.get('UpdateDate') or '')[:10]
        if d and (trading_day is None or d > trading_day):
            trading_day = d
        picks.setdefault(code, {}).setdefault(month, close)

    if not picks:
        sys.exit('未解析到任何行情（接口可能异常或非交易时段）')

    # 幂等判断：品种文件最后日期 >= trading_day 则跳过
    if trading_day is None:
        trading_day = today
    last_date = None
    any_skip = False
    for code in index['products']:
        f = os.path.join(DATA_DIR, index['products'][code]['file'])
        if os.path.exists(f):
            pf = json.load(open(f, encoding='utf-8'))
            if pf.get('dates'):
                d0 = pf['dates'][-1]
                if last_date is None or d0 > last_date:
                    last_date = d0
    if last_date and last_date >= trading_day:
        print('数据已更新到 %s（今日 %s 无需追加）' % (last_date, trading_day))
        return

    # 追加到各品种文件
    updated = 0
    for code in sorted(index['products']):
        info = index['products'][code]
        f = os.path.join(DATA_DIR, info['file'])
        if not os.path.exists(f):
            continue
        pf = json.load(open(f, encoding='utf-8'))
        month_pick = picks.get(code)
        if not month_pick:
            continue
        if pf['dates'] and pf['dates'][-1] >= trading_day:
            continue
        pf['dates'].append(trading_day)
        changed = False
        for month in info['contracts']:
            c = month_pick.get(month)
            if c is None:
                continue
            series = pf['series'].setdefault(month, {}).setdefault('close', [])
            series.append(float(c))
            changed = True
        if changed:
            with open(f, 'w', encoding='utf-8') as fo:
                json.dump(pf, fo, ensure_ascii=False, separators=(',', ':'))
            updated += 1

    index['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    print('完成：交易日 %s，更新 %d 个品种文件（今日 %s）' % (trading_day, updated, today))


if __name__ == '__main__':
    main()
