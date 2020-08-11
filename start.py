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
def testFun():
    even:StandEven = StandEven(
        'CQ','12345','group','233233233',
        'group',False,True,'233233233',StandEven.baleToStandGroupInfo('233233233','测试测试',0,'nmdwsm'),
        '3309003591',StandEven.baleToStandSenduuidInfo('3309003591','nmdwsm','晨轩°'),
        SendMessage('!爪巴 你快爬'),{},{}
        )
    Plugmanagement.eventArrives(even)
    even.setMessage("!233 动啊.jpg")
    Plugmanagement.eventArrives(even)
    even.setMessage("!复读 做无情的复读机")
    Plugmanagement.eventArrives(even)


import botinterface.nonebotstart as nonebotstart
if __name__ == "__main__":
    #加载插件
    info = Plugmanagement.initPlug()
    if config.DEBUG:
        logger.info(info)
    
    #加载nonebot
    if config.nonebot:
        nonebotstart.Run()



