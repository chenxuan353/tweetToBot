from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,PlugMsgTypeEnum,PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

from pluginsinterface.PluginLoader import SendMessage,StandEven
from module.msgStream import send_msg
from module.twitter import tweetcache,encode_b64,decode_b64
from module.tweettrans import TweetTrans,rate_limit_bucket
import re
import traceback
import requests
import os
import random
import time
import base64
from io import BytesIO
import asyncio
import config
from helper import dictGet,dictSet
from helper import getlogger,data_read_auto,data_save,TempMemory
logger = getlogger(__name__)
# 线程池
from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(max_workers=4,thread_name_prefix="trans_Threads")

trans_img_path = config.trans_img_path
transtemplate_filename = 'transtemplate.json'
transtemplate = data_read_auto(transtemplate_filename,default={})
def pop_trigger(item):
    # 烤推历史溢出时删除旧文件
    if os.path.exists(item['filepath']):
        os.remove(item['filepath'])
# 烤推列表缓存
trans_tmemory = TempMemory('trans_tmemory.json',limit=350,autoload=True,autosave=True,pop_trigger = pop_trigger)

def setTranstemplate(bottype,botgroup,uuid,value):
    global transtemplate
    dictSet(transtemplate,bottype,botgroup,uuid,obj=value)
    data_save(transtemplate_filename,transtemplate)
def getTranstemplate(bottype,botgroup,uuid):
    global transtemplate
    return dictGet(transtemplate,bottype,botgroup,uuid,default='<p dir="auto" style="color:# 1DA1F2;font-size:0.7em;font-weight: 600;">翻译自日文</p>')


@plugRegistered('烤推','TweetTrans')
def _():
    return {
        'plugmanagement':'1.0',# 插件注册管理(原样)  
        'version':'1.0',# 插件版本  
        'auther':'chenxuan',# 插件作者  
        'des':'用于烤推的插件'# 插件描述  
        }

@on_plugloaded()
def _(plug:PluginsManage):
    if plug:
        # 注册权限
        plug.registerPerm('manage',des = '管理权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('manageuse',des = '管理授权的权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('use',des = '使用权限',defaultperm=PlugMsgTypeEnum.private)
        plug.registerPerm('trans',des = '烤推权限',defaultperm=PlugMsgTypeEnum.allowall)

@on_preprocessor()
async def _(session:Session) -> PlugMsgReturn:
    # msg:str = session.sourcefiltermsg
    # if msg.startswith(('!','！')):
    #     session.sourcefiltermsg = msg[1:]
    #     return PlugMsgReturn.Allow
    # return PlugMsgReturn.Refuse
    return PlugMsgReturn.Allow

@on_message(msgfilter='[!！]烤推授权',bindsendperm='manage',des='烤推授权 - 烤推授权')
async def _(session:Session):
    if session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'TweetTrans','use'):
        session.send('已经拥有授权！')
        return
    res = session.authAllowSelf('TweetTrans','use')
    if not res[0]:
        session.send(res[1])
    session.send('授权成功')

@on_message(msgfilter='[!！]取消烤推授权',bindsendperm='manage',des='取消烤推授权 - 取消烤推授权')
async def _(session:Session):
    if not session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'TweetTrans','use'):
        session.send('尚无授权！')
        return
    res = session.authRemovalSelf('TweetTrans','use')
    if not res[0]:
        session.send(res[1])
    session.send('取消授权成功')

def getImage(url,maxsize = 50,timeout = 15):
    """
        获取图片base64编码，参数为最大文件大小(Kb)，下载超时时间
    """
    maxsize = maxsize*1024
    try:
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        if int(r.headers.get('Content-Length')) > maxsize:
            raise ValueError('response too large')
        filedata = bytes()
        size = 0
        start = time.time()
        for chunk in r.iter_content(1024):
            if time.time() - start > timeout:
                raise ValueError('timeout reached')
            filedata += chunk
            size += len(chunk)
            if size > maxsize:
                raise ValueError('response too large')
        base64code = str(base64.b64encode(filedata),'utf8')
        if config.DEBUG:
            logger.info(base64code)
    except ValueError:
        return (False,'文件大小超出限制或下载超时')
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        return (False,'文件下载异常')
    else:
        return (True,'文件下载成功',base64code)
