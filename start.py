# -*- coding: UTF-8 -*-
import nonebot
import module.twitter as tweetListener
import traceback
import time
import asyncio
from os import path
from concurrent.futures import ThreadPoolExecutor
#import module.twitter_test as tweetListener_test
#配置
import config
#日志输出
from helper import log_print
#线程池
threads = ThreadPoolExecutor(max_workers=10,thread_name_prefix='MAIN')
'''
nonebot封装的CQHTTP插件
'''

def run_tewwtlistener(new_loop):
    asyncio.set_event_loop(new_loop)
    try:
        tweetListener.Run()
    except (ConnectionError,TimeoutError):
        log_print(0,"推特监听流连接失败！\n"+errorMsg)
    except:
        log_print(0,'推特监听异常')
        s = traceback.format_exc(limit=10)
        log_print(2,s)
def run_nonebot(new_loop):
    asyncio.set_event_loop(new_loop)
    try:
        nonebot.init(config)
        nonebot.load_plugins(
            path.join(path.dirname(__file__), 'plugins'),
            'plugins'
        )
        nonebot.run(host='127.0.0.1', port = 8190)
    except:
        log_print(1,'BOT状态异常')
        s = traceback.format_exc(limit=10)
        log_print(2,s)


if __name__ == "__main__":
    #启动线程
    log_print(4,'启动nonebot...')
    new_loop = asyncio.new_event_loop()
    Future = threads.submit(run_nonebot,new_loop)
    
    time.sleep(2)
    log_print(4,'启动推特流...')
    new_loop = asyncio.new_event_loop()
    Future = threads.submit(run_tewwtlistener,new_loop)
    
    loop = asyncio.get_event_loop()
    log_print(4,'维持主线程运行...')
    loop.run_forever()


