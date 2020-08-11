import nonebot
import threading
import traceback
import botinterface.nonebotconfig as nonebotconfig
from os import path
from helper import getlogger
logger = getlogger(__name__)
"""
nonebot加载
可异步运行nonebot
*注：曾经尝试异步运行但失败了，某个操作必须在主线程完成
插件文件夹在botinterface.plugins.nonebot下
"""

def Run():
    try:
        logger.info('启动nonebot...')
        nonebot.init(nonebotconfig)
        nonebot.load_plugins(
            path.join(path.dirname(__file__), 'plugins','nonebot_plug'),
            'botinterface.plugins.nonebot_plug'
        )
        nonebot.run(host=nonebotconfig.NONEBOT_HOST, port = nonebotconfig.NONEBOT_PORT)
    except:
        s = traceback.format_exc(limit=5)
        logger.error('nonebot异常！\n'+s)
def RunThread():
    threading.Thread(
            group=None, 
            target=Run, 
            name='bot_nonebot',
            daemon=True
        )
