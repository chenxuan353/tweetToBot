# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import plugLoads,plugRunLoop
from module.twitter import runTwitterPushThread
from module.pollingTwitterApi import runPollingTwitterApiThread
from module.twitterApi import runTwitterApiThread
from module.pollingRSShub import runPollingRSShubThread
import asyncio
#配置
import config
#日志输出
from helper import getlogger
logger = getlogger('START')
"""
启动文件

注：服务器时区设置 timedatectl set-timezone Asia/Shanghai
注：服务器中文环境设置 export LANG="zh_CN.UTF-8"
"""
if __name__ == "__main__":
    #加载插件
    plugLoads()
    #启动事件处理
    plugRunLoop()
    loop = asyncio.get_event_loop()
    #启动推送监听
    if config.twitterpush:
        runTwitterPushThread()
        runPollingTwitterApiThread()
        if config.twitterStream:
            runTwitterApiThread()
    if config.RSS_open:
        runPollingRSShubThread()
    #加载nonebot
    if config.nonebot:
        import botinterface.nonebotstart as nonebotstart
        #nonebotstart.RunInThread()
        nonebotstart.Run()
    loop.run_forever()


