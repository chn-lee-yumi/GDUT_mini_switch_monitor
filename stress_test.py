"""API压测模块。"""
import requests
import threading
import time

for number in range(3115000000, 3119000000, 100):
    t0 = time.time()
    ts = []
    for x in range(0, 200):
        ts.append(
            threading.Thread(target=requests.get,
                             args=("https://gdutnic.com/api/warning?number=%d" % (number + x),)))
    for t in ts:
        t.start()
    ts[50].join()
    print(number, time.time() - t0)
