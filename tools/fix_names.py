# -*- coding: utf-8 -*-
"""修正 data/index.json 中品种的中文名（openctp 部分品种名为小写代码，需映射）"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(BASE, 'data', 'index.json')

# 品种代码 → 中文名（覆盖 openctp 缺失/无效的名称）
PRODUCT_NAMES = {
    'A': '豆一', 'AD': '苹果干', 'AG': '白银', 'AL': '铝', 'AO': 'AO', 'AP': '苹果',
    'AU': '黄金', 'B': '豆二', 'BB': '胶合板', 'BC': '国际铜', 'BR': '丁二烯橡胶',
    'BU': '沥青', 'BZ': '纯苯', 'C': '玉米', 'CF': '棉花', 'CJ': '红枣', 'CS': '玉米淀粉',
    'CU': '铜', 'CY': '棉纱', 'EB': '苯乙烯', 'EC': '集运指数', 'EG': '乙二醇', 'FB': '纤维板',
    'FG': '玻璃', 'FU': '燃料油', 'HC': '热卷', 'I': '铁矿石', 'IC': '中证500',
    'IF': '沪深300', 'IH': '上证50', 'IM': '中证1000', 'J': '焦炭', 'JD': '鸡蛋',
    'JM': '焦煤', 'JR': '粳稻', 'L': '塑料', 'LC': '碳酸锂', 'LG': '原木', 'LH': '生猪',
    'LU': '低硫燃料油', 'M': '豆粕', 'MA': '甲醇', 'NI': '镍', 'NR': '20号胶', 'OI': '菜油',
    'OP': 'OP', 'P': '棕榈油', 'PB': '铅', 'PD': '钯', 'PF': '短纤', 'PG': '液化气',
    'PK': '花生', 'PL': 'PL', 'PM': '普麦', 'PP': '聚丙烯', 'PR': '瓶片', 'PS': '多晶硅',
    'PT': '铂', 'PX': '对二甲苯', 'RB': '螺纹钢', 'RI': '早籼稻', 'RM': '菜粕', 'RR': '粳米',
    'RS': '菜籽', 'RU': '橡胶', 'SA': '纯碱', 'SC': '原油', 'SF': '硅铁', 'SH': '烧碱',
    'SI': '工业硅', 'SM': '锰硅', 'SN': '锡', 'SP': '纸浆', 'SR': '白糖', 'SS': '不锈钢',
    'T': '十年国债', 'TA': 'PTA', 'TF': '五年国债', 'TL': '三十年期国债', 'TS': '两年国债',
    'UR': '尿素', 'V': '聚氯乙烯', 'WH': '强麦', 'WR': '线材', 'Y': '豆油', 'ZC': '动力煤',
    'ZN': '锌',
}


def clean(name, code):
    """openctp 名称若是小写代码等无效值，返回 None"""
    if not name:
        return None
    if name == code or name == code.lower() or name == code.upper():
        return None
    if len(name) <= 2 and name.isalpha():
        return None
    return name


def main():
    idx = json.load(open(INDEX, encoding='utf-8'))
    changed = 0
    for code, info in idx['products'].items():
        old = info.get('name', '')
        new = clean(old, code) or PRODUCT_NAMES.get(code, old)
        if new != old:
            info['name'] = new
            changed += 1
    json.dump(idx, open(INDEX, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('修正 %d 个品种的中文名' % changed)
    for code in sorted(idx['products']):
        print('%s\t%s' % (code, idx['products'][code]['name']))


if __name__ == '__main__':
    main()
