# -*- coding: UTF-8 -*-
import os
from os import path
from helper import check_path,initNonebotLogger
import sys
import nonebot
import module.twitterApi as tweetListener
import module.RSShub_twitter as RSShub_twitter
import module.pollingTwitterApi as pollingTwitterApi
import traceback
import time
import asyncio
import threading

#配置
import config
#日志输出
from helper import getlogger,msgSendToBot
logger = getlogger('START')
'''
nonebot封装的CQHTTP插件
'''
#初始化文件夹
base_path = 'cache'
#推特监听对象
runTweetListener = None
runTweetPlugin = ''

def init():
    global runTweetListener,runTweetPlugin
    allow_start_method = {
        'TweetApi':{
            'Listener':tweetListener.runTwitterApiThread,
            'plugin':'plugins.twitterListener.twitterApi',
        },
        'PollingTweetApi':{
            'Listener':pollingTwitterApi.runPollingTwitterApiThread,
            'plugin':'plugins.twitterListener.twitterApi',
        },
        'RSShub':{
            'Listener':RSShub_twitter.runTwitterListenerThread,
            'plugin':'plugins.twitterListener.RSShub',
        },
        'Twint':{
            'Listener':tweetListener.runTwitterApiThread,
            'plugin':'plugins.twitterListener.twitterApi',
        }
    }
    if config.UPDATA_METHOD not in allow_start_method:
        msg = '配置的更新检测(UPDATA_METHOD)方法不合法：'+str(config.UPDATA_METHOD)
        logger.critical(msg)
        raise Exception(msg)
    runTweetListener = allow_start_method[config.UPDATA_METHOD]['Listener']
    runTweetPlugin = allow_start_method[config.UPDATA_METHOD]['plugin']
    if runTweetListener == None:
        msg = '配置的更新检测(UPDATA_METHOD)方法未实现：'+str(config.UPDATA_METHOD)
        logger.critical(msg)
        raise Exception(msg)


if __name__ == "__main__":
    #初始化
    init()
    #启动线程
    time.sleep(2)
    logger.info('启动推特流...')
    #runTweetListener()
    logger.info('启动nonebot...')
    nonebot.init(config)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'),
        'plugins'
    )
    nonebot.load_plugin(runTweetPlugin) #加载侦听对应的插件
    nonebot.run(host=config.NONEBOT_HOST, port = config.NONEBOT_PORT) #阻塞
    sys.exit() #退出程序(报错后可能存在非守护线程不退出的情况，所以主动退出)



