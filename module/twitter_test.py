import nonebot
import asyncio
import tweepy
import requests
import sys
import traceback
import time
import string
import urllib.request
import os
import time
import module.config as config
from concurrent.futures import ThreadPoolExecutor
#错误上报
bot_error_printID = config.bot_error_printID
#推特认证
spylist = [
    "997786053124616192",
    "1154304634569150464",
    "1200396304360206337",
    "996645451045617664",
    "1024528894940987392",
    "1109751762733301760",
    "979891380616019968",
    "805435112259096576",#我的推特
    "1131691820902100992",#another_test
    "1128877708530790400",#another_test
    "1104692320291549186",#another_test
    "1068883575292944384"#another_test
]
auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
#获取API授权
api = tweepy.API(auth, proxy="127.0.0.1:1080")
#线程池
threads = ThreadPoolExecutor(max_workers=1)
loop = asyncio.get_event_loop()
#日志输出
def log_print(level,str):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    if level == 0:
        print('[致命错误]['+ time_str + ']' +str)
        if bot_error_printID != '':
            requests.post('http://127.0.0.1:5700/send_msg_rate_limited',data={'user_id': bot_error_printID, 'message': time_str})
    elif level == 1:
        print('[!!错误!!]['+ time_str + ']' +str)
    elif level == 2:
        print('[!警告!]['+ time_str + ']'+str)
    elif level == 3:
        print('[调试]['+ time_str + ']'+str)
    elif level == 4:
        print('[信息]['+ time_str + ']'+str)
    elif level == 5:
        print('[值得注意]['+ time_str + ']'+str)
async def log_print_asy(level,str):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    if level == 0:
        print('[致命错误]['+ time_str + ']' +str)
        if bot_error_printID != '':
            requests.post('http://127.0.0.1:5700/send_msg_rate_limited',data={'user_id': bot_error_printID, 'message': time_str})
    elif level == 1:
        print('[!!错误!!]['+ time_str + ']' +str)
    elif level == 2:
        print('[!警告!]['+ time_str + ']'+str)
    elif level == 3:
        print('[调试]['+ time_str + ']'+str)
    elif level == 4:
        print('[信息]['+ time_str + ']'+str)
    elif level == 5:
        print('[值得注意]['+ time_str + ']'+str)

class MyStreamListener(tweepy.StreamListener):
    isrun = False
    #开始链接监听
    def on_connect(self):
        log_print(4,"推送流已就绪")
        self.isrun = True
    #断开链接监听
    def on_disconnect(self, notice):
        log_print(4,"推送流已断开链接")
        self.isrun = False
    def on_status(self, status):
        stype = self.deal_tweet_type(status)
        if stype != 'retweet':
            s = "接收到一个推送信息:"+status.user.name+":"+status.text
            starttime = time.time()
            log_print(4,s)
            bot = nonebot.get_bot()
            #bot.api.send_msg
            bot.sync.send_msg(self_id='1837730674',user_id='3309003591',message=s)
            #threads.submit(asyncio.run,bot.send_msg(self_id='1837730674',user_id='3309003591',message=s))
            log_print(4,'阻塞结束:'+str(time.time()-starttime))
            
            

    def deal_tweet_type(self, status):
        if hasattr(status, 'retweeted_status'):
            return 'retweet' #纯转推
        elif hasattr(status, 'quoted_status'):
            return 'quoted' #推特内含引用推文(带评论转推)
        elif status.in_reply_to_status_id != None:
            return 'reply_to_status' #回复(推特下评论)
        elif status.in_reply_to_screen_name != None:
            return 'reply_to_user' #提及(猜测就是艾特)
        else:
            return 'none' #未分类(估计是主动发推)

#创建监听对象
myStreamListener = MyStreamListener()
#创建监听流
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(follow=spylist,is_async=True)