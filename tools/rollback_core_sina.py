# -*- coding: utf-8 -*-
"""
rollback_core_sina.py — 核心品种（P/Y/OI/M/RM）回滚为新浪数据版（afd6907，2018 起 01-12 月合约）
用户决定：其他品种用新浪数据，外盘用 Excel（马棕/美豆油已导入，保留不动）
用法：python tools/rollback_core_sina.py
"""
import json
import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
INDEX_FILE = os.path.join(DATA_DIR, 'index.json')
CORE = ['P', 'Y', 'OI', 'M', 'RM']
COMMIT = 'afd6907'


def git_json(path):
    raw = subprocess.check_output(['git', 'show', '%s:%s' % (COMMIT, path)], cwd=BASE)
    return json.loads(raw.decode('utf-8'))


def main():
    idx = json.load(open(INDEX_FILE, encoding='utf-8'))
    old_idx = git_json('data/index.json')
    for prod in CORE:
        src = git_json('data/%s.json' % prod)
        with open(os.path.join(DATA_DIR, prod + '.json'), 'w', encoding='utf-8') as f:
            json.dump(src, f, ensure_ascii=False, separators=(',', ':'))
        info = old_idx['products'].get(prod, {})
        idx['products'][prod] = info
        print('[%s] %d 天 %s ~ %s, 合约: %s' % (prod, len(src['dates']), src['dates'][0], src['dates'][-1], info.get('contracts')))
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, separators=(',', ':'))
    print('回滚完成，外盘品种保留：', [k for k, v in idx['products'].items() if v.get('foreign')][:5], '...')


if __name__ == '__main__':
    main()
