from module.twitterApi import tweet_event_deal,dealTweetsQueue,push_list
from helper import getlogger,CQsessionToStr,TokenBucket,msgSendToBot
import tweepy
import config
import threading
import time
import traceback
import random
logger = getlogger(__name__)
"""
推特API的轮询模式
仅使用应用程序验证
"""
polling_silent_start = not config.polling_silent_start
polling_interval = int(config.polling_interval)
#引入测试方法
try:
    #on_status
    import dbtest as test
except:
    test = None

#应用程序匿名访问
class TwitterAppApiPackage:
    def __init__(self,consumer_key:str,consumer_secret:str):
        #应用程序限制窗口
        self.apibucket = {
            'users_timeline':TokenBucket(1.5,1500,0.5),#用户时间线
            'users_show':TokenBucket(0.9,900,0.5),#用户检索
            'users_lookup':TokenBucket(0.3,300,0.5),#多用户检索
            #'statuses_show':TokenBucket(0.45,450,0.5),#单推文检索
            'statuses_lookup':TokenBucket(0.3,300,0.5),#多推文检索
        }
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.api = tweepy.API(self.auth, proxy=config.api_proxy)
    def users_timeline(self,autoid = None,user_id = None,screen_name = None,since_id = None):
        if not self.apibucket['users_timeline'].consume(1):
            return (False,'速率限制！')
        try:
            if autoid:
                tweets = self.api.user_timeline(id = autoid,since_id = since_id)
            elif user_id:
                tweets = self.api.user_timeline(user_id = user_id)
            elif screen_name:
                tweets = self.api.user_timeline(screen_name = screen_name)
            else:
                return (False,'参数错误')
        except:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            return (False,'tweepy错误！')
        return (True,tweets)
    def users_show(self,autoid = None,user_id = None,screen_name = None,since_id = None):
        if not self.apibucket['users_show'].consume(1):
            return (False,'速率限制！')
        try:
            if autoid:
                user = self.api.get_user(id = autoid,since_id = since_id)
            elif user_id:
                user = self.api.get_user(user_id = user_id)
            elif screen_name:
                user = self.api.get_user(screen_name = screen_name)
            else:
                return (False,'参数错误')
        except:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            return (False,'tweepy错误！')
        return (True,user)
    def statuses_lookup(self,id = None,ids:list = None):
        if not self.apibucket['statuses_lookup'].consume(1):
            return (False,'速率限制！')
        try:
            if id:
                tweets = self.api.statuses_lookup([id])
            elif ids:
                tweets = self.api.statuses_lookup(ids)
            else:
                return (False,'参数错误')
        except:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            return (False,'程序异常')
        return (True,tweets)


class PollingTwitterApps:
    allowFunname = {
        'users_timeline':1.5,#用户时间线
        'users_show':0.9,#用户检索
        'users_lookup':0.3,#多用户检索
        #'statuses_show':0.45,#单推文检索
        'statuses_lookup':0.3,#多推文检索
    }
    def __init__(self,consumers:list):
        self.consumers = consumers.copy()
        self.apps = [] #应用列表
        self.lasti = 0
        for consumer in self.consumers:
            self.apps.append(
                TwitterAppApiPackage(consumer[0],consumer[1])
            )
    #获取可用的应用密钥，没有可用的密钥时返回None
    def getAllow(self,funname:str) -> TwitterAppApiPackage:
        if funname not in self.allowFunname:
            raise Exception('不被允许的方法')
        appl = len(self.apps)
        for i in range(0,appl):
            app = self.apps[(self.lasti + i)%appl]
            if app.apibucket[funname].canConsume(1):
                self.lasti = (self.lasti + i)%appl + 1
                return app
        return None
    def hasApp(self) -> bool:
        return self.apps != []

ptwitterapps = PollingTwitterApps(config.polling_consumers)

run_info = {
    'DealDataThread':None,
    'queque':dealTweetsQueue,
    'Thread':None,
    'keepRun':True,
    'lasterror':int(time.time()),
    'error':0,
}
def setStreamOpen(b:bool):
    run_info['keepRun'] = b


