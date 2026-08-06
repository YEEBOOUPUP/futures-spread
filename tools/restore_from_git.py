# -*- coding: utf-8 -*-
"""
restore_from_git.py — 从 git 历史恢复核心品种（P/Y/OI/M/RM）的 WIND Excel 完整数据
（2015 起、主力/最近合约、close），覆盖被新浪重建覆盖的版本。
数据源：commit 2d5e8ec 的 data/data.json（WIND 宽表 2817 交易日完整版）
用法：python tools/restore_from_git.py
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')
CORE = ['P', 'Y', 'OI', 'M', 'RM']
COMMIT = '2d5e8ec'


def label_key(lb):
    if lb == '主力':
        return (0, 0)
    if lb == '最近':
        return (0, 1)
    return (1, int(lb))


def main():
    raw = subprocess.check_output(['git', 'show', '%s:data/data.json' % COMMIT], cwd=BASE)
    d = json.loads(raw.decode('utf-8'))
    print('git %s 的 data.json: %d 交易日 %s ~ %s' % (COMMIT, len(d['dates']), d['dates'][0], d['dates'][-1]))

    index = json.load(open(INDEX_FILE, encoding='utf-8'))
    for prod in CORE:
        if prod not in d['series']:
            print('跳过（git 数据无此品种）:', prod)
            continue
        src = d['series'][prod]  # label -> metric -> [prices]
        labels = {lb for lb in src if 'close' in src[lb]}
        # 与当前文件（新浪版）合并：git 数据优先，新浪版多余的日期并入
        fpath = os.path.join(DATA_DIR, prod + '.json')
        cur = json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else None
        merged = {lb: {dt: v for dt, v in zip(d['dates'], src[lb]['close']) if v is not None} for lb in labels}
        if cur:
            cur_dates = set(cur['dates'])
            git_dates = set(d['dates'])
            for clb, cser in cur['series'].items():
                for i, dt in enumerate(cur['dates']):
                    if dt not in git_dates and i < len(cser['close']) and cser['close'][i] is not None:
                        merged.setdefault(clb, {})[dt] = cser['close'][i]
        dates = sorted(set().union(*[set(v.keys()) for v in merged.values()]))
        out = {'dates': dates, 'series': {m: {'close': [merged[m].get(dd) for dd in dates]} for m in merged}}
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
        contracts = sorted(merged.keys(), key=label_key)
        index['products'].setdefault(prod, {})['contracts'] = contracts
        index['products'][prod]['metrics'] = ['close']
        index['products'][prod]['file'] = prod + '.json'
        main_arr = merged.get('主力', {}).get(dates[0])
        print('[%s] %d 天 %s ~ %s, 合约 %d 个, 主力首日=%s' % (prod, len(dates), dates[0], dates[-1], len(contracts), main_arr))
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    print('恢复完成')


if __name__ == '__main__':
    main()
