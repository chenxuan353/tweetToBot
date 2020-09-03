# -*- coding: UTF-8 -*-
import nonebot
import threading
import traceback
import asyncio
import botinterface.nonebotconfig as nonebotconfig
import config
from os import path
from helper import getlogger
logger = getlogger(__name__)
"""
nonebot加载
可异步运行nonebot
*注：曾经尝试异步运行但失败了，某个操作必须在主线程完成
插件文件夹在botinterface.plugins.nonebot下
"""
runinfo = {
    'run':False,
    'threading':None,
    'loop':asyncio.new_event_loop()
}
def Run():
    try:
        logger.info('启动nonebot...')
        nonebot.init(nonebotconfig)
        nonebot.load_plugins(
            path.join(path.dirname(__file__), 'plugins','nonebot_plug'),
            'botinterface.plugins.nonebot_plug'
        )
        nonebot.run(host=config.NONEBOT_HOST, port = config.NONEBOT_PORT)
    except:
        s = traceback.format_exc(limit=5)
        logger.error('nonebot异常！\n'+s)

def __startLoop(runinfo):
    # 设置事件循环
    asyncio.set_event_loop(runinfo['loop'])
    runinfo['loop'].run_forever()
    # asyncio.run_coroutine_threadsafe(__evendeal(runinfo['queue']), runinfo['loop'])

def RunInThread():
    runinfo['threading'] = threading.Thread(
            group=None, 
            target=__startLoop,
            args=(runinfo,),
            name= 'bot_nonebot',
            daemon=True
        )
    runinfo['threading'].start()
    nonebot.init(nonebotconfig)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'plugins','nonebot_plug'),
        'botinterface.plugins.nonebot_plug'
    )
    # nonebot.run(host=nonebotconfig.NONEBOT_HOST, port = nonebotconfig.NONEBOT_PORT)
    task = nonebot.get_bot().run_task(host=config.NONEBOT_HOST, port = config.NONEBOT_PORT)
    asyncio.run_coroutine_threadsafe(task, runinfo['loop'])
    runinfo['run'] = True