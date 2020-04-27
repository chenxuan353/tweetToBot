# -*- coding: UTF-8 -*-
import nonebot
from os import path
import module.twitter as tweetListener
#import module.twitter_test as tweetListener_test
import config
'''
nonebot封装的CQHTTP插件
'''
if __name__ == "__main__":
    nonebot.init(config)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'),
        'plugins'
    )
    #启动推特监听流
    tweetListener.Run()
    nonebot.run(host='127.0.0.1', port = 8190)
