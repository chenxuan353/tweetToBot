# -*- coding: UTF-8 -*-
import tweepy
import traceback
import time
import threading
import module.twitter as twitter
import module.msgStream as msgStream
# 引入配置
import config
from helper import getlogger,data_read_auto,data_save,TokenBucket
logger = getlogger(__name__)
# 引入推送列表、推送处理模版

'''
推特API监听更新的实现类
'''
pushmerge = True # 推送合并
tokenbucket = TokenBucket(3,30) # 流式限速检查
# 推特监听者
class MyStreamListener(tweepy.StreamListener):
    # 错误处理
    def on_error(self, status_code):
        # 推特错误代码https://developer.twitter.com/en/docs/basics/response-codes
        msg = "推特流错误:"+str(status_code)
        logger.critical(msg)
        msgStream.exp_send(msg)
        # 返回False结束流
        return False
    # 开始链接监听
    def on_connect(self):
        msg = "推特流已就绪"
        logger.info(msg)
        msgStream.exp_send(msg)
    # 断开链接监听
    def on_disconnect(self, notice):
        msg = "推特流已断开链接"
        logger.info(msg)
        msgStream.exp_send(msg)
        return False
    # 推特事件监听
    def on_status(self, status):
        global pushmerge
        try:
            # 提交status
            twitter.submitStatus(status,pushmerge)
        except:
            s = traceback.format_exc(limit=5)
            logger.error(s)

# 推特认证
auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
# 获取API授权
api = tweepy.API(auth, proxy=config.api_proxy)

# 安装测试列表
# test_install_push_list()
# 创建监听对象
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
listenlist = list(data_read_auto(listenlistconfig,default=['1109751762733301760']))
def addListen(userid:str) -> tuple:
    global listenlist,listenlistconfig
    userid = str(userid)
    if userid in listenlist:
        return (False,'用户已存在！')
    listenlist.append(userid)
    if not data_save(listenlistconfig,listenlist)[0]:
        exp_send('推送侦听保存失败')
    return (True,"添加成功！")
def delListen(userid:str) -> tuple:
    global listenlist,listenlistconfig
    userid = str(userid)
    if userid not in listenlist:
        return (False,'侦听中不存在此用户！')
    if len(listenlist) == 1:
        return (False,'禁止全部移除，辅助监听至少需要一个监听对象。')
    listenlist.remove(userid)
    if not data_save(listenlistconfig,listenlist)[0]:
        exp_send('推送侦听保存失败')
    return (True,'移除成功')
def getListenList(page:int = 0) -> tuple:
    global listenlist
    msg = '推送流侦听列表'
    lll = len(listenlist)
    if lll == 0:
        return '推送流侦听列表为空'
    i = 0
    for userid in listenlist:
        if i >= page*5 and i < (page+1)*5:
            userinfo = twitter.tweetcache.getUserInfo(userid = userid)
            if userinfo is not None:
                msg += '\n{0}({1}),{2}'.format(userinfo['screen_name'],userinfo['name'],userinfo['id'])
            else:
                msg += '\n无缓存(不明),{0}'.format(userid)
        i += 1
    msg += '\n当前页{0}/{1} (总{2})'.format(page,int(lll/5),lll)
    return msg

# 维持侦听流运行
def Run():
    time.sleep(7)
    logger.info("StreamTweetApi 已启动")
    # 五分钟内至多重启五次
    run_info['isRun'] = True
    run_info['lastRunTime'] = int(time.time())
    run_info['errorCount'] = 0
    while True:
        while not run_info['keepRun']:
            time.sleep(3) # 保持运行标记为否时堵塞执行
        if run_info['errorCount'] > 5:
            exp_send('重试次数过多，停止重试...')
            while run_info['errorCount'] > 5:
                time.sleep(1) # 错误次数达到上限时暂停运行
        if run_info['errorCount'] > 0:
            exp_send('推特流异常正在尝试重启，'+'第 ' + str(run_info['errorCount']) + ' 次尝试...')
        try:
            # 创建监听流
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
        if run_info['errorCount'] > 0 and int(time.time()) - run_info['lastRunTime'] > 300:
            run_info['lastRunTime'] = int(time.time()) # 两次重启间隔五分钟以上视为重启成功
            run_info['lastErrTime'] = int(time.time()) # 两次重启间隔五分钟以上视为重启成功
            run_info['errorCount'] = 0 # 重置计数
        run_info['errorCount'] = run_info['errorCount'] + 1

# 运行推送线程
def runTwitterApiThread():
    # 推特流维护线程
    run_info['ListenThread'] = threading.Thread(
        group=None, 
        target=Run, 
        name='ListenThread',
        daemon=True
    )
    run_info['ListenThread'].start()
    return run_info