@on_message(msgfilter='([!！]设置烤推模[版板])',sourceAdmin=True,des='设置烤推模版 参数 - 设置烤推模版')
async def _(session:Session):
    urls = session.message.gerUrls()
    if urls:
        if len(urls) != 1:
            session.send('错误，模版图片最多只能包含一张')
            return
        res = getImage(urls[0])
        if not res[0]:
            session.send('模版设置失败->'+res[1])
            return
        b64 = res[2].replace('','')
        template = "<div style=\"padding:5px;margin:0px\"><img height=\"38\" src=\"data:image/jpg;base64,{0}\"></div>".format(b64)
        setTranstemplate(session.bottype,session.botgroup,session.uuid,template)
        msg = SendMessage('已设置模版为图片->')
        msg.append(msg.baleImgObj(urls[0]))
        session.send(msg)
        return
    message = SendMessage(session.argstr).toSimpleStr()
    code = [
        ('&','&amp;'),
        ('<','&lt;'),
        ('>','&gt;'),
        ('"','&quot;'),
        ('\'','&# x27;'),
        ('/','&# x2F;')
    ]
    for cu in code:
        message.replace(cu[0],cu[1])
    template = '<p dir="auto" style="color:# 1DA1F2;font-size:0.7em;font-weight: 600;">{0}</p>'.format(message)
    setTranstemplate(session.bottype,session.botgroup,session.uuid,template)
    session.send('已设置模版为->'+message)


def deal_trans(arg,template) -> dict:
    trans = {
        'type_html':template,
        'source':arg,
        'text':{}
    }
    tests = arg.split('# # ')
    if len(tests) == 1:
        kvc = tests[0].partition("# !")
        trans['text']['main'] = []
        trans['text']['main'].append(kvc[0].strip())
        if kvc[2] != '':
            trans['text']['main'].append(kvc[2].strip())
    else:
        for test in tests:
            test = test.strip()
            if test == '':
                continue
            kv = re.findall(r'^([0-9]{1,2}|main|m)\s{1}(.+)',test,re.S)
            if kv == []:
                return None # 格式不正确
            kv = list(kv[0])
            if kv[0].isnumeric():
                kv[0] = str(int(kv[0]))
            elif kv[0] == 'm':
                kv[0] = 'main'
            kvc = kv[1].partition("# !")
            trans['text'][kv[0]] = []
            trans['text'][kv[0]].append(kvc[0].strip())
            if kvc[2] != '':
                trans['text'][kv[0]].append(kvc[2].strip())
    return trans
def getTransImg(even:StandEven,senduuid,sendname,tweetid,trans):
    try:
        # 使用64进制减少长度
        tasktype = encode_b64(int(time.time()),offset = 0) + '_' + str(random.randint(0,1000))
        # 检查推文缓存
        tweet_name = 's'
        tweet = tweetcache.getTweetFromCache(tweetid)
        if tweet is not None:
            logger.info('检测到缓存:' + tweet['id_str'] + '(' + tweet['userinfo']['name'] + ')')
            # logger.info(tweet)
            tweet_cache = tweet
            tweet_name = tweet_cache['userinfo']['screen_name']
        tt = TweetTrans()
        res = tt.getTransFromTweetID(
            str(tweetid),
            trans,
            tweet_name,
            str(tasktype)
            )
        if res[0]:
            imgurl = trans_img_path + str(tasktype) + '.png'
            trans_tmemory.join({
                'bottype':even.bottype,
                'botuuid':even.botuuid,
                'botgroup':even.botgroup,
                'uuid':even.uuid,
                'senduuid':even.senduuid,
                'sendnick':sendname,
                'imgurl':imgurl,
                'filepath':res[1],
                'id':tweetid,
                'mintrans':trans['source'][0:15].replace("\r"," ").replace("\n"," "),
                'minid':encode_b64(tweetid),
                'tasktype':tasktype,
                'trans':trans,
                })
            msg = SendMessage("{url}\n".format(url = imgurl))
            msg.append(msg.baleImgObj(imgurl))
            msg.append('\n使用 !tl 查看烤推历史')
            even.send(msg)
        else:
            even.send("错误，"+res[2])
        del tt
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        even.send("错误，烤推服务异常!")
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
        arg = decode_b64(arg)
        if arg == -1:
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
@on_message(msgfilter='([!！]烤推)|([!！]t)|(##)',argfilter=argfilter,bindperm='use',bindsendperm='trans',des='烤推 烤推参数 - 烤制推文,别名t',at_to_me=False)
async def _(session:Session):
    if not rate_limit_bucket.consume(1):
        await session.send("烤推繁忙，请稍后再试")
        return
    tweetid = session.filterargs['tweetid']
    sendname = session.even.senduuidinfo['nick']
    template = getTranstemplate(session.bottype,session.botgroup,session.uuid)
    if not session.filterargs['tail']:
        template = ""
    trans = deal_trans(session.filterargs['tail'],template)
    pool.submit(getTransImg,
        session.even,
        session.senduuid,sendname,tweetid,trans
        )
    session.send("图片合成中...")

