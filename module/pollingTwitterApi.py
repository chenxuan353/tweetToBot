# -*- coding: UTF-8 -*-
import time
import traceback
import threading
import module.msgStream as msgStream
import module.twitter as twitter
from module.TwitterAppApiPackage import TwitterAppApiPackage, PollingTwitterApps
from load_config import config
from helper import getlogger, data_read_auto, data_save, TempMemory
logger = getlogger(__name__)
"""
推特API的轮询模式
仅使用应用程序验证
"""
# 轮询间隔
polling_interval = config['polling_interval'] if config['polling_interval'] and config['polling_interval'] >= 0 else 1
ptwitterapps = PollingTwitterApps(config['polling_consumers'])

prioritylistconfig = 'twitterprioritylist.json'
prioritylist = data_read_auto(prioritylistconfig, default={})
defaultpriority = 5  # 默认优先级
nowpriority = {}
if config['polling_level'] and config['polling_level'] >= 0 and config['polling_level'] <= 15:
    defaultpriority = int(config['polling_level'])


def Priority_set(setvalue: int, userid: int) -> tuple:
    global prioritylist, msgStream
    userid = str(userid)
    if setvalue < 0 or setvalue > 15:
        return (False, '设置值范围错误，范围限定0-15')
    if userid not in nowpriority:
        return (False, '检测列表中不存在此用户！')
    old = str(prioritylist[userid]) if userid in prioritylist else '(未设置)'
    prioritylist[userid] = setvalue
    if userid in nowpriority:
        del nowpriority[userid]
    if not data_save(prioritylistconfig, prioritylist)[0]:
        msgStream.exp_send('推送侦听保存失败', source='推特轮询检测', flag='错误')
    return (True, '设置成功{old}>{new}'.format(old=old, new=setvalue))


def Priority_clear(userid: int) -> tuple:
    global prioritylist, msgStream
    userid = str(userid)
    if userid not in nowpriority:
        return (False, '优先级列表中不存在此用户！')
    del prioritylist[userid]
    if userid in nowpriority:
        del nowpriority[userid]
    if not data_save(prioritylistconfig, prioritylist)[0]:
        msgStream.exp_send('推送侦听保存失败', source='推特轮询检测', flag='错误')
    return (True, '已清空优先级设置')


def Priority_getlist(page: int = 1) -> str:
    global prioritylist
    msg = '轮询优先级列表\n优先级，用户名，用户UUID'
    page = page - 1
    i = 0
    lll = len(prioritylist)
    if lll == 0:
        return '轮询优先级列表为空'
    if page > int(lll / 5):
        page = 0
    for userid in prioritylist:
        i += 1
        if i >= page * 5 and i < (page + 1) * 5:
            userinfo = twitter.tweetcache.getUserInfo(userid=userid)
            if userinfo:
                msg += '\n{0},{1}({2}),{3}'.format(prioritylist[userid],
                                                   userinfo['screen_name'],
                                                   userinfo['name'],
                                                   userinfo['id'])
            else:
                msg += '\n{0},(无缓存_不明),{1}'.format(prioritylist[userid],
                                                   userid)
    msg += '\n当前页{0}/{1} (共{2}个设置)'.format(page + 1, int(lll / 5) + 1, lll)
    return msg


def Priority_canRun(userid: str, defaultpriority: int = defaultpriority):
    # 检测是否可运行监测
    userid = str(userid)
    if userid not in nowpriority:
        nowpriority[userid] = prioritylist[
            userid] if userid in prioritylist else defaultpriority
    nowpriority[userid] -= 1
    if nowpriority[userid] == 0:
        nowpriority[userid] = prioritylist[
            userid] if userid in prioritylist else defaultpriority
        return True
    return False


def exp_send(msg: str, flag='警告'):
    logger.warning(msg)
    msgStream.exp_send(msg, source='推特轮询流', flag=flag)


# 防止更新检测重复
tweetIdCacheConfig = 'PollingTweetIdCache.json'
tweetIdCache = data_read_auto(tweetIdCacheConfig, default={})


def TIC_listUserClear(userid: str) -> bool:
    global tweetIdCache
    userid = str(userid)
    del tweetIdCache[userid]
    if not data_save(tweetIdCacheConfig, tweetIdCache)[0]:
        exp_send('轮询推文ID缓存列表保存失败')
        return False
    return True


def TIC_listUserClearSpylist(Spylist: list) -> bool:
    global tweetIdCache
    for userid in list(tweetIdCache.keys()):
        if str(userid) not in Spylist:
            del tweetIdCache[userid]
    if not data_save(tweetIdCacheConfig, tweetIdCache)[0]:
        exp_send('轮询推文ID缓存列表保存失败')
        return False
    return True


