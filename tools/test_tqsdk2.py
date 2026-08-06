# -*- coding: utf-8 -*-
"""测试 tqsdk 账号 + 外盘月度合约日线"""
from tqsdk import TqApi, TqAuth

AUTH = TqAuth('13277930996', 'wyb15967613709')

try:
    api = TqApi(auth=AUTH, _stock=False)
    print('连接成功!')
except Exception as e:
    print('连接失败:', type(e).__name__, str(e)[:200])
    raise SystemExit

# 测试外盘合约代码格式（CBOT 美豆各月份、BMD 马棕、COMEX 黄金）
tests = [
    ('CBOT.ZS2603', 'CBOT美豆2603'),
    ('CBOT.ZS2611', 'CBOT美豆2611'),
    ('CBOT.ZL2607', 'CBOT美豆油2607'),
    ('BMD.FCPO2601', 'BMD马棕2601'),
    ('COMEX.GC2612', 'COMEX黄金2612'),
    ('CME.CL2609', 'CME原油2609'),
]
for sym, desc in tests:
    try:
        k = api.get_kline_serial(sym, 86400, 300)
        api.wait_update()
        n = len(k)
        if n:
            print(f'{sym} [{desc}]: {n} 根日线, 首 {k.iloc[0]["datetime"]}, 尾 {k.iloc[-1]["datetime"]}')
        else:
            print(f'{sym} [{desc}]: 空')
    except Exception as e:
        print(f'{sym} [{desc}]: 失败 {type(e).__name__}: {str(e)[:120]}')
    api.close()
    try:
        api = TqApi(auth=AUTH, _stock=False)
    except Exception as e:
        print('重连失败:', e)
        break