def getlist(bottype,botuuid,botgroup,uuid,page:int=1):
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    page = page - 1
    cout = 0
    s = "昵称,任务标识,推文标识,翻译简写"
    for i in range(length - 1,-1,-1):
        if ttm[i]['bottype'] == bottype and \
            ttm[i]['botuuid'] == botuuid and \
            ttm[i]['botgroup'] == botgroup and \
            ttm[i]['uuid'] == uuid:
            if cout >= page*5 and cout < (page+1)*5:
                s += '\n{0},{1},{2},{3}'.format(
                    ttm[i]['sendnick'],
                    ttm[i]['tasktype'],
                    ttm[i]['minid'],
                    ttm[i]['mintrans']
                )
            cout = cout + 1
    totalpage = int(cout/5)+1
    s += '\n当前页{0}/{1} (共{2}个记录)'.format(page+1,totalpage,cout)
    s += '使用!推文任务 任务标识 获取指定任务图片' + "\n"
    s += '使用!烤推结果 推文标识 (也可使用!gt)获取指定推文最后的译文图片'
    return s
argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}# 设置默认值
    )
@on_message(msgfilter='([!！]烤推列表)|([!！]tl)',argfilter=argfilter,bindperm='use',des='烤推列表 页码 - 获取烤推列表,别名tl',at_to_me=False)
async def _(session:Session):
    page = session.filterargs['page']
    msg = getlist(session.bottype,session.botuuid,session.botgroup,session.uuid,page)
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
    'tasktype',
    '任务标识',
    '烤推结果的任务标识',
    prefunc=getRealTweetID,
    verif='uint'
    )
@on_message(msgfilter='([!！]烤推结果)|([!！]gt)',argfilter=argfilter,bindperm='use',des='烤推结果 推特ID - 获取指定ID的最后烤推结果,别名gt',at_to_me=False)
async def _(session:Session):
    tweetid = session.filterargs['tweetid']
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    for i in range(length - 1,-1,-1):
        if ttm[i]['id'] == tweetid:
            imgurl = ttm[i]['imgurl']
            msg = SendMessage('推文ID：{0}'.format(ttm[i]['minid']))
            msg.append("{url}\n".format(url = imgurl))
            msg.append(msg.baleImgObj(imgurl))
            msg.append('\n使用 !tl 查看烤推历史')
            session.send(msg)
            return
    session.send("未查找到推文烤制结果")

@on_message(msgfilter='([!！]推文任务)|([!！]tgt)',bindperm='use',des='推文任务 任务标识 - 获取指定标识烤推结果,别名tgt',at_to_me=False)
async def _(session:Session):
    tasktype = session.filterargs['tail']
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    for i in range(length - 1,-1,-1):
        if ttm[i]['tasktype'] == tasktype:
            imgurl = ttm[i]['imgurl']
            msg = SendMessage('推文ID：{0}'.format(ttm[i]['minid']))
            msg.append("{url}\n".format(url = imgurl))
            msg.append(msg.baleImgObj(imgurl))
            msg.append('\n使用 !tl 查看烤推历史')
            session.send(msg)
            return
    session.send("未查找到烤制结果")

@on_message(msgfilter='[!！]烤推帮助',bindperm='use',des='烤推帮助 - 获取烤推帮助',at_to_me=False)
async def _(session:Session):
    res = session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'TweetTrans','use')
    msg = '当前版本为全自动烤推机V3.0' + "\n" + \
        '授权状态:' + ("已授权" if res else "未授权") + "\n" + \
        '!t 推文ID 翻译 -合成翻译,别名 烤推' + "\n" + \
        '!tl - 已烤制结果列表,别名 烤推列表' + "\n" + \
        '!gt 推文ID -获取推文最后结果,别名 烤推结果' + "\n" + \
        '!tgt 任务标识 -获取指定烤推结果,别名 推文任务' + "\n" + \
        '多层回复翻译:' + "\n" + \
        '# # 1 第一层翻译' + "\n" + \
        '# ! 第一层层内推文(转推并评论类型里的内嵌推文)' + "\n" + \
        '# # 2 第二层翻译' + "\n" + \
        '# # main 主翻译' + "\n" + \
        '烤推支持换行参数，支持更换模版(翻译自日文)' + "\n" + \
        '如果出现问题可以 !反馈 反馈内容 反馈信息'
    session.send(msg)