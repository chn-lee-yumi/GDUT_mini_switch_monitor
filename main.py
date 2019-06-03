from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr
import mod_drcom_manager as Drcom
import mod_switch_monitor as Monitor
import json
import time
import logging
from datetime import timedelta

logging.basicConfig(level=logging.INFO, filename='/var/log/mini_monitor.log', filemode='a',
                    format='%(levelname)s: %(message)s')

app = Flask(__name__)
app.send_file_max_age_default = timedelta(seconds=30)
limiter = Limiter(
    app,
    key_func=get_ipaddr,  # 根据访问者的IP记录访问次数
    default_limits=["2/second"]  # 默认限制
)

session = Drcom.login()  # drcom
token = Monitor.login()  # monitor
switch_down_list = []  # 交换机掉线ip列表

building_list = ["东一", "东二", "东三", "东四", "东五", "东六", "东七", "东八", "东九小栋", "东九大栋", "东十小栋", "东十大栋", "东十一小栋", "东十一大栋",
                 "东十二", "东十三", "东十四", "西一", "西二", "西三", "西四", "西五", "西六", "西七", "西八", "西九", "西十", "西十一", "西十二",
                 "西十三", "西十四", "西十五"]

warning_cache = {}
warning_cache_time = 0
warning_expire = 60

vlan_cache = {}  # vlan缓存，key为学号，value为vlan
vlan_cache_time = 0
vlan_expire = 60

ip_cache = {}


@app.route("/")
@limiter.exempt
def index():
    return app.send_static_file("index.html")


@app.route("/api/warning")
@limiter.exempt
def api_warning():
    global token, switch_down_list, warning_cache, warning_cache_time, warning_expire
    # 检查缓存
    if time.time() - warning_expire < warning_cache_time:
        return json.dumps(warning_cache)
    # 调用监控接口获得交换机掉线情况
    try:
        warnings = Monitor.get_warnings(token)
    except:
        try:
            token = Monitor.login()
            warnings = Monitor.get_warnings(token)
        except:
            return json.dumps({"code": -1})
    switch_down_list = []
    # 整理数据
    status = {}
    for b in building_list:  # 初始化掉线数量
        status[b] = 0
    for warn in warnings:
        if warn["warning"] == "devices_down":
            switch_down_list.append(warn['ip'])
            if warn["model"] == "全部设备":
                status[warn['building']] = -1
            else:
                status[warn['building']] += 1
    # 刷新缓存
    warning_cache_time = time.time()
    warning_cache = {"code": 0, "buildings": building_list, "status": status, "time": warning_cache_time}
    return json.dumps(warning_cache)


@app.route("/api/query")
def api_query():
    global session, token, switch_down_list, vlan_cache, vlan_cache_time, vlan_expire, ip_cache
    number = request.args.get('number')
    client_ip = request.headers['X-Forwarded-For']
    # 检查学号范围
    try:
        if not (1129999999 > int(number) > 1110000000 or 2111999999 > int(number) > 2111000000 or 3230000000 > int(
                number) > 3114000000):
            return json.dumps({'code': 0, 'status': 'unknown'})  # 学号范围不正常报错
    except:
        return json.dumps({'code': 0, 'status': 'unknown'})  #
    # 检查缓存
    if time.time() - vlan_expire > vlan_cache_time:
        vlan_cache = {}
        vlan_cache_time = time.time()
    if number not in vlan_cache:
        # 登录drcom获取学号绑定的vlan
        try:
            vlan_info = Drcom.get_vlan(number, session)
        except:
            try:
                session = Drcom.login()
                vlan_info = Drcom.get_vlan(number, session)
            except:
                logging.WARNING("Drcom错误：查询学号为 %s 客户端IP： %s" % (number, client_ip))
                vlan_cache[number] = [0, 0]
                return json.dumps({'code': 0, 'status': 'unknown'})
        # 写入缓存
        vlan_cache[number] = [vlan_info['cvlan'], vlan_info['pvlan']]
    # 检查ip缓存
    try:
        ip = ip_cache[vlan_cache[number][0]][vlan_cache[number][1]]
    except:
        # 调用监控接口获得对应的交换机ip
        try:
            ip = Monitor.get_vlan_ip(vlan_cache[number][0], vlan_cache[number][1], token)
        except:
            try:
                token = Monitor.login()
                ip = Monitor.get_vlan_ip(vlan_cache[number][0], vlan_cache[number][1], token)
            except:
                return json.dumps({"code": -2})
        # 写入缓存
        if vlan_cache[number][0] not in ip_cache:
            ip_cache[vlan_cache[number][0]] = {}
        ip_cache[vlan_cache[number][0]][vlan_cache[number][1]] = ip
    # 判断交换机ip在不在掉线列表里
    if ip == 'unknown':
        status = 'unknown'
    else:
        status = 'up'
        for switch in switch_down_list:
            if switch.count('.') == 2:  # 楼栋掉线
                if ip.split('.')[2] == switch.split('.')[2][:3]:
                    status = 'down'
                    break
            else:  # 单台掉线
                if ip == switch:
                    status = 'down'
                    break

    return json.dumps({'code': 0, 'status': status})


@app.route("/api/clear_ip_cache")
def api_clear_ip_cache():
    global ip_cache
    ip_cache = {}
    return "OK"


if __name__ == '__main__':
    app.run(port=8083)
