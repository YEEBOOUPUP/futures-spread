# -*- coding: utf-8 -*-
"""
foreign_monthly.py — 东财外盘期货月度合约数据（真实月差数据源）

- 用东财外盘接口（需代理）：futures_global_spot_em 拿品种/合约列表，futures_global_hist_em 拉历史
- 品种代码规范：F_ 前缀 + 东财品种前缀（F_ZS 美豆、F_ZL 美豆油、F_ZM 美豆粕、F_ZC 美玉米...）
- 合约结构：同国内（dates + series{月份}.close），月份字母转数字（F=1 G=2 H=3 J=4 K=5 M=6 N=7 Q=8 U=9 V=10 X=11 Z=12）
- 连续月拼接：同品种同月份历年合约按日期合并（重叠取较新年份）

模式：
  --init  全量初始化（拉 2019 年至今所有月份合约，一次性）
  --daily 每日增量（只拉当前存续合约的历史并合并，幂等，约 2-3 分钟）
用法：python collector/foreign_monthly.py --init    # 首次
      python collector/foreign_monthly.py --daily   # 每日（update_daily 调用）
"""
import argparse
import json
import os
import re
import sys
import time

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'

import akshare as ak

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')
START_YEAR = 2019

MONTH_LETTER = {1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
                7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'}
LETTER_MONTH = {v: k for k, v in MONTH_LETTER.items()}


def fetch_hist(symbol):
    """东财外盘合约历史 → {date: close} 或 None"""
    try:
        df = ak.futures_global_hist_em(symbol=symbol)
    except Exception:
        return None
    if df is None or len(df) == 0:
        return None
    out = {}
    for _, row in df.iterrows():
        d = str(row['日期'])[:10]
        c = row['最新价']
        if c is None or (isinstance(c, float) and c != c):
            continue
        out[d] = float(c)
    return out or None


def parse_code(code):
    """'ZS26Z' → ('ZS', 26, 'Z')；连续合约（00Y 等）返回 None"""
    m = re.match(r'^([A-Z]+)(\d{2})([A-Z])$', code)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3)


def clean_name(name):
    """'大豆2809'→'大豆'；'糖11号'→'糖11号'（只去 4 位年份数字）"""
    return re.sub(r'\d{4}', '', str(name)).replace('当月连续', '').replace('连续', '').strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['init', 'daily'], default='init')
    args = ap.parse_args()

    spot = ak.futures_global_spot_em()
    if spot is None or len(spot) == 0:
        sys.exit('东财外盘 spot 接口失败')

    # 品种分组：前缀 → {name, months: {月字母}} + 当前存续合约代码
    groups = {}
    contracts_of = {}
    for _, row in spot.iterrows():
        code = str(row['代码'])
        p = parse_code(code)
        if not p:
            continue
        prefix, yy, letter = p
        g = groups.setdefault(prefix, {'name': '', 'months': set()})
        g['name'] = clean_name(row['名称']) or g['name']
        g['months'].add(letter)
        contracts_of.setdefault(prefix, []).append(code)

    index = json.load(open(INDEX_FILE, encoding='utf-8')) if os.path.exists(INDEX_FILE) else {'products': {}}
    cur_year = time.localtime().tm_year

    for prefix in sorted(groups):
        g = groups[prefix]
        code_f = 'F_' + prefix
        months_letters = sorted(g['months'])
        # 目标合约列表
        targets = []
        if args.mode == 'init':
            for yy in range(START_YEAR % 100, (cur_year + 1) % 100 + 1):
                yy2 = 2000 + (yy if yy >= START_YEAR % 100 else yy + 100) if False else yy
                for letter in months_letters:
                    targets.append('%s%02d%s' % (prefix, yy, letter))
        else:  # daily：当前存续合约
            targets = contracts_of.get(prefix, [])

        # 拉取并拼接
        merged = {}   # 月份字母 → {date: close}
        fetched = 0
        for sym in targets:
            data = fetch_hist(sym)
            if not data:
                continue
            fetched += 1
            p2 = parse_code(sym)
            if not p2:
                continue
            letter = p2[2]
            bucket = merged.setdefault(letter, {})
            for d, c in data.items():
                bucket[d] = c   # 重叠日：后拉（较新年份）覆盖
            time.sleep(0.15)
        if not merged:
            continue

        # 月份字母 → 数字标签
        series = {}
        all_dates = set()
        for letter, data in merged.items():
            month = '%02d' % LETTER_MONTH[letter]
            series[month] = {'close': [data[d] for d in sorted(data)]}
            all_dates.update(data.keys())
        dates = sorted(all_dates)

        # 合并已有文件（幂等）
        fpath = os.path.join(DATA_DIR, code_f + '.json')
        if os.path.exists(fpath):
            old = json.load(open(fpath, encoding='utf-8'))
            old_dates = set(old['dates'])
            if old_dates.issubset(set(dates)):
                pass  # 新数据已含旧数据
            else:
                # 需要合并旧数据
                merged_all = {d: {} for d in dates}
                for om, oser in old['series'].items():
                    for i, d in enumerate(old['dates']):
                        merged_all.setdefault(d, {})[om] = oser['close'][i]
                for d in dates:
                    for m, c in series.items():
                        merged_all.setdefault(d, {})[m] = c['close'][dates.index(d)]
                # 重建
                nd = sorted(merged_all)
                series = {}
                for m in sorted({k for d in merged_all for k in merged_all[d]}):
                    series[m] = {'close': [merged_all[d].get(m) for d in nd]}
                dates = nd
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump({'dates': dates, 'series': series}, f, ensure_ascii=False, separators=(',', ':'))
        index['products'][code_f] = {
            'name': g['name'], 'contracts': sorted(series.keys()),
            'metrics': ['close'], 'file': code_f + '.json', 'foreign': True,
        }
        print('[%s] %s %s: 月份 %s, %d 天, %s ~ %s' % (
            args.mode, code_f, g['name'], ','.join(sorted(series.keys())),
            len(dates), dates[0] if dates else '-', dates[-1] if dates else '-'))

    from datetime import datetime
    index['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    print('东财外盘%s完成，共 %d 个外盘品种' % ('初始化' if args.mode == 'init' else '更新', len(groups)))


if __name__ == '__main__':
    main()
