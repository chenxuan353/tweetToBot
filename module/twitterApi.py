# -*- coding: UTF-8 -*-
import tweepy
import traceback
import time
import threading
import module.twitter as twitter
import module.msgStream as msgStream
#引入配置
import config
from helper import getlogger,data_read_auto,data_save,TokenBucket
logger = getlogger(__name__)
#引入推送列表、推送处理模版

'''
推特API监听更新的实现类
'''
pushmerge = True #推送合并
tokenbucket = TokenBucket(3,30) #流式限速检查
#推特监听者
class MyStreamListener(tweepy.StreamListener):
    #错误处理
    def on_error(self, status_code):
        #推特错误代码https://developer.twitter.com/en/docs/basics/response-codes
        msg = "推特流错误:"+str(status_code)
        logger.critical(msg)
        msgStream.exp_send(msg)
        #返回False结束流
        return False
    #开始链接监听
    def on_connect(self):
        msg = "推特流已就绪"
        logger.info(msg)
        msgStream.exp_send(msg)
    #断开链接监听
    def on_disconnect(self, notice):
        msg = "推特流已断开链接"
        logger.info(msg)
        msgStream.exp_send(msg)
        return False
    #推特事件监听
    def on_status(self, status):
        global pushmerge
        try:
            #提交status
            twitter.submitStatus(status,pushmerge)
        except:
            s = traceback.format_exc(limit=5)
            logger.error(s)

#推特认证
auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
#获取API授权
api = tweepy.API(auth, proxy=config.api_proxy)

#安装测试列表
#test_install_push_list()
#创建监听对象
myStreamListener = MyStreamListener()

run_info = {
    'ListenThread':None,
    'keepRun':True,
    'isRun':False,
    'errorCount':0,
    'lastRunTime':0,
    'lastErrTime':0,
    'apiStream':None
}
def setStreamOpen(b:bool):
    run_info['errorCount'] = 0
    run_info['keepRun'] = b
    run_info['apiStream'].running = b
def resetError():
    run_info['errorCount'] = 0

def exp_send(msg:str,flag = '警告'):
    logger.warning(msg)
    msgStream.exp_send(msg,source='推特API流',flag=flag)

listenlistconfig = 'twitterlistenlist.json'
listenlist = list(data_read_auto(listenlistconfig,default=[]))
def addListen(userid:int = None,screen_name:str = None) -> tuple:
    global listenlist
    if not userid and not screen_name:
        raise Exception('未指定用户')
    #添加侦听，添加成功返回用户信息
    userinfo = twitter.tweetcache.getUserInfo(userid = userid,screen_name= screen_name)
    if not userinfo:
        return (False,msgStream.SendMessage('此用户不在缓存中，无法操作'))
    if userinfo['id_str'] in listenlist:
        return (False,msgStream.SendMessage('用户已存在！'))
    listenlist.append(userinfo['id_str'])
    if not data_save(listenlistconfig,listenlist)[0]:
        exp_send('推送侦听保存失败')
    msg = twitter.tweetevendeal.userinfoToStr(userinfo)
    return (True,msg.insert(msg.baleTextObj("添加成功！\n")))
def delListen(userid:int = None,screen_name:str = None) -> tuple:
    global listenlist
    if not userid and not screen_name:
        raise Exception('未指定用户')
    #添加侦听，添加成功返回用户信息
    userinfo = twitter.tweetcache.getUserInfo(userid = userid,screen_name= screen_name)
    if not userinfo:
        if not userid:
            return (False,msgStream.SendMessage('此用户不在缓存中，无法使用用户名操作'))
    if str(userid) not in listenlist:
        return (False,msgStream.SendMessage('侦听中不存在此用户！'))
    listenlist.remove(str(userid))
    if not data_save(listenlistconfig,listenlist)[0]:
        exp_send('推送侦听保存失败')
    return (True,msgStream.SendMessage('移除成功'))
def getListenList(page:int = 0) -> tuple:
    global listenlist
    msg = msgStream.SendMessage('推送流侦听列表')
    lll = len(listenlist)
    if lll == 0:
        return msgStream.SendMessage('推送流侦听列表为空')
    i = 0
    for userid in listenlist:
        i += 1
        if i > page*5 and i % 5 == 0:
            userinfo = twitter.tweetcache.getUserInfo(userid = userid)
            if userinfo:
                msg.append(msg.baleTextObj('\n{0}({1}),{2}'.format(userinfo['screen_name'],userinfo['name'],userinfo['id'])))
            else:
                msg.append(msg.baleTextObj('\n用户不在缓存中(不明),{0}'.format(userid)))
    
    msg.append('\n当前页{0}/total (总{1})'.format(page,lll/5,lll))
    return msg

#维持侦听流运行
def Run():
    #五分钟内至多重启五次
    run_info['isRun'] = True
    run_info['lastRunTime'] = int(time.time())
    run_info['errorCount'] = 0
    while True:
        while not run_info['keepRun']:
            time.sleep(3) #保持运行标记为否时堵塞执行
        if run_info['errorCount'] > 5:
            exp_send('重试次数过多，停止重试...')
            while run_info['error_cout'] > 5:
                time.sleep(1) #错误次数达到上限时暂停运行
        if run_info['error_cout'] > 0:
            exp_send('推特流异常正在尝试重启，'+'第 ' + str(run_info['error_cout']) + ' 次尝试...')
        try:
            #创建监听流
            run_info['apiStream'] = tweepy.Stream(auth = api.auth, listener=myStreamListener)
            run_info['apiStream'].filter(follow=listenlist,is_async=False)
        except:
            s = traceback.format_exc(limit=10)
            logger.error(s)
            exp_send('推特监听异常,将在10秒后尝试重启...')
            time.sleep(10)
        else:
            run_info['isRun'] = False
            exp_send('推特流被主动停止...')
            logger.info('推特流被主动停止')
        if run_info['error_cout'] > 0 and int(time.time()) - run_info['last_reboot'] > 300:
            run_info['last_reboot'] = int(time.time()) #两次重启间隔五分钟以上视为重启成功
            run_info['error_cout'] = 0 #重置计数
        run_info['error_cout'] = run_info['error_cout'] + 1

#运行推送线程
def runTwitterApiThread():
    time.sleep(5)
    logger.info("StreamTweetApi 已启动")
    #推特流维护线程
    run_info['ListenThread'] = threading.Thread(
        group=None, 
        target=Run, 
        name='ListenThread',
        daemon=True
    )
    run_info['ListenThread'].start()
    return run_info