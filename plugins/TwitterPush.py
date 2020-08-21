from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,PlugMsgTypeEnum,PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

from pluginsinterface.PluginLoader import SendMessage
from module.twitter import tweetcache,pushlist,tweetstatusdeal,tweetevendeal,encode_b64,decode_b64
from module.twitterApi import setStreamOpen as apisetStreamOpen,addListen,delListen,getListenList
from module.pollingTwitterApi import ptwitterapps,setStreamOpen as pollingsetStreamOpen

from module.pollingTwitterApi import Priority_getlist,Priority_set
import time
import config
import functools
from helper import getlogger
logger = getlogger(__name__)
"""
    推特推送管理
"""

@plugRegistered('推特推送管理','twitterPush')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'chenxuan',#插件作者  
        'des':'用于管理推特推送的插件'#插件描述  
        }
@on_plugloaded()
def _(plug:PluginsManage):
    if plug:
        #if not config.twitterpush:
        #    plug.switchPlug(False) #关闭插件
        #注册权限
        plug.registerPerm('manage',des = '管理权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('manageuse',des = '使用的管理权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('use',des = '使用权限',defaultperm=PlugMsgTypeEnum.private)
        plug.registerPerm('manageself',des = '管理自己的权限',defaultperm=PlugMsgTypeEnum.allowall)
        plug.registerPerm('cacheinfo',des = '获取缓存信息的权限',defaultperm=PlugMsgTypeEnum.allowall)
        #plug.registerPerm('apiuse',des = '使用API获取数据的权限',defaultperm=PlugMsgTypeEnum.allowall)

@on_preprocessor()
async def _(session:Session) -> PlugMsgReturn:
    msg:str = session.sourcefiltermsg
    if msg.startswith(('!','！')):
        session.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Allow
    return PlugMsgReturn.Refuse

@on_message(msgfilter='转推授权',bindsendperm='manageuse',des='转推授权 - 转推授权')
async def _(session:Session):
    if session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'twitterPush','use'):
        session.send('已经拥有授权！')
        return
    res = session.authAllowSelf('twitterPush','use')
    if not res[0]:
        session.send(res[1])
    session.send('授权成功')

@on_message(msgfilter='取消转推授权',bindsendperm='manageuse',des='取消转推授权 - 取消转推授权')
async def _(session:Session):
    if not session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'twitterPush','use'):
        session.send('尚无授权！')
        return
    res = session.authRemovalSelf('twitterPush','use')
    if not res[0]:
        session.send(res[1])
    session.send('取消授权成功')

argfilter = PlugArgFilter()
argfilter.addArg(
    'msgtype',
    '消息来源',
    '需要输入有效的消息来源名称',
    canSkip=False,
    vlimit={
        '群聊':'group',
        '私聊':'private',
        'group':'',
        'private':'',
    }
    )
argfilter.addArg(
    'uuid',
    '消息来源ID',
    '需要输入有效的消息来源名称',
    canSkip=False,
    )
@on_message(msgfilter='定向清空转推列表',argfilter=argfilter,bindsendperm='manage',des='定向清空转推列表 消息来源标识 消息来源ID - 定向清空转推列表')
async def _(session:Session):
    msgtype = session.filterargs['msgtype']
    uuid = session.filterargs['uuid']
    res = pushlist.delPushunitFromPushTo(session.bottype,session.botuuid,msgtype,uuid)
    session.send(res[1])

def getRealTweetUserID(arg:str,useapi = True):
    arg = arg.strip()
    if arg == '#' or arg == '':
        return None
    if arg.isdigit():
        userinfo = tweetcache.getUserInfo(userid=int(arg))
        if userinfo is not None:
            return userinfo
    userinfo = tweetcache.getUserInfo(screen_name=arg)
    if userinfo is None:
        userinfo = tweetcache.getUserInfoFromllikename(arg)
    if userinfo is not None:
        return userinfo
    if not useapi:
        return (False,'缓存中查询不到此用户')
    app = ptwitterapps.getAllow('users_show')
    if app is not None:
        if arg.isdecimal():
            res = app.users_show(user_id = int(arg))
        else:
            res = app.users_show(screen_name = arg)
        if not res[0]:
            return (False,'查询不到此用户')
        userinfo = tweetstatusdeal.get_userinfo(res[1],checkspy=False)
        return userinfo
    return (False,'速率限制，或查询不到此用户，建议稍后再试')
argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
@on_message(msgfilter='定向清空转推对象',argfilter=argfilter,bindsendperm='manage',des='定向清空转推对象 用户名 - 定向清空转推对象')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    res = pushlist.delPushunitFromSpyUUID(userinfo['id_str'])
    session.send(res[1])

def getGlobalSpyList(spylist,page:int = 1):
    msg = '用户名,用户ID'
    page = page - 1
    i = 0
    lll = len(spylist)
    if page > int(lll/5):
        page = 0
    for spyuuid in spylist:
        userinfo = tweetcache.getUserInfo(userid=int(spyuuid))
        if i >= page*5 and i < (page+1)*5:
            if userinfo is not None:
                msg += "\n{0},{1}".format(userinfo['name'],spyuuid)
            else:
                msg += "\n{0},{1}".format('未知',spyuuid)
        i += 1
    msg += '\n当前页{0}/{1} (共{2}个推文)'.format(page+1,int(lll/5)+1,lll)
    return msg
argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='全局转推列表',argfilter=argfilter,bindsendperm='manage',des='全局转推列表 - 全局转推列表')
async def _(session:Session):
    page = session.filterargs['page']
    msg = getGlobalSpyList(pushlist.getSpylist(),page)
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
@on_message(msgfilter='添加辅助转推',argfilter=argfilter,bindsendperm='manage',des='添加辅助转推 用户名 - 添加辅助转推')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    res = addListen(userinfo['id_str'])
    session.send(res[1])

argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
@on_message(msgfilter='删除辅助转推',argfilter=argfilter,bindsendperm='manage',des='删除辅助转推 用户名 - 删除辅助转推')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    res = delListen(userinfo['id_str'])
    session.send(res[1])


argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='辅助转推列表',argfilter=argfilter,bindsendperm='manage',des='辅助转推列表 页码 - 辅助转推列表')
async def _(session:Session):
    page = session.filterargs['page']
    msg = getListenList(page)
    session.send(msg)


@on_message(msgfilter='启动主监听',bindsendperm='manage',des='启动主监听 - 启动推送的主要监听')
async def _(session:Session):
    pollingsetStreamOpen(True)
    session.send('已响应')
@on_message(msgfilter='关闭主监听',bindsendperm='manage',des='启动主监听 - 关闭推送的主要监听')
async def _(session:Session):
    pollingsetStreamOpen(False)
    session.send('已响应')
@on_message(msgfilter='启动辅助监听',bindsendperm='manage',des='启动辅助监听 - 启动推送的辅助监听')
async def _(session:Session):
    apisetStreamOpen(True)
    session.send('已响应')
@on_message(msgfilter='关闭辅助监听',bindsendperm='manage',des='关闭辅助监听 - 关闭推送的辅助监听')
async def _(session:Session):
    apisetStreamOpen(False)
    session.send('已响应')

def getRealTweetID(arg:str):
    arg = arg.strip()
    if arg.startswith('https://twitter.com/') or arg.startswith('http://twitter.com/'):
        arg = arg.split('/')[-1]
        arg = arg.split('?')[0]
        if not arg.isdigit():
            return None
        return int(arg)
    if arg.startswith('#'):
        arg = arg.strip()[1:]
    if not arg.isdigit():
        return None
    arg = int(arg)
    if arg <= 0:
        return None
    if arg < 10000:
        tweetid = tweetcache.getTweetSourceID(arg)
        if tweetid == -1:
            return None
        return tweetid
    return arg
argfilter = PlugArgFilter()
argfilter.addArg(
    'tweetid',
    '推特ID',
    '推特临时ID、推文链接、推文链接末尾的数字ID',
    prefunc=getRealTweetID,
    verif='uint'
    )
