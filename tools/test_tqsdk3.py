# -*- coding: utf-8 -*-
"""按 SKILL.md：连接 tqsdk → query_quotes 发现外盘合约 → 拉月度合约日线"""
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth('13277930996', 'wyb15967613709'))
try:
    # 1. 发现外盘期货合约（CBOT / BMD / COMEX）
    for exch in ['CBOT', 'BMD', 'COMEX']:
        try:
            q = api.query_quotes(ins_class='FUTURE', exchange_id=exch, expired=False)
            info = api.query_symbol_info(list(q))
            cols = ['instrument_id', 'product_id', 'instrument_name']
            sub = info[[c for c in cols if c in info.columns]]
            print(f'=== {exch} 存续期货合约: {len(sub)} 个 ===')
            print(sub.head(10).to_string())
        except Exception as e:
            print(f'{exch}: 失败 {type(e).__name__}: {str(e)[:120]}')
finally:
    api.close()
