# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import plugLoads,plugRunLoop
import asyncio
#配置
import config
#日志输出
from helper import getlogger
logger = getlogger('START')
"""
启动文件

注：服务器时区设置 timedatectl set-timezone Asia/Shanghai
"""
if __name__ == "__main__":
    #加载插件
    plugLoads()
    #启动事件处理
    plugRunLoop()
    loop = asyncio.get_event_loop()
    #加载nonebot
    if config.nonebot:
        import botinterface.nonebotstart as nonebotstart
        nonebotstart.RunInThread()
    loop.run_forever()