def init():
    if not ptwitterapps.hasApp():
        raise Exception("错误，APP密钥对未配置，轮询监测启动失败")
    #读取推送侦听配置
    res = push_list.readPushList()
    if res[0] == True:
        logger.info('侦听配置读取成功')
    else:
        logger.error('侦听配置读取失败:' + res[1])

def on_status(status):
    try:
        #重新组织推特数据
        tweetinfo = tweet_event_deal.deal_tweet(status)
        #只有值得关注的推文才会推送处理,降低处理压力(能降一大截……)
        if tweetinfo['tweetNotable']:
            try:
                dealTweetsQueue.put(tweetinfo,timeout=15)
            except:
                s = traceback.format_exc(limit=5)
                msgSendToBot(logger,'推特监听处理队列溢出，请检查队列！')
                logger.error(s)
        if test != None:
            test.on_status(tweetinfo,status)
    except:
        s = traceback.format_exc(limit=5)
        logger.error(s)

def get_updata(trigger : bool = True):
    spylist = push_list.spylist
    interval = polling_interval
    for spy in spylist:
        app = ptwitterapps.getAllow('users_timeline')
        while app == None:
            logger.warning('触发轮询上限，建议增加轮询间隔')
            app = ptwitterapps.getAllow('users_timeline')
            time.sleep(1)
        res = app.users_timeline(user_id=int(spy))
        if not res[0]:
            logger.error("错误，未搜索到"+str(spy)+"的时间线数据")
            if run_info['lasterror'] - int(time.time()) > 300:
                run_info['lasterror'] = int(time.time())
                run_info['error'] = 0
            run_info['error'] = run_info['error'] + 1
            if run_info['error'] > 5:
                #短时间错误次数过高
                msgSendToBot(logger,"错误，监测服务异常，请检测后手动启动")
                run_info['keepRun'] = False
                break
            continue
        statuss = res[1]
        if not tweet_event_deal.hasUserTSInCache(spy):
            #初次监测不推送
            logger.info("初次检测:"+spy)
            trigger = False
        for i in range(len(statuss)-1,-1,-1):
            res = tweet_event_deal.tryGetTweet(statuss[i].id,user_id=spy)
            if not res:
                if trigger:
                    on_status(statuss[i])
                else:
                    #组织推特数据
                    tweetinfo = tweet_event_deal.deal_tweet(statuss[i])
                    #缓存处理
                    tweet_event_deal.bale_event(tweetinfo['type'],tweetinfo['trigger_user'],tweetinfo)
        itv = round(random.uniform(0,interval),2)
        interval = interval - itv
        interval = max(0.5,interval)
        time.sleep(itv)
    time.sleep(interval)
            

def Run():
    global polling_interval
    init()
    #使用PollingTweetApi接收更新
    logger.info("PollingTweetApi")
    time.sleep(5)
    logger.info("PollingTweetApi 启动检测正在运行")
    itv = polling_interval
    polling_interval = 1
    get_updata(trigger = polling_silent_start)
    polling_interval = itv
    logger.info("PollingTweetApi 启动检测结束")
    time.sleep(polling_interval)
    while True:
        if run_info['keepRun']:
            logger.info("PollingTweetApi 自动检测")
            get_updata()
        
        


#处理推特数据(独立线程)
def dealTweetData():
    while True:
        tweetinfo = run_info['queque'].get()
        try:
            #推送事件处理，输出到酷Q
            eventunit = tweet_event_deal.bale_event(tweetinfo['type'],tweetinfo['trigger_user'],tweetinfo)
            tweet_event_deal.deal_event(eventunit)
            #控制台输出
            tweet_event_deal.statusPrintToLog(tweetinfo)
        except:
            s = traceback.format_exc(limit=5)
            logger.warning(s)
        run_info['queque'].task_done()

#运行推送线程
def runPollingTwitterApiThread():
    run_info['Thread'] = threading.Thread(
        group=None, 
        target=Run, 
        name='Polling_tweetListener_thread', 
        daemon=True
    )
    run_info['DealDataThread'] = threading.Thread(
        group=None, 
        target=dealTweetData, 
        name='Polling_tweetListener_DealDataThread',
        daemon=True
    )
    run_info['Thread'].start()
    run_info['DealDataThread'].start()
    return run_info