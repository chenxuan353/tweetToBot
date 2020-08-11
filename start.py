# -*- coding: UTF-8 -*-
import pluginsinterface.Plugmanagement as Plugmanagement
import pluginsinterface.EventHandling as EventHandling
from pluginsinterface.EventHandling import StandEven,SendMessage
#配置
import config
#日志输出
from helper import getlogger
logger = getlogger('START')
"""
启动文件
"""
import botinterface.nonebotstart as nonebotstart
if __name__ == "__main__":
    #加载插件
    info = Plugmanagement.initPlug()
    if config.DEBUG:
        logger.info(info)
    
    #加载nonebot
    if config.nonebot:
        nonebotstart.Run()



