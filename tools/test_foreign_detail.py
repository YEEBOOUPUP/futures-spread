# -*- coding: utf-8 -*-
"""测试 akshare 外盘详情接口，寻找月份合约日线"""
import akshare as ak
import inspect

for fn in ['futures_foreign_detail', 'futures_foreign_commodity_realtime']:
    try:
        f = getattr(ak, fn)
        print(f'=== {fn} 签名:', inspect.signature(f))
        try:
            if fn == 'futures_foreign_detail':
                df = f()
                print('结果:', len(df) if df is not None else 'None')
                if df is not None and len(df):
                    print(list(df.columns))
                    print(df.head(3).to_string())
            else:
                df = f(symbol='ZSD')
                print('ZSD 结果:', len(df) if df is not None else 'None')
                if df is not None and len(df):
                    print(df.to_string())
        except Exception as e:
            print('调用失败:', type(e).__name__, str(e)[:100])
    except Exception as e:
        print(f'{fn}: 不可用 {type(e).__name__}')