def TIC_listUserHas(userid: str) -> bool:
    global tweetIdCache
    userid = str(userid)
    return userid in tweetIdCache


def TIC_listAdd(userid: str, tweetid: str) -> bool:
    global tweetIdCache, tweetIdCacheConfig
    userid = str(userid)
    if userid not in tweetIdCache:
        tweetIdCache[userid] = []
    if tweetid in tweetIdCache[userid]:
        return False
    tweetIdCache[userid].append(tweetid)
    if len(tweetIdCache[userid]) > 50:
        # 仅缓存50项
        tweetIdCache[userid].pop(0)
    if not data_save(tweetIdCacheConfig, tweetIdCache)[0]:
        exp_send('轮询推文ID缓存列表保存失败')
    return True


run_info = {
    'ListenThread': None,
    'isRun': True,
    'keepRun': True,
    'errorCount': 0,
    'errorlist': TempMemory('twitterPollingError.json', limit=150),
    'lastRunTime': 0,
    'lastErrTime': 0
}


def setStreamOpen(b: bool):
    run_info['keepRun'] = b
    run_info['errorCount'] = 0


def on_status(status):
    twitter.submitStatus(status, source='轮询流')


def get_updata(trigger: bool = True, start=False):
    # 获取更新(会进行优先级处理)
    spylist = twitter.pushlist.getSpylist()
    for spy in spylist:
        # 优先级判定(不通过则不进行更新收集)
        if not Priority_canRun(spy) and not start:
            continue
        # 等待API空闲
        app = ptwitterapps.getAllow('users_timeline')
        while app == None:
            app = ptwitterapps.getAllow('users_timeline')
            time.sleep(ptwitterapps.getWaitTime('users_timeline'))
        # 开始搜索
        res = app.users_timeline(user_id=int(spy))
        if not res[0]:
            logger.error("错误，未搜索到" + str(spy) + "的时间线数据")
            run_info['errorlist'].join((str(spy), res[1]))
            if int(time.time()) - run_info['lastErrTime'] > 300:
                run_info['lastErrTime'] = int(time.time())
                run_info['errorCount'] = 0
            run_info['errorCount'] += 1
            if run_info['errorCount'] > 9:
                # 短时间错误次数过高
                exp_send("错误，监测服务异常，请检测后手动启动")
                run_info['keepRun'] = False
                run_info['isRun'] = False
                break
            continue
        statuss = res[1]
        if not TIC_listUserHas(spy):
            # 初次监测不推送
            logger.info("初次检测:" + str(spy))
            trigger = False

        for i in range(len(statuss) - 1, -1, -1):
            cache = TIC_listAdd(spy, statuss[i].id)
            if not trigger:
                # 不触发时仅缓存推文
                res = twitter.tweetevendeal.dealSourceData(statuss[i],
                                                           checkuser=True)
                twitter.tweetcache.addTweetToCache(res['tweetinfo'])
            # 推文不存在于缓存时推送
            if cache:
                if trigger:
                    on_status(statuss[i])
            elif trigger:
                try:
                    userinfo = twitter.tweetstatusdeal.get_userinfo(
                        statuss[i].user)
                    userevens = twitter.tweetevendeal.checkUserInfoUpdata(
                        userinfo)
                    for usereven in userevens:
                        twitter.on_even(usereven, source='轮询-用户更新事件')
                except:
                    s = traceback.format_exc(limit=5)
                    logger.error(s)


def Run():
    global ptwitterapps, polling_interval
    if not ptwitterapps.hasApp():
        raise Exception("错误，APP密钥对未配置，轮询监测启动失败")
    time.sleep(5)
    logger.info("PollingTweetApi 已启动")
    logger.info("PollingTweetApi 正在执行启动清理")
    TIC_listUserClearSpylist(twitter.pushlist.getSpylist())
    logger.info("PollingTweetApi 启动清理完毕")
    # 使用PollingTweetApi接收更新
    polling_silent_start = not config['polling_silent_start']
    logger.info("PollingTweetApi 启动检测正在运行")
    get_updata(trigger=polling_silent_start, start=True)
    logger.info("PollingTweetApi 启动检测结束")
    time.sleep(polling_interval)
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
                    logger.info("PollingTweetApi 完整检测，{0}s".format(
                        round(nowtime - star_interval, 2)))
                    star_interval = nowtime
                    count = 0
                get_updata()
            else:
                run_info['isRun'] = False
            time.sleep(
                max(polling_interval,
                    ptwitterapps.getWaitTime('users_timeline')))
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)


# 运行推送线程
def runPollingTwitterApiThread():
    run_info['ListenThread'] = threading.Thread(
        group=None, target=Run, name='PollingListenThread_thread', daemon=True)
    run_info['ListenThread'].start()
    return run_info