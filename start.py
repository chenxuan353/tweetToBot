# -*- coding: UTF-8 -*-
import nonebot
import module.twitter as tweetListener
import traceback
import time
import asyncio
import os
import threading
from os import path

#配置
import config
#日志输出
from helper import log_print,keepalive

'''
nonebot封装的CQHTTP插件
'''
def init():
    base_path = 'cache/'
    file_path = 'config'
    if not os.path.exists(base_path + file_path):
        log_print(4,'文件夹' + base_path + file_path + '不存在，重新建立')
        #os.mkdir(file_path)
        os.makedirs(base_path + file_path)

def reboot_tewwtlistener():
    keepalive['reboot_tewwtlistener'] = False
    if keepalive['reboot_tweetListener_cout'] > 5:
        log_print(6,'重试次数过多，停止重试...')
        keepalive['tewwtlistener_alive'] = False
        return
    keepalive['reboot_tweetListener_cout'] = keepalive['reboot_tweetListener_cout'] + 1
    log_print(6,'尝试重启推特流，'+'进行第 ' + str(keepalive['reboot_tweetListener_cout']) + ' 次尝试...')

    keepalive['tweetListener_threads'] = threading.Thread(
        group=None, 
        target=run_tewwtlistener, 
        name='tweetListener_threads', 
        daemon=True
    )
    keepalive['tweetListener_threads'].start()

def run_tewwtlistener():
    keepalive['tewwtlistener_alive'] = True
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        tweetListener.Run()
    except:
        log_print(0,'推特监听异常,将在10秒后尝试重启...')
        s = traceback.format_exc(limit=10)
        log_print(2,s)
        time.sleep(10)
        reboot_tewwtlistener()
        return

def run_nonebot():
    new_loop = asyncio.new_event_loop()
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

def nonebot_threads_run():
    keepalive['nonebot_threads'] = threading.Thread(
        group=None, 
        target=run_nonebot, 
        name='nonebot_threads', 
        daemon=True
    )
    keepalive['nonebot_threads'].start()

def tweetListener_threads_run():
    keepalive['tweetListener_threads'] = threading.Thread(
        group=None, 
        target=run_tewwtlistener, 
        name='tweetListener_threads', 
        daemon=True
    )
    keepalive['tweetListener_threads'].start()

async def DealAndKeepAlive():
    while True:
        await asyncio.sleep(1)
        if keepalive['reboot_tewwtlistener'] == True:
            reboot_tewwtlistener()


if __name__ == "__main__":
    #初始化
    init()
    #启动线程
    log_print(4,'启动nonebot...')
    nonebot_threads_run()
    time.sleep(2)
    log_print(4,'启动推特流...')
    tweetListener_threads_run()
    loop = asyncio.get_event_loop()
    log_print(4,'维持主线程运行...')
    loop.run_until_complete(DealAndKeepAlive())


