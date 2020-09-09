# -*- coding: UTF-8 -*-
from helper import getlogger,TokenBucket,TempMemory
import tweepy
import config
import threading
import time
import traceback
import random
logger = getlogger(__name__)

# 应用程序匿名访问
class TwitterAppApiPackage:
    def __init__(self,consumer_key:str,consumer_secret:str):
        # 应用程序限制窗口
        self.apibucket = {
            'users_timeline':TokenBucket(1.3,1,0.0),# 用户时间线
            'users_show':TokenBucket(0.9,2,0.1),# 用户检索
            'users_lookup':TokenBucket(0.3,2,0.1),# 多用户检索
            # 'statuses_show':TokenBucket(0.45,450,0.5),# 单推文检索
            'statuses_lookup':TokenBucket(0.3,2,0.1),# 多推文检索
        }
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.api = tweepy.API(self.auth, proxy=config.api_proxy)
    def users_timeline(self,autoid = None,user_id = None,screen_name = None,since_id = None):
        if not self.apibucket['users_timeline'].consume(1):
            return (False,'速率限制！')
        try:
            if autoid:
                tweets = self.api.user_timeline(id = autoid,since_id = since_id,tweet_mode = 'extended')
            elif user_id:
                tweets = self.api.user_timeline(user_id = user_id,tweet_mode = 'extended')
            elif screen_name:
                tweets = self.api.user_timeline(screen_name = screen_name,tweet_mode = 'extended')
            else:
                return (False,'参数错误')
        except tweepy.error.TweepError as e:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            logger.warning(f"api错误代码：{e.api_code}")
            try:
                if e.api_code == None:
                    return (True,[])
            except:
                return (True,[])
            return (False,'tweepy错误！')
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
        except tweepy.error.TweepError as e:
            logger.warning(e)
            return (False,'tweepy错误！',e.response.status_code)
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
                tweets = self.api.statuses_lookup([id],tweet_mode = 'extended')
            elif ids:
                tweets = self.api.statuses_lookup(ids,tweet_mode = 'extended')
            else:
                return (False,'参数错误')
        except tweepy.error.TweepError as e:
            logger.warning(e)
            return (False,'tweepy错误！',e.response.status_code)
        except:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            return (False,'程序异常')
        return (True,tweets)

class PollingTwitterApps:
    allowFunname = {
        'users_timeline':1.3,# 用户时间线
        'users_show':0.9,# 用户检索
        'users_lookup':0.3,# 多用户检索
        # 'statuses_show':0.45,# 单推文检索
        'statuses_lookup':0.3,# 多推文检索
    }
    waitTime = {
        'users_timeline':0,# 用户时间线
        'users_show':0,# 用户检索
        'users_lookup':0,# 多用户检索
        # 'statuses_show':0.45,# 单推文检索
        'statuses_lookup':0,# 多推文检索
    }
    def __init__(self,consumers:list):
        self.consumers = consumers.copy()
        self.apps = [] # 应用列表
        self.lasti = 0
        for consumer in self.consumers:
            self.apps.append(
                TwitterAppApiPackage(consumer[0],consumer[1])
            )
        appl = len(self.apps)
        for key in self.waitTime:
            self.waitTime[key] = int((1/(self.allowFunname[key]*appl))*100)/100 + 0.5
    # 获取可用的应用密钥，没有可用的密钥时返回None
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
    # 获取最短可用时间
    def getWaitTime(self,funname:str) -> TwitterAppApiPackage:
        return self.waitTime[funname]
    def hasApp(self) -> bool:
        return self.apps != []