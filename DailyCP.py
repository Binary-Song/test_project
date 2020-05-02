import requests
import json
import io
import random
import time
import re
import pyDes
import base64
import uuid

class DailyCP:
    def __init__(self, host="aust.campusphere.net"):
        self.key = "ST83=@XV"#dynamic when app update
        self.t = str(int(round(time.time() * 1000)))
        self.session = requests.session()
        self.host = host
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
            # "User-Agent": "okhttp/3.12.4"
        })
        url = "https://"+self.host+"/iap/login?service=https%3A%2F%2F" + \
            self.host+"%2Fportal%2Flogin"
        ret = self.session.get(url)
        self.client = re.findall(re.compile(
            r'id=\"lt\" value=\"(.*?)\"'), ret.text)[0]
        self.encryptSalt = re.findall(re.compile(
            r'id=\"encryptSalt\" type=\"hidden\" value=\"(.*?)\"'), ret.text)[0]

    def encrypt(self,text):
        k = pyDes.des(self.key, pyDes.CBC, b"\x01\x02\x03\x04\x05\x06\x07\x08", pad=None, padmode=pyDes.PAD_PKCS5)
        ret = k.encrypt(text)
        return base64.b64encode(ret).decode()

    def decrypt(self,text):
        k = pyDes.des(self.key, pyDes.CBC, b"\x01\x02\x03\x04\x05\x06\x07\x08", pad=None, padmode=pyDes.PAD_PKCS5)
        ret = k.decrypt(base64.b64decode(text))
        return ret.decode()

    def checkNeedCaptcha(self, username):
        url = "https://"+self.host+"/iap/checkNeedCaptcha?username="+username+"&_="+self.t
        ret = self.session.get(url)
        ret = json.loads(ret.text)
        return ret["needCaptcha"]

    def generateCaptcha(self):
        url = "https://"+self.host+"/iap/generateCaptcha?ltId=" + \
            self.client+"&codeType=2&"+self.t
        ret = self.session.get(url)
        return ret.content

    def login(self, username, password, captcha=""):
        url = "https://"+self.host+"/iap/doLogin"
        self.username = username
        body = {
            "username": username,
            "password": password,
            "lt": self.client,
            "captcha": captcha,
            "rememberMe": "true",
        }
        self.session.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        ret = self.session.post(url, data=body)
        if ret.text[0] == "{":
            print(json.loads(ret.text))
            return False
        else:return True

    def getCollectorList(self):
        body = {
            "pageSize": 10,
            "pageNumber": 1
        }
        self.session.headers["Content-Type"] = "application/json"
        url = "https://"+self.host + \
            "/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList"
        ret = self.session.post(url, data=json.dumps(body))
        ret = json.loads(ret.text)
        return ret["datas"]["rows"]

    def getNoticeList(self):
        body = {
            "pageSize": 10,
            "pageNumber": 1
        }
        self.session.headers["Content-Type"] = "application/json"
        url = "https://"+self.host + \
            "/wec-counselor-stu-apps/stu/notice/queryProcessingNoticeList"
        ret = self.session.post(url, data=json.dumps(body))
        ret = json.loads(ret.text)
        return ret["datas"]["rows"]

    def confirmNotice(self, wid):
        body = {
            "wid": wid
        }
        self.session.headers["Content-Type"] = "application/json"
        url = "https://"+self.host+"/wec-counselor-stu-apps/stu/notice/confirmNotice"
        ret = self.session.post(url, data=json.dumps(body))
        ret = json.loads(ret.text)
        if ret["message"] == "SUCCESS":return True
        else:
            print(ret["message"])
            return False

    def getCollectorDetail(self, collectorWid):
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/detailCollector"
        body = {
            "collectorWid": collectorWid
        }
        self.session.headers["Content-Type"] = "application/json"
        ret = self.session.post(url, data=json.dumps(body))
        ret = json.loads(ret.text)["datas"]
        url = ret["form"]["formContent"]
        return ret

    def getCollectorFormFiled(self, formWid, collectorWid):
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/getFormFields"
        body = {
            "pageSize": 50,
            "pageNumber": 1,
            "formWid": formWid,
            "collectorWid": collectorWid
        }
        self.session.headers["Content-Type"] = "application/json"
        ret = self.session.post(url, data=json.dumps(body))
        ret = json.loads(ret.text)["datas"]["rows"]
        return ret

    def submitCollectorForm(self, formWid, collectWid, schoolTaskWid, rows, address):
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/submitForm"
        body = {
            "formWid": formWid,
            "collectWid": collectWid,
            "schoolTaskWid": schoolTaskWid,
            "form": rows,
            "address": address
        }
        self.session.headers["Content-Type"] = "application/json"
        # self.session.headers["extension"] = "1" extension
        extension = {"deviceId":str(uuid.uuid4()),"systemName":"未来操作系统","userId":self.username,"appVersion":"8.1.13","model":"红星一号量子计算机","lon":0.0,"systemVersion":"初号机","lat":0.0}
        self.session.headers.update({"Cpdaily-Extension": self.encrypt(json.dumps(extension))})
        ret = self.session.post(url, data=json.dumps(body))
        print(ret.text)
        ret = json.loads(ret.text)
        if ret["message"] == "SUCCESS":return True
        else:
            print(ret["message"])
            return False

    def autoFill(self, rows):
        # isRequired
        for item in rows:
            index = 0
            while index < len(item["fieldItems"]):
                if item["fieldItems"][index]["isSelected"] == 1:index = index + 1
                else:item["fieldItems"].pop(index)

    def autoComplete(self, address):
        collectList = self.getCollectorList()
        print(collectList)
        for item in collectList:
            detail = self.getCollectorDetail(item["wid"])
            form = self.getCollectorFormFiled(
                detail["collector"]["formWid"], detail["collector"]["wid"])
            self.autoFill(form)
            # you can edit this form content by your self.
            # autoFill can fill the form with default value.
            self.submitCollectorForm(detail["collector"]["formWid"], detail["collector"]
                            ["wid"], detail["collector"]["schoolTaskWid"], form, address)

        confirmList = self.getNoticeList()
        print(confirmList)
        for item in confirmList:
            self.confirmNotice(item["noticeWid"])


if __name__ == "__main__":
    app = DailyCP()
    while True:
        account = input("请输入帐号：")
        cap = ""
        if app.checkNeedCaptcha(account):
            with io.open("Captcha.png", "wb") as file:
                file.write(app.generateCaptcha())
            cap = input("请输入验证码(Captcha.png)：")
        password = input("请输入密码：")
        ret = app.login(account, password, cap)
        if ret:break
    address = input("请输入定位地址：")  # "C-137平行宇宙，地球，中国"
    app.autoComplete(address)

# Usage:
#   just edit your id and password.
#   if you are not auster,you need replace the host
#   and run this script
# Author:HuangXu,FengXinYang,ZhouYuYang.
# By:AUST HACKER