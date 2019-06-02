"""交换机监控接入模块，使用模拟登录。交换机监控项目地址：https://github.com/AlbumenJ/switch-monitor"""
import requests

USERNAME = ""
PASSWORD = ""
URL = ""


def login():
    """登录交换机监控，返回认证信息（认证信息加到请求头部）"""
    login = False
    retry_times = 0
    while not login:
        s = requests.Session()
        a = s.get(URL + "auth/commonlogin?username=%s&password=%s" % (USERNAME, PASSWORD))
        if a.json()["success"] == True:
            login = True
        else:
            login = False

        if login:
            return a.json()["token"]
        else:
            retry_times += 1
            if retry_times == 3:
                raise RuntimeError('交换机监控登录失败')


def get_warnings(t):
    a = requests.get(URL + "api/warnings", headers={"Authorization": t})
    return a.json()['warning']


def get_vlan_ip(cvlan, pvlan, t):
    if cvlan == pvlan == '0':
        return 'unknown'
    a = requests.get(URL + "api/vlan/%s/%s" % (cvlan, pvlan), headers={"Authorization": t})
    return a.json()['object']['ip']


if __name__ == '__main__':
    token = login()
    print(get_warnings(token))
    print(get_vlan_ip(102, 101, token))
