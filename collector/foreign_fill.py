# -*- coding: utf-8 -*-
"""
foreign_fill.py — 新浪外盘期货：全量重拉 + 合并去重（初始化与每日更新通用）

- 外盘 30 个品种（主力连续合约），代码统一加 F_ 前缀避免与国内冲突
- 每次运行对每个品种全量重拉历史（约 10-20 秒），与现有数据按日期去重合并 → 幂等
- 更新 data/index.json（新增/更新外盘品种条目）

用法：python collector/foreign_fill.py
"""
import json
import os
import sys
import time
from datetime import datetime

import akshare as ak

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')

# 外盘代码 → 中文名（F_ 前缀避免与国内品种冲突）
FOREIGN = {
    'FEF': '欧洲电力', 'FCPO': '马棕油', 'RSS3': '泰胶', 'RS': 'RS', 'BTC': '比特币',
    'CT': '美棉', 'NID': '伦镍', 'PBD': '伦铅', 'SND': '伦锡', 'ZSD': '美豆',
    'AHD': 'AHD', 'CAD': 'CAD', 'S': 'S', 'W': '美小麦', 'C': '美玉米',
    'BO': '美豆油', 'SM': '美豆粕', 'TRB': 'TRB', 'HG': 'CMX铜', 'NG': '天然气',
    'CL': 'WTI原油', 'SI': 'CMX白银', 'GC': 'CMX黄金', 'LHC': '瘦肉猪', 'OIL': '布伦特原油',
    'XAU': '伦敦金', 'XAG': '伦敦银', 'XPT': '铂金', 'XPD': '钯金', 'EUA': '碳配额',
}


def main():
    index = json.load(open(INDEX_FILE, encoding='utf-8')) if os.path.exists(INDEX_FILE) else {'products': {}}
    added, updated = 0, 0
    for sym, name in FOREIGN.items():
        code = 'F_' + sym
        try:
            df = ak.futures_foreign_hist(symbol=sym)
        except Exception as e:
            print('拉取失败 %s: %s' % (sym, e))
            continue
        if df is None or len(df) == 0:
            continue
        # date → close
        data = {}
        for _, row in df.iterrows():
            d = str(row['date'])[:10]
            c = row['close']
            if c is None or (isinstance(c, float) and c != c):
                continue
            data[d] = float(c)
        if not data:
            continue
        # 合并已有文件（按日期去重）
        fpath = os.path.join(DATA_DIR, code + '.json')
        if os.path.exists(fpath):
            old = json.load(open(fpath, encoding='utf-8'))
            old_data = dict(zip(old['dates'], old['series']['主力']['close']))
            old_data.update(data)
            data = old_data
        dates = sorted(data)
        out = {'dates': dates, 'series': {'主力': {'close': [data[d] for d in dates]}}}
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
        existed = code in index['products']
        index['products'][code] = {
            'name': name, 'contracts': ['主力'], 'metrics': ['close'],
            'file': code + '.json', 'foreign': True,
        }
        if existed:
            updated += 1
        else:
            added += 1
        print('[%s] %s %s: %d 天, %s ~ %s' % ('新增' if not existed else '更新', code, name, len(dates), dates[0], dates[-1]))
        time.sleep(0.2)

    index['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    print('外盘更新完成：新增 %d 个，更新 %d 个，共 %d 个外盘品种' % (added, updated, len(FOREIGN)))


if __name__ == '__main__':
    main()