@on_message(msgfilter='(获取推文)|(看推)',argfilter=argfilter,bindperm='use',bindsendperm='cacheinfo',des='获取推文 推文ID或推文链接 - 获取指定推文',at_to_me=False)
async def _(session:Session):
    tweetid = session.filterargs['tweetid']
    tweet = tweetcache.getTweetFromCache(tweetid)
    if tweet is None:
        if ptwitterapps.hasApp():
            app = ptwitterapps.getAllow('statuses_lookup')
            if app == None:
                session.send("速率限制，请稍后再试！")
                return
            res = app.statuses_lookup(id = tweetid)
            if not res[0] or res[1] == []:
                session.send("未查找到该推文！")
                return
            tweet = tweetstatusdeal.get_tweet_info(res[1][0],checkspy=False)
        else:
            session.send("未从缓存中查找到该推文！")
            return
    msg = '已查找到推文：\n' + tweetevendeal.tweetToMsg(tweet).toStandStr()
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='推送优先级设置列表',argfilter=argfilter,bindsendperm='manage',des='推送优先级设置列表 - 轮询优先级列表')
async def _(session:Session):
    page = session.filterargs['page']
    msg = Priority_getlist(page)
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
argfilter.addArg(
        'value',
        '优先级',
        '优先级设置，范围1-15',
        prefunc=(lambda arg: int(arg) if arg.isdigit() and 0 < int(arg) <= 15 else None),
        verif='intnozero',
        vlimit={'':1}
    )
@on_message(msgfilter='设置推送优先级',argfilter=argfilter,bindsendperm='manage',des='设置推送优先级 用户ID 优先级 - 设置轮询优先级')
async def _(session:Session):
    value = session.filterargs['value']
    userinfo = session.filterargs['userinfo']
    res = Priority_set(userinfo['id_str'],value)
    session.send(res[1])


argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名',
        prefunc=getRealTweetUserID,
        verif='other'
    )
@on_message(msgfilter='查询推特用户',argfilter=argfilter,bindperm='use',bindsendperm='cacheinfo',des='查询推特用户 用户ID或用户名 - 查询指定推特用户的信息',at_to_me=False)
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    msg = "UID：{0}\n用户名：{1}\n用户昵称：{2}\n头像：{3}\n描述：{4}\n".format(
        userinfo['id'],
        userinfo['screen_name'],
        userinfo['name'],
        SendMessage().append(SendMessage.baleImgObj(userinfo['profile_image_url'])).toStandStr(),
        userinfo['description'],
    )
    try:
        msg += "粉丝数：{0}\n".format(
                userinfo['followers_count']
            )
        msg += "关注数：{0}\n".format(
                userinfo['friends_count']
            )
        msg += "发推数(包括转发)：{0}\n".format(
                userinfo['statuses_count']
            )
        msg += "账户创建时间：{0}".format(
                time.strftime("%Y{0}%m{1}%d{2} %H:%M:%S",time.localtime(int(userinfo['created_at']))).format('年','月','日')
            )
    except:
        pass
    session.send(msg)

def getTweetsList(tweets,page:int = 1):
    msg = ''
    page = page - 1
    i = 0
    lll = len(tweets)
    if page > int(lll/5):
        page = 0
    lll -= 1
    for i in range(lll,-1,-1):
        j = lll - i
        if j >= page*5 and j < (page+1)*5:
            msg += '\n' + tweetevendeal.tweetToMsg(tweets[i],simple=True).toStandStr()
    msg += '\n当前页{0}/{1} (共{2}个推文)'.format(page+1,int(lll/5)+1,lll)
    return msg
argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名(非昵称)',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        canSkip=True,
        vlimit={'':None},
        verif='other'
    )
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='推文列表',argfilter=argfilter,bindperm='use',bindsendperm='cacheinfo',des='推文列表 用户ID或用户名 页码 - 查询指定推特用户的推文列表',at_to_me=False)
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    page = session.filterargs['page']
    if userinfo is None:
        res = pushlist.getLitsFromPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
        if not res:
            session.send('推送列表内无成员，无法使用默认值')
        userid = res[0]['spyuuid']
        userinfo = tweetcache.getUserInfo(userid=userid)
    else:
        userid = userinfo['id_str']
    tweets = tweetcache.getTweetsFromCache(userid)
    if tweets is None:
        session.send('未查找到该用户推文列表，或该推文列表为空')
        return
    msg = getTweetsList(tweets.tm,page = page)
    session.send("{0} 的推文列表：{1}".format((userinfo['name'] if userinfo is not None else userid),msg))

argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名(非昵称)',
        prefunc=getRealTweetUserID,
        verif='other'
    )
argfilter.addArg(
        'nick',
        '推送昵称',
        '推送昵称',
        verif='str',
        vlimit={'':''}
    )
argfilter.addArg(
        'des',
        '推送描述',
        '推送描述',
        verif='str',
        vlimit={'':''}
    )
@on_message(msgfilter='(加推)|(addone)|(D一个)',argfilter=argfilter,des='加推 用户名 昵称(可选) 描述(可选) - 增加一个推送订阅，别名addone、D一个',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    nick = session.filterargs['nick']
    des = session.filterargs['des']
    pushconfig = pushlist.baleForConfig(
        nick = nick,
        des = des
    )
    unit = pushlist.baleToPushUnit(
        session.bottype,session.botuuid,
        session.botgroup,session.uuid,userinfo['id_str'],
        pushconfig,session.senduuid,time.time(),
        session.senduuid,time.time(),receiveobj=session.sourceObj
    )
    res = pushlist.addPushunit(unit)
    if not res[0]:
        session.send('推送添加失败，'+res[1])
        return
    msg = "UID：{0}\n用户名：{1}\n用户昵称：{2}\n头像：{3}\n描述：{4}\n".format(
        userinfo['id'],
        userinfo['screen_name'],
        userinfo['name'],
        SendMessage().append(SendMessage.baleImgObj(userinfo['profile_image_url'])).toStandStr(),
        userinfo['description'],
    )
    session.send('{0}\n推送添加成功！'.format(msg))


argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名(非昵称)',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
@on_message(msgfilter='(减推)|(delone)|(少D一个)',argfilter=argfilter,des='减推 用户名 - 减少一个推送订阅，别名delone、少D一个',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    unit = pushlist.findPushunit(session.bottype,session.botuuid,session.botgroup,session.uuid,userinfo['id_str'])
    if unit is None:
        session.send('找不到推送对象...')
        return
    res = pushlist.delPushunit(unit)
    if not res[0]:
        session.send('推送删除失败，'+res[1])
        return
    msg = "UID：{0}\n用户名：{1}\n用户昵称：{2}\n头像：{3}\n描述：{4}\n".format(
        userinfo['id'],
        userinfo['screen_name'],
        userinfo['name'],
        SendMessage().append(SendMessage.baleImgObj(userinfo['profile_image_url'])).toStandStr(),
        userinfo['description'],
    )
    session.send('{0}\n推送移除成功！'.format(msg))

def getSpyList(spylist,page:int = 1):
    msg = '昵称,用户名,描述'
    page = page - 1
    i = 0
    lll = len(spylist)
    if page > int(lll/5):
        page = 0
    for spyunit in spylist:
        userinfo = tweetcache.getUserInfo(userid=int(spyunit['spyuuid']))
        nick = spyunit['pushconfig']['unit']['nick']
        des = spyunit['pushconfig']['unit']['des'] if spyunit['pushconfig']['unit']['des'] else "未设置"
        if i >= page*5 and i < (page+1)*5:
            if userinfo is None:
                msg += "\n{0},{1},{2}".format((nick if nick else "未设置"),spyunit['spyuuid'],des)
            else:
                msg += "\n{0},{1},{2}".format((nick if nick else userinfo['name']),userinfo['screen_name'],des)
        i += 1
    msg += '\n当前页{0}/{1} (共{2}个对象)'.format(page+1,int(lll/5)+1,lll)
    return msg
argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='(转推列表)|(pusllist)|(DD列表)|(单推列表)',argfilter=argfilter,des='转推列表 用户名 - 获取推送名单，别名pusllist、DD列表、单推列表',sourceAdmin=True,bindperm='use',bindsendperm='manageself',at_to_me=False)
async def _(session:Session):
    page = session.filterargs['page']
    l = pushlist.getLitsFromPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
    msg = getSpyList(l,page)
    session.send(msg)

@on_message(msgfilter='(清空推送)|(delallpush)',des='清空推送 - 清空推送列表，别名delallpush',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    res = pushlist.delPushunitFromPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
    if not res[0]:
        session.send(res[1])
        return
    session.send("推送已清空")


#获取推送对象总属性设置
def getPushToSetting(config:dict,kind:str='basic') -> str:
    attrlist = {    
        'basic':{
            'upimg':'图片',#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
            
            #推特推送开关
            'retweet':'转推',#转推(默认不开启)
            'quoted':'转推并评论',#带评论转推(默认开启)
            'reply_to_status':'回复',#回复(默认开启)
            'reply_to_user':'提及',#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
            'none':'发推',#发推(默认开启)
        },
        'template':{
            #推特推送模版
            'template':'转推模版',
        },
        'ai':{
            #智能
            'ai_retweet':'部分转推',
            'ai_reply_to_status':'部分转发回复',
            'ai_passive_reply_to_status':'部分转发被回复',
            'ai_passive_quoted':'部分转发被转推并评论',
            'ai_passive_reply_to_user':'部分转发被提及',
        },
        'userinfo':{
            #个人信息变化推送(非实时)
            'change_ID':'ID修改', #ID修改(默认关闭)
            'change_name':'昵称修改', #昵称修改(默认开启)
            'change_description':'描述修改', #描述修改(默认关闭)
            'change_headimgchange':'头像修改', #头像更改(默认开启)
            'change_followers':'粉丝数(每几K)'
        }
    }
    res = ''
    if kind == 'basic':
        value = config['upimg']
        res += '\n图片:{0}'.format((value if value not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value]))
    if kind == 'template':
        value = config['template']
        res += '\n模版:\n{0}'.format(value if value else '未定义')
    for key,value in config['push'].items():
        if key in attrlist[kind]:
            res += '\n{0}:{1}'.format(
                    attrlist[kind][key],
                    (value if value not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value])
                )
    return res
