# -*- coding: utf-8 -*-
"""
history_fill.py — 用新浪期货日线重建全市场历史数据（2019 至今，收盘价）

流程：
  1. 从 openctp 数据中心 instruments 接口获取全市场期货品种（代码/中文名/活跃月份集合）
  2. 对每个品种每个活跃月份，枚举历年合约（2019~当前年+1），用新浪日线接口逐个拉取
  3. 按"连续月合约"规则拼接：同一品种同一月份，历年合约按时间无缝衔接（重叠日取较新合约）
  4. 输出 data/index.json + data/{品种}.json

用法：python collector/history_fill.py
依赖：pip install akshare（新浪源）
"""
import json
import os
import re
import sys
import time
import urllib.request

import akshare as ak

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
START_YEAR = 2019          # 新浪历史深度约 2019 起
INSTRUMENTS_URL = 'http://dict.openctp.cn/instruments?types=futures'
SLEEP = 0.15               # 新浪请求间隔（秒）

# 常见品种中文名兜底（openctp 名称缺失时用）
FALLBACK_NAMES = {
    'P': '棕榈油', 'Y': '豆油', 'OI': '菜油', 'M': '豆粕', 'RM': '菜粕',
    'A': '豆一', 'B': '豆二', 'C': '玉米', 'CS': '淀粉', 'L': '塑料',
    'PP': '聚丙烯', 'V': 'PVC', 'EG': '乙二醇', 'EB': '苯乙烯', 'PG': '液化气',
    'J': '焦炭', 'JM': '焦煤', 'I': '铁矿石', 'RR': '粳米', 'JD': '鸡蛋',
    'LH': '生猪', 'FB': '纤维板', 'BB': '胶合板',
    'CU': '铜', 'AL': '铝', 'ZN': '锌', 'PB': '铅', 'NI': '镍', 'SN': '锡',
    'AU': '黄金', 'AG': '白银', 'RB': '螺纹钢', 'HC': '热卷', 'SS': '不锈钢',
    'WR': '线材', 'FU': '燃料油', 'BU': '沥青', 'RU': '橡胶', 'NR': '20号胶',
    'SP': '纸浆', 'SC': '原油', 'LU': '低硫燃料油', 'BC': '国际铜',
    'TA': 'PTA', 'MA': '甲醇', 'SA': '纯碱', 'FG': '玻璃', 'UR': '尿素',
    'CF': '棉花', 'SR': '白糖', 'AP': '苹果', 'CY': '棉纱', 'PK': '花生',
    'PF': '短纤', 'PX': '对二甲苯', 'SH': '烧碱', 'SM': '锰硅', 'SF': '硅铁',
    'ZC': '动力煤', 'WH': '强麦', 'PM': '普麦', 'RI': '早籼稻', 'LR': '晚籼稻',
    'JR': '粳稻', 'RS': '菜籽', 'CJ': '红枣', 'UR': '尿素',
    'LC': '碳酸锂', 'SI': '工业硅', 'PS': '多晶硅',
    'IF': '沪深300', 'IH': '上证50', 'IC': '中证500', 'IM': '中证1000',
    'T': '十年国债', 'TF': '五年国债', 'TS': '两年国债', 'TL': '三十年国债',
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def get_products():
    """从 openctp 数据中心拿品种列表（代码/中文名/活跃月份集合）"""
    data = fetch_json(INSTRUMENTS_URL)
    if data.get('rsp_code') != 0:
        raise RuntimeError('instruments 接口失败: ' + str(data.get('rsp_message')))
    products = {}
    for item in data['data']:
        if item.get('ProductClass') not in ('1', '2'):
            continue
        code = str(item.get('ProductID', '')).upper()
        inst = str(item.get('InstrumentID', ''))
        if not code or not inst:
            continue
        m = re.search(r'(\d{2})$', inst)          # 合约尾部月份
        if not m:
            continue
        month = m.group(1)
        p = products.setdefault(code, {'name': '', 'months': set()})
        p['months'].add(month)
        if not p['name']:
            name = str(item.get('InstrumentName', '') or '')
            name = re.sub(r'[0-9]+$', '', name).strip()
            p['name'] = name or FALLBACK_NAMES.get(code, '')
    return products


def fetch_contract_daily(symbol):
    """拉取一个合约的历史日线，返回 {date: close} 或 None"""
    try:
        df = ak.futures_zh_daily_sina(symbol=symbol)
    except Exception:
        return None
    if df is None or len(df) == 0:
        return None
    out = {}
    for _, row in df.iterrows():
        d = str(row['date'])[:10]
        c = row['close']
        if c is None or (isinstance(c, float) and c != c):   # NaN
            continue
        out[d] = float(c)
    return out or None


def build_product_series(products, current_year, log=print):
    """对每个品种拉取所有月份合约并拼接，返回 {code: {month: {date: close}}}"""
    result = {}
    codes = sorted(products)
    for ci, code in enumerate(codes):
        info = products[code]
        months = sorted(info['months'])
        series = {}
        total_fetch = 0
        for month in months:
            merged = {}
            for year in range(START_YEAR, current_year + 2):
                sym = '%s%02d%s' % (code, year % 100, month)
                data = fetch_contract_daily(sym)
                if data:
                    total_fetch += 1
                    for d, c in data.items():
                        # 重叠日取较新合约（年份大者覆盖）
                        merged[d] = c
                time.sleep(SLEEP)
            if merged:
                series[month] = merged
        result[code] = series
        n = sum(len(v) for v in series.values())
        log('[%d/%d] %s(%s) 月份[%s] 合约序列数=%d 数据点数=%d'
            % (ci + 1, len(codes), code, info['name'], ','.join(months), len(series), n))
    return result


def main():
    print('=== 期货历史数据重建（新浪，%d 年起）===' % START_YEAR)
    products = get_products()
    print('品种数: %d' % len(products))
    current_year = int(__import__('datetime').datetime.now().year)
    print('拉取中（预计 20-60 分钟，请耐心等待）...')

    all_series = build_product_series(products, current_year)
    if not all_series:
        sys.exit('没有拉到任何数据，请检查网络/akshare')

    # 写文件：index.json + 各品种文件
    os.makedirs(DATA_DIR, exist_ok=True)
    index_products = {}
    for code in sorted(all_series):
        series = all_series[code]
        if not series:
            continue
        # 品种 dates = 该品种所有月份的日期并集（排序）
        dates = sorted(set().union(*[set(v.keys()) for v in series.values()]))
        # 序列数组化（与 dates 对齐）
        out_series = {}
        for month, m in series.items():
            out_series[month] = {'close': [m.get(d) for d in dates]}
        with open(os.path.join(DATA_DIR, code + '.json'), 'w', encoding='utf-8') as f:
            json.dump({'dates': dates, 'series': out_series}, f, ensure_ascii=False, separators=(',', ':'))
        info = products.get(code, {})
        index_products[code] = {
            'name': info.get('name', FALLBACK_NAMES.get(code, '')),
            'contracts': sorted(series.keys()),
            'metrics': ['close'],
            'file': code + '.json',
        }

    from datetime import datetime
    index = {
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'source': 'sina-daily + openctp',
        'products': index_products,
    }
    with open(os.path.join(DATA_DIR, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    total_days = sum(len(open(os.path.join(DATA_DIR, code + '.json'), encoding='utf-8').read()) for code in index_products)
    print('完成：%d 个品种 → data/ 目录（index.json + 各品种文件，共 %.1f MB）'
          % (len(index_products), total_days / 1024 / 1024))


if __name__ == '__main__':
    main()
