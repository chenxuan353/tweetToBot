# **可提供一对多转推服务的bot后端**

目前仍然处于测试状态

已经可用，对大部分异常进行了处理(宕机也是宕一半.jpg)

依赖的模块 nonebot

pip安装nonebot

将config_example.py改名为config.py并填写内部的配置信息

然后就可以用start.py启动项目了

仅支持 Python 3.7+ 及 CQHTTP 插件 v4.8+。



## 推特监测支持的命令：

注:命令前注意添加前缀，以及注意命令权限要求

### delall

别名：这里单推bot

权限：超级管理员,艾特bot

功能：移除当前私聊/群的所有监测

### getpushlist

别名：DD列表

权限：无限制

功能：获取当前私聊/群的监测列表

![image-20200428114040218](readme\image-20200428114040218.png)

### getuserinfo 推特用户ID/用户名(非昵称)

别名：查询推特用户

权限：超级管理员,艾特bot

功能：获取当前私聊/群的监测列表

例：getuserinfo shiranuiflare

![image-20200428113938381](readme\image-20200428113938381.png)

### addone 推特用户ID/用户名(非昵称) 昵称 描述

别名：给俺D一个

权限：超级管理员,艾特bot

功能：添加一个用户到本群监测

例如：给俺D一个 shirakamifubuki 吹雪 我永远喜欢小狐狸

![image-20200428113806819](readme\image-20200428113806819.png)

### delone 推特用户ID/用户名(非昵称)

别名：我不想D了

权限：超级管理员,艾特bot

功能：移除一个本群监测的用户