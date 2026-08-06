# -*- coding: utf-8 -*-
"""测试 tqsdk 外盘 K 线（可能需要天勤账号）"""
import sys

try:
    from tqsdk import TqApi, TqAuth, TqKq
    print('tqsdk 导入 OK')
except Exception as e:
    print('导入失败:', e)
    sys.exit(0)

# 尝试无账号连接（tqsdk 免费版可匿名访问有限数据）
try:
    api = TqApi(auth=TqAuth('', ''), _stock=False)
    print('匿名连接成功')
    # 外盘合约代码猜测格式
    for sym in ['GLOBAL.ZS2603', 'GLOBAL.ZS2609', 'GLOBAL.FCPO2601', 'GLOBAL.ZL2603']:
        try:
            k = api.get_kline_serial(sym, 86400, 5)
            api.wait_update()
            print(f'{sym}: 最新 {k.iloc[-1]["datetime"]} close={k.iloc[-1]["close"]}')
        except Exception as e:
            print(f'{sym}: 失败 {type(e).__name__}: {str(e)[:90]}')
    api.close()
except Exception as e:
    print('连接失败（可能需要天勤账号）:', type(e).__name__, str(e)[:200])
