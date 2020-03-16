import requests
import json
import io
import random
import time
import re
class DailyCP:
    def __init__(self,host = "aust.campusphere.net"):
        self.t = str(int(round(time.time() * 1000)))
        self.session = requests.session()
        self.host = host
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
            #"User-Agent": "okhttp/3.12.4"
        })
        url = "https://"+self.host+"/iap/login?service=https%3A%2F%2F"+self.host+"%2Fportal%2Flogin"
        ret = self.session.get(url)
        '''
        <input type="hidden" name="lt" id="lt" value="iap:1020372549012747:LT:7d5b799b-c638-4cfc-afa3-5005f0fff56b:20200304203021">
        <input id="encryptSalt" type="hidden" value="3f53a877260c4270">
        '''
        self.client = re.findall(re.compile(r'id=\"lt\" value=\"(.*?)\"'),ret.text)[0]
        self.encryptSalt = re.findall(re.compile(r'id=\"encryptSalt\" type=\"hidden\" value=\"(.*?)\"'),ret.text)[0]
    def checkNeedCaptcha(self,username):
        url = "https://"+self.host+"/iap/checkNeedCaptcha?username="+username+"&_="+self.t
        ret = self.session.get(url)
        ret = json.loads(ret.text)
        return ret["needCaptcha"]
    def generateCaptcha(self):
        url = "https://"+self.host+"/iap/generateCaptcha?ltId="+self.client+"&codeType=2&"+self.t
        ret = self.session.get(url)
        return ret.content
    def login(self,username,password,captcha=""):
        url = "https://"+self.host+"/iap/doLogin"
        body = {
            "username": username,
            "password": password,
            "lt": self.client,
            "captcha": captcha,
            "rememberMe": "true",
        }
        self.session.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        ret = self.session.post(url,data=body)
        if ret.text[0] == "{":
            return json.loads(ret.text)
        else:
            return "SUCCESS"
    def getList(self):
        body ={
            "pageSize":10,
            "pageNumber":1
        }
        self.session.headers["Content-Type"] = "application/json"
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList"
        ret = self.session.post(url,data=json.dumps(body))
        ret = json.loads(ret.text)
        #{"code":"0","message":"SUCCESS","datas":{"totalSize":0,"pageSize":10,"pageNumber":3,"rows":[]}}
        return ret["datas"]["rows"]
    def getDetail(self,collectorWid):
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/detailCollector"
        body = {
            "collectorWid":collectorWid
        }
        self.session.headers["Content-Type"] = "application/json"
        ret = self.session.post(url,data=json.dumps(body))
        ret = json.loads(ret.text)["datas"]
        url = ret["form"]["formContent"]
        return ret
    def getFormFiled(self,formWid,collectorWid):
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/getFormFields"
        body = {
            "pageSize":50,
            "pageNumber":1,
            "formWid":formWid,
            "collectorWid":collectorWid
        }
        self.session.headers["Content-Type"] = "application/json"
        ret = self.session.post(url,data=json.dumps(body))
        ret = json.loads(ret.text)["datas"]["rows"]
        return ret
    def submitForm(self,formWid,collectWid,schoolTaskWid,rows,address):
        url = "https://"+self.host+"/wec-counselor-collector-apps/stu/collector/submitForm"
        body = {
            "formWid":formWid,
            "collectWid":collectWid,
            "schoolTaskWid":schoolTaskWid,
            "form":rows,
            "address":address
        }
        self.session.headers["Content-Type"] = "application/json"
        #self.session.headers["extension"] = "1" extension
        self.session.headers.update({"Cpdaily-Extension":"7Q881vmOiX7nCAFvYP7Vs0i+EVwTCyEruC4euS0HemoXqaLS/g5g7wovFJVeHrikY1uuQ8gSH5RdZQeCzbsBjk+0DKsec7OiSPZxU3wDCpuvnS12Ikra05lQ B7dFJeUJb/IdN0JXRwTR7xqUfqje7sdXl6C1BRrfwXnWuxmOXh+NXAMxd7t1 UoUMYS2qHw5wNUgO37idqwJjd3Nzfez7XDkRehxMQwCCm7VgcAn6Z741lLzN Mt95ElAtkHp4O26TaCZ5Tmi7fcrZsrNSXQbx1E2HsrjGntoo"})
        ret = self.session.post(url,data=json.dumps(body))
        print(ret.text)
        ret = json.loads(ret.text)
        if ret["message"] != "SUCCESS":
            print("填表失败")
    def autoFill(self,rows):
        #isRequired
        for item in rows:
            index = 0
            while index < len(item["fieldItems"]):
                if item["fieldItems"][index]["isSelected"] == 1:
                    index = index + 1
                else:
                    item["fieldItems"].pop(index)
    def autoComplete(self,address):
        collectList = self.getList()
        print(collectList)
        for item in collectList:
            detail = self.getDetail(item["wid"])
            form = self.getFormFiled(detail["collector"]["formWid"],detail["collector"]["wid"])
            self.autoFill(form)
            #you can edit this form content by your self.
            #autoFill can fill the form with default value.
            self.submitForm(detail["collector"]["formWid"],detail["collector"]["wid"],detail["collector"]["schoolTaskWid"],form,address)

if __name__ == "__main__":
    app = DailyCP()
    while True:
        account = input("请输入帐号：")
        cap = ""
        if app.checkNeedCaptcha(account):
            with io.open("Captcha.png","wb") as file:
                file.write(app.generateCaptcha())
            cap = input("请输入验证码(Captcha.png)：")
        password = input("请输入密码：")
        ret = app.login(account,password,cap)
        if ret == "SUCCESS":
            break
        else:
            print(ret)
    address = input("请输入定位地址：")#"C-137平行宇宙，地球，中国"
    app.autoComplete(address)

#Usage:
#   just edit your id and password.
#   if you are not auster,you need replace the host
#   and run this script
#Author:HuangXu,FenXinYang,ZhouYuYang.
#By:AUST HACKER