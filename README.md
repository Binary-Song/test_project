# FuckDailyCP

#### 简介

今日校园自动健康打卡脚本。

可以挂服务器上定时自动打卡。

健康的人可以用一下（雾）。

![](doc/img.png)

#### 使用说明

```bash
python3 DailyCP.py
```

根据提示输入账户密码即可，有手就行。

#### 挂服务器提示

自己先建立一个文件里面存了帐号和密码，然后创建定时任务。

```bash
cat /root/FuckDailyCP/account | python3 /root/FuckDailyCP/DailyCP.py >> /root/FuckDailyCP/history.log
```

#### At Last

白嫖不给Star的人最恶心了。