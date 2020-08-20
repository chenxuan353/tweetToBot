# -*- coding: UTF-8 -*-
import time
import traceback
import threading
import random
import module.msgStream as msgStream
import config
from module.RSShubApiPackage import RSShubsPackage
from module.RSS import pushlist,rsshubevendeal

from helper import getlogger,data_read_auto,data_save,TempMemory
logger = getlogger(__name__)
"""
用于支持RSS推送的模块
·支持标准RSS协议
"""
#轮询间隔
polling_interval = config.RSS_interval if config.RSS_interval and config.RSS_interval >= 0 else 1
rssapps = RSShubsPackage()

prioritylistconfig = 'RSShubprioritylist.json'
prioritylist = data_read_auto(prioritylistconfig,default={})
defaultpriority = 5 #默认优先级
nowpriority = {}
if config.polling_level and config.polling_level >= 0 and config.polling_level <= 15:
    defaultpriority = int(config.polling_level)

def Priority_set(setvalue:int,userid:str) -> tuple:
    global prioritylist,msgStream
    userid = str(userid)
    if setvalue < 0 or setvalue > 15:
        return (False,'设置值范围错误，范围限定0-15')
    if userid not in nowpriority:
        return (False,'检测列表中不存在此用户！')
    old = str(prioritylist[userid]) if userid in prioritylist else '(未设置)'
    prioritylist[userid] = setvalue
    if userid in nowpriority:
        del nowpriority[userid]
    if not data_save(prioritylistconfig,prioritylist)[0]:
        msgStream.exp_send('推送侦听保存失败',source='推特轮询检测',flag='错误')
    return (True,'设置成功{old}>{new}'.format(old = old,new = setvalue))

def Priority_clear(userid:int = None,screen_name:str = None) -> tuple:
    global prioritylist,msgStream
    if not userid and not screen_name:
        raise Exception('未指定用户')

def Priority_getlist(page:int = 1) -> tuple:
    global prioritylist
    msg = '轮询优先级列表\n优先级，路径'
    page = page - 1
    i = 0
    lll = len(prioritylist)
    if lll == 0:
        return '轮询优先级列表为空'
    if page > int(lll/5):
        page = 0
    for path in prioritylist:
        i += 1
        if i >= page*5 and i < (page+1)*5:
            msg += "{0},{1}".format(prioritylist[path],path)
    msg += '\n当前页{0}/{1} (共{2}个设置)'.format(page+1,int(lll/5)+1,lll)
    return msg

def Priority_canRun(path:str,defaultpriority:int = defaultpriority):
    #检测是否可运行监测
    if path not in nowpriority:
        nowpriority[path] = prioritylist[path] if path in prioritylist else random.randint(1,defaultpriority)
        if path not in prioritylist:
            if not path.startswith('/bilibili'):
                nowpriority[path] += 1
    nowpriority[path] -= 1
    if nowpriority[path] == 0:
        nowpriority[path] = prioritylist[path] if path in prioritylist else defaultpriority
        return True
    return False

def exp_send(msg:str,flag = '警告'):
    logger.warning(msg)
    msgStream.exp_send(msg,source='RSS轮询流',flag=flag)

run_info = {
    'ListenThread':None,
    'isRun':True,
    'keepRun':True,
    'errorCount':0,
    'errorlist':TempMemory('twitterPollingError.json',limit=150),
    'lastRunTime':0,
    'lastErrTime':0
    }
def setStreamOpen(b:bool):
    run_info['keepRun'] = b
    run_info['errorCount'] = 0

def get_updata(trigger : bool = True):
    global rssapps
    #获取更新(会进行优先级处理)
    spylist = pushlist.getSpylist()
    for spy in spylist:
        #优先级判定(不通过则不进行更新收集)
        if not Priority_canRun(spy):
            continue
        res = rssapps.getUpdata(spy)
        if not res[0]:
            logger.error("获取{0}路径更新时错误，{1}".format(spy,res[1]))
            run_info['errorlist'].join((str(spy),res[1]))
            if int(time.time()) - run_info['lastErrTime']  > 300:
                run_info['lastErrTime'] = int(time.time())
                run_info['errorCount'] = 0
            run_info['errorCount'] += 1
            if run_info['errorCount'] > 5:
                #短时间错误次数过高
                exp_send("错误，监测服务异常，请检测后手动启动")
                run_info['keepRun'] = False
                run_info['isRun'] = False
                break
            continue
        updatas = res[1]
        for data in updatas:
            event = rsshubevendeal.bale_event(spy,data)
            rsshubevendeal.deal_event(event)
        time.sleep(0.1)

def Run():
    global polling_interval,rssapps
    defaultUrls = config.RSShub_urls if config.RSShub_urls else []
    if len(defaultUrls) == 0:
        logger.warning("RSShub链接未配置，轮询更新启动失败")
        return
    time.sleep(5)
    logger.info("PollingRSShub 已启动")
    star_interval = time.time()
    count = 0
    try:
        while True:
            if run_info['keepRun']:
                run_info['isRun'] = True
                run_info['lastRunTime'] = time.time()
                count += 1
                if count % 10 == 0:
                    nowtime = time.time()
                    logger.info("RSShub 完整检测，{0}s".format(round(nowtime - star_interval,2)))
                    star_interval = nowtime
                    count = 0
                get_updata()
            else:
                run_info['isRun'] = False
            time.sleep(max(polling_interval,rssapps.getWaitTime()))
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)

#运行推送线程
def runPollingRSShubThread():
    run_info['ListenThread'] = threading.Thread(
        group=None, 
        target=Run, 
        name='PollingRSShubThread_thread', 
        daemon=True
    )
    run_info['ListenThread'].start()
    return run_info
