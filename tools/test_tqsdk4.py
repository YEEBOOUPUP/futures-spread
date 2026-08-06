# -*- coding: utf-8 -*-
"""探测 tqsdk 外盘合约代码格式（含原油），带超时保护"""
import sys
import time
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth('13277930996', 'wyb15967613709'))
tests = [
    # (代码, 说明)
    ('CME.CL2609', 'CME 原油2609'),
    ('NYMEX.CL2609', 'NYMEX 原油2609'),
    ('CBOT.ZS2603', 'CBOT 美豆2603'),
    ('CBOT.ZS2611', 'CBOT 美豆2611'),
    ('BMD.FCPO2601', 'BMD 马棕2601'),
    ('CBOT.ZL2607', 'CBOT 美豆油2607'),
    ('CBOT.ZM2607', 'CBOT 美豆粕2607'),
    ('COMEX.GC2612', 'COMEX 黄金2612'),
]
for sym, desc in tests:
    try:
        k = api.get_kline_serial(sym, 86400, 100)
        api.wait_update(deadline=time.time() + 10)
        n = len(k)
        if n > 0:
            print(f'{sym} [{desc}]: OK {n} 根, 尾={k.iloc[-1]["datetime"]} close={k.iloc[-1]["close"]}', flush=True)
        else:
            print(f'{sym} [{desc}]: 空序列（合约不存在或无行情）', flush=True)
    except Exception as e:
        print(f'{sym} [{desc}]: 失败 {type(e).__name__}: {str(e)[:100]}', flush=True)
api.close()
print('完成', flush=True)
