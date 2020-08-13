# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import plugLoads
#配置
import config
#日志输出
from helper import getlogger
logger = getlogger('START')
"""
启动文件
"""
if __name__ == "__main__":
    #加载插件
    plugLoads()
    #加载nonebot
    if config.nonebot:
        import botinterface.nonebotstart as nonebotstart
        nonebotstart.Run()



