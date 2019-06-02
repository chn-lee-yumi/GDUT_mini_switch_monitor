"""Drcom认证计费系统接入模块，使用模拟登录。"""
import requests

USERNAME = ""
PASSWORD = ""
URL = ""


def login():
    """登录drcom，返回登录成功的requests.Session"""
    login = False
    retry_times = 0
    while not login:
        s = requests.Session()
        a = s.get(URL + "login.do?P=logincor")
        # print("cookie(JSESSIONID):", a.cookies["JSESSIONID"])
        checkcode = a.text.split('name="checkcode" type="text" value="')[1][:4].strip('"').strip('"')
        # print("checkcode:", checkcode)

        s.get(URL + "login_random.do?P=execute&randomNum=0.8177881855212492")

        datas = {
            "loginFlag": 1,
            # "adminName": "",
            "usercode": USERNAME,
            # "adminRealName": "",
            "account": USERNAME,
            "password": PASSWORD,
            # "str_random": "",
            "checkcode": checkcode,
            # "Submit": ""
        }
        b = s.post(URL + "loginactioncor.do?P=into", data=datas)
        # print("login text:", b.text)
        if b.text.find("浏览器必须支持框架，才能正常显示") != -1:
            # print("[INFO] Login success!")
            login = True
        else:
            # print("[WARN] Login failed!")
            login = False

        if login:
            return s
        else:
            retry_times += 1
            if retry_times == 5:
                raise RuntimeError('Drcom登录失败')


def query_user_info(number, s):
    datas = {
        "judgeClause": " AND A.FLDUSERNAME LIKE '" + str(number) + "' ",
        "judgeClauseTotalRecords": 1,
        "includeDeleteUsers": "false",
        "page": 1,
        "start": 0,
        "limit": 50
    }
    c = s.post(URL + "user_query.do?P=queryUsers", data=datas)
    # 内部ID：c.json()['data'][0]['FLDUSERID']
    return c.json()


def get_user_id(number, s):
    c = query_user_info(number, s)
    return c['data'][0]['FLDUSERID']


def get_user_info(number, s):
    userid = get_user_id(number, s)
    c = s.get(URL + "user_register.do?P=getUserInfo&edtUserId=%d&math=0.6319344603534873" % userid)
    return c.json()


def get_vlan(number, s):
    c = get_user_info(number, s)
    data = {
        'pvlan': c['edtBindPVlan'],
        'cvlan': c['edtBindVlan']
    }
    return data


def logout(s):
    s.close()


if __name__ == '__main__':
    session = login()
    print(get_vlan("3118000001", session))
