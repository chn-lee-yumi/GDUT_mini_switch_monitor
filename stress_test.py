"""API压测模块。"""
import requests
import threading
import time

for number in range(3115000000, 3119000000, 200):
    t0 = time.time()
    ts = []
    for x in range(0, 200):
        ts.append(
            threading.Thread(target=requests.get, args=(
                "https://mini-monitor.gdutnic.com/api/query?number=%d" % (number + x),)))  # 辣鸡学校，不给域名
    for t in ts:
        t.start()
    ts[100].join()
    print(number, time.time() - t0)