argfilter = PlugArgFilter()
argfilter.addArg(
    'pagename',
    '分页名',
    '要显示的设置分页名,支持 基础、模版、部分、信息等',
    vlimit={
        '':'basic',
        'basic':'basic','基础':'basic',
        'template':'template','模版':'template',
        'ai':'ai','智能':'ai','智能推送':'ai','部分':'ai',
        'userinfo':'userinfo','信息':'userinfo','用户信息':'userinfo','用户':'userinfo','个人资料':'userinfo'
    }
)
@on_message(msgfilter='转推设置列表',argfilter=argfilter,des='转推设置列表 配置界面 - 界面支持四个选项',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    pagename = session.filterargs['pagename']
    pushto = pushlist.getPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
    if pushto is None:
        session.send('设置不存在，请添加推送后再试。')
        return
    config = pushlist.getMergeConfKey(pushto['config'])
    msg = getPushToSetting(config,pagename)
    msg = '-设置列表-' + msg
    session.send(msg)


argfilter = PlugArgFilter()
argfilter.addArg(
    'key',
    '属性名',
    '需要设置的属性名',
    vlimit={
        #携带图片发送
        'upimg':'upimg','图片':'upimg','img':'upimg',
        #昵称设置
        #'nick':'nick','昵称':'nick',
        #消息模版
        'retweet_template':'retweet_template','转推模版':'retweet_template',
        'quoted_template':'quoted_template','转推并评论模版':'quoted_template',
        'reply_to_status_template':'reply_to_status_template','回复模版':'reply_to_status_template',
        'reply_to_user_template':'reply_to_user_template','被提及模版':'reply_to_user_template',
        'none_template':'none_template','发推模版':'none_template',
        #推特转发各类型开关
        'retweet':'retweet','转推':'retweet',
        'quoted':'quoted','转推并评论':'quoted',
        'reply_to_status':'reply_to_status','回复':'reply_to_status',
        'reply_to_user':'reply_to_user','提及':'reply_to_user',
        'none':'none','发推':'none',
        #智能推送开关
        'ai_retweet':'ai_retweet','智能转推':'ai_retweet',
        'ai_reply_to_status':'ai_reply_to_status','智能转发回复':'ai_reply_to_status',
        'ai_passive_reply_to_status':'ai_passive_reply_to_status','智能转发被回复':'ai_passive_reply_to_status',
        'ai_passive_quoted':'ai_passive_quoted','智能转发被转推并评论':'ai_passive_quoted',
        'ai_passive_reply_to_user':'ai_passive_reply_to_user','智能转发被提及':'ai_passive_reply_to_user',
        #推特个人信息变动推送开关
        'change_id':'change_ID','ID改变':'change_ID','ID修改':'change_ID',
        'change_name':'change_name','名称改变':'change_name','名称修改':'change_name','名字改变':'change_name','名字修改':'change_name','昵称修改':'change_name','昵称改变':'change_name',
        'change_description':'change_description','描述改变':'change_description','描述修改':'change_description',
        'change_headimgchange':'change_headimgchange','头像改变':'change_headimgchange','头像修改':'change_headimgchange',
        'change_followers':'change_followers','粉丝增加':'change_followers','粉丝数':'change_followers'
    }
)
argfilter.addArg(
    'value',
    '要设置的值',
    '需要设置的值',
    vlimit={
        'true':1,'开':1,'打开':1,'开启':1,
        'false':0,'关':0,'关闭':0
    },
    verif='int'
)
@on_message(msgfilter='转推设置',argfilter=argfilter,des='推送设置 属性 属性值- 设置全局推送设置',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    key = session.filterargs['key']
    value = session.filterargs['value']
    res = pushlist.PushTo_setAttr(session.bottype,session.botuuid,session.botgroup,session.uuid,key,value)
    if not res[0]:
        session.send(res[1])
        return
    session.send(res[1])

argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名(非昵称)',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
argfilter.addArg(
    'key',
    '属性名',
    '需要设置的属性名',
    vlimit={
        #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
        #携带图片发送
        'upimg':'upimg','图片':'upimg','img':'upimg',
        #昵称设置
        #'nick':'nick','昵称':'nick',
        #消息模版
        'retweet_template':'retweet_template','转推模版':'retweet_template',
        'quoted_template':'quoted_template','转推并评论模版':'quoted_template',
        'reply_to_status_template':'reply_to_status_template','回复模版':'reply_to_status_template',
        'reply_to_user_template':'reply_to_user_template','被提及模版':'reply_to_user_template',
        'none_template':'none_template','发推模版':'none_template',
        #推特转发各类型开关
        'retweet':'retweet','转推':'retweet',
        'quoted':'quoted','转推并评论':'quoted',
        'reply_to_status':'reply_to_status','回复':'reply_to_status',
        'reply_to_user':'reply_to_user','提及':'reply_to_user',
        'none':'none','发推':'none',
        #智能推送开关
        'ai_retweet':'ai_retweet','智能转推':'ai_retweet',
        'ai_reply_to_status':'ai_reply_to_status','智能转发回复':'ai_reply_to_status',
        'ai_passive_reply_to_status':'ai_passive_reply_to_status','智能转发被回复':'ai_passive_reply_to_status',
        'ai_passive_quoted':'ai_passive_quoted','智能转发被转推并评论':'ai_passive_quoted',
        'ai_passive_reply_to_user':'ai_passive_reply_to_user','智能转发被提及':'ai_passive_reply_to_user',
        #推特个人信息变动推送开关
        'change_id':'change_ID','ID改变':'change_ID','ID修改':'change_ID',
        'change_name':'change_name','名称改变':'change_name','名称修改':'change_name','名字改变':'change_name','名字修改':'change_name','昵称修改':'change_name','昵称改变':'change_name',
        'change_description':'change_description','描述改变':'change_description','描述修改':'change_description',
        'change_headimgchange':'change_headimgchange','头像改变':'change_headimgchange','头像修改':'change_headimgchange'
    }
)
argfilter.addArg(
    'value',
    '要设置的值',
    '需要设置的值',
    vlimit={
        '*':'*',#允许原始值
        'true':'1','开':'1','打开':'1','开启':'1',
        'false':'0','关':'0','关闭':'0'
    },
    verif='str'
)
@on_message(msgfilter='转推单元设置',argfilter=argfilter,des='推送单元设置 对象ID 属性 属性值- 设置单元推送设置',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    key = session.filterargs['key']
    value = session.filterargs['value']
    res = pushlist.setPushunitAttr(session.bottype,session.botuuid,session.botgroup,session.uuid,userinfo['id_str'],key,value)
    if not res[0]:
        session.send(res[1])
        return
    session.send(res[1])



#获取推送对象总属性设置
def getConfigSetting(config:dict,kind:str='basic') -> str:
    attrlist = {    
        'basic':{
            'upimg':'图片',#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
            
            #推特推送开关
            'retweet':'转推',#转推(默认不开启)
            'quoted':'转推并评论',#带评论转推(默认开启)
            'reply_to_status':'回复',#回复(默认开启)
            'reply_to_user':'提及',#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
            'none':'发推',#发推(默认开启)
        },
        'template':{
            #推特推送模版
            'retweet_template':'转推模版',
            'quoted_template':'转推并评论模版',
            'reply_to_status_template':'回复模版',
            'reply_to_user_template':'提及模版', 
            'none_template':'发推模版',
        },
        'ai':{
            #智能
            'ai_retweet':'部分转推',
            'ai_reply_to_status':'部分转发回复',
            'ai_passive_reply_to_status':'部分转发被回复',
            'ai_passive_quoted':'部分转发被转推并评论',
            'ai_passive_reply_to_user':'部分转发被提及',
        },
        'userinfo':{
            #个人信息变化推送(非实时)
            'change_ID':'ID修改', #ID修改(默认关闭)
            'change_name':'昵称修改', #昵称修改(默认开启)
            'change_description':'描述修改', #描述修改(默认关闭)
            'change_headimgchange':'头像修改', #头像更改(默认开启)
        }
    }
    res = ''
    if kind == 'basic':
        value = config['upimg']
        res += '\n图片:{0}'.format((value if value not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value]))
    for key,value in config['push'].items():
        if key in attrlist[kind]:
            res += '\n{0}:{1}'.format(
                    attrlist[kind][key],
                    (value if value not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value])
                )
    return res
argfilter = PlugArgFilter()
argfilter.addArg(
        'userinfo',
        '推特用户ID',
        '推特用户ID或有效用户名(非昵称)',
        prefunc=functools.partial(getRealTweetUserID,useapi = False),
        verif='other'
    )
argfilter.addArg(
    'pagename',
    '分页名',
    '要显示的设置分页名,支持 基础、模版、部分、信息等',
    vlimit={
        '':'basic',
        'basic':'basic','基础':'basic',
        'template':'template','模版':'template',
        'ai':'ai','智能':'ai','智能推送':'ai','部分':'ai',
        'userinfo':'userinfo','信息':'userinfo','用户信息':'userinfo','用户':'userinfo','个人资料':'userinfo'
    }
)
@on_message(msgfilter='转推单元设置列表',argfilter=argfilter,des='转推单元设置列表 用户名 配置界面 - 界面支持四个选项',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    userinfo = session.filterargs['userinfo']
    pagename = session.filterargs['pagename']
    pushto = pushlist.getPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
    if pushto is None:
        session.send('设置不存在，请添加推送后再试。')
        return
    pushunit = pushlist.findPushunit(session.bottype,session.botuuid,session.botgroup,session.uuid,userinfo['id_str'])
    if pushunit is None:
        session.send('推送单元不存在，请添加推送后再试。')
        return
    config = pushlist.getMergeConfKey(pushto['config'],pushunit['pushconfig'])
    msg = getPushToSetting(config,pagename)
    msg = '-设置列表-' + msg
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
        'tweetid',
        '正整数',
        '推文ID或任意正整数',
        verif='uint'
    )
@on_message(msgfilter='(64进制编码)|(2t64编码)|(压缩推文ID)',des='2t64编码 参数 - 2t64编码,别名64进制编码、压缩推文ID')
async def _(session:Session):
    tweetid = session.filterargs['tweetid']
    msg = encode_b64(tweetid,offset=0)
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
        'text',
        '编码文本',
        '64进制编码的文本',
        verif='str'
    )
@on_message(msgfilter='(64进制编码)|(2t64编码)|(压缩推文ID)',des='2t64编码 参数 - 2t64编码,别名64进制编码、压缩推文ID')
async def _(session:Session):
    text = session.filterargs['text']
    msg = str(decode_b64(text,offset=0))
    session.send(msg)