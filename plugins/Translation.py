# 插件标准依赖
from pluginsinterface.PluginLoader import on_message, Session, on_preprocessor, on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn, plugRegistered, PlugMsgTypeEnum, PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

from pluginsinterface.PluginLoader import StandEven
import re
import time
import traceback
from module.twitter import tweetcache
from module.machineTranslation import allow_st, engine_nick, engine_list
from helper import dictSet, dictGet
from helper import getlogger, data_read_auto, data_save
logger = getlogger(__name__)

transstreamconfig = 'translationstream.json'
streamlist = data_read_auto(transstreamconfig, default={})
# 线程池
from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tls_Threads")


@plugRegistered('翻译翻译', 'translation')
def _():
    return {
        'plugmanagement': '1.0',  # 插件注册管理(原样)  
        'version': '1.0',  # 插件版本  
        'auther': 'chenxuan',  # 插件作者  
        'des': '用于机翻的插件'  # 插件描述  
    }


@on_plugloaded()
def _(plug: PluginsManage):
    if plug:
        # 注册权限
        plug.registerPerm('manage',
                          des='管理权限',
                          defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('streamtrans',
                          des='设置流式翻译的权限',
                          defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('trans',
                          des='翻译权限',
                          defaultperm=PlugMsgTypeEnum.allowall)


def streamTrans(even: StandEven, text, source, target, res, timestamp):
    if time.time() - timestamp > 15:
        logger.warning('翻译执行超时...')
        return
    try:
        engine_func = engine_list[res[even.senduuid]['engine']]['func']
        res = engine_func(text, source, target)
        even.send("机翻:{0}".format(res[1]))
        even.setReply(False)
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)


@on_preprocessor()
async def _(session: Session) -> PlugMsgReturn:
    res = dictGet(streamlist, session.bottype, session.botgroup,
                  session.botuuid, session.uuid)
    if res is not None:
        if session.senduuid in res:
            source = res[session.senduuid]['source']
            target = res[session.senduuid]['target']
            text = session.message.filterToStr(('text'))
            if not text:
                return PlugMsgReturn.Allow
            if source == 'auto' and target == 'zh':
                if not re.search(r'[\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7A3]',
                                 text):
                    target = 'jp'
                else:
                    source = 'jp'
            streamTrans(session.even, text, source, target, res, time.time())
            # pool.submit(streamTrans,session.even,text,source,target,time.time())
    return PlugMsgReturn.Allow


argfilter = PlugArgFilter()
argfilter.addArg(
    'engine',
    '机翻引擎',
    '机翻引擎',
    verif='str',
    canSkip=True,
    vlimit=engine_nick  # 设置默认值
)
argfilter.addArg(
    'source',
    '源语言',
    '语言',
    verif='str',
    canSkip=True,
    vlimit=allow_st['Source']  # 设置默认值
)
argfilter.addArg(
    'target',
    '目标语言',
    '语言',
    verif='str',
    canSkip=True,
    vlimit=allow_st['Target']  # 设置默认值
)


@on_message(msgfilter='([！!]翻译)|([！!]机翻)|(机翻)',
            argfilter=argfilter,
            des='翻译 引擎(可选) 源语言(可选) 目标语言(可选) 待翻译文本 - 机器翻译，别名机翻',
            bindsendperm='trans',
            at_to_me=False)
async def _(session: Session):
    engine = session.filterargs['engine']
    source = session.filterargs['source']
    target = session.filterargs['target']
    text: str = session.filterargs['tail'].strip()
    if text == '':
        return
    if text.startswith('# '):
        if text[1:].isdigit():
            n = int(text[1:])
            tweetid = tweetcache.getTweetSourceID(n)
            if tweetid != -1:
                tweets = tweetcache.getTweetFromCache(tweetid=tweetid)
                if tweets is not None:
                    text = tweets['text']
    elif source == 'auto' and target == 'zh':
        if not re.search(r'[\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7A3]', text):
            target = 'jp'
        else:
            source = 'jp'
    engine_func = engine_list[engine]['func']
    res = engine_func(text, source, target)
    if not res[0]:
        session.send("翻译引擎错误，" + res[1])
        return
    session.send("---翻译结果---\n" + res[1])


argfilter = PlugArgFilter()
argfilter.addArg('transtarget',
                 '翻译目标',
                 '目标唯一ID',
                 verif='uint',
                 canSkip=True,
                 vlimit={'': ''})
argfilter.addArg(
    'engine',
    '机翻引擎',
    '机翻引擎',
    verif='str',
    canSkip=True,
    vlimit=engine_nick  # 设置默认值
)
argfilter.addArg(
    'source',
    '源语言',
    '语言',
    verif='str',
    canSkip=True,
    vlimit=allow_st['Source']  # 设置默认值
)
argfilter.addArg(
    'target',
    '目标语言',
    '语言',
    verif='str',
    canSkip=True,
    vlimit=allow_st['Target']  # 设置默认值
)


@on_message(msgfilter='([！!]启用流式翻译)',
            argfilter=argfilter,
            des='启用流式翻译 目标 引擎(可选) 源语言(可选) 目标语言(可选) - 启用流式翻译',
            bindsendperm='streamtrans',
            at_to_me=False)
async def _(session: Session):
    transtarget = str(session.filterargs['transtarget'])
    engine = session.filterargs['engine']
    source = session.filterargs['source']
    target = session.filterargs['target']
    if transtarget == '':
        transtarget = session.senduuid
    if dictGet(streamlist, session.bottype, session.botgroup, session.botuuid,
               session.uuid, transtarget):
        session.send("{0} 的流式翻译已经为启动状态".format(transtarget))
        return
    streamobj = {
        'bottype': session.bottype,
        'botgroup': session.botgroup,
        'botuuid': session.botuuid,
        'uuid': session.uuid,
        'openuuid': session.senduuid,
        'transtarget': transtarget,
        'engine': engine,
        'source': source,
        'target': target
    }
    dictSet(streamlist,
            session.bottype,
            session.botgroup,
            session.botuuid,
            session.uuid,
            transtarget,
            obj=streamobj)
    session.send("已对 {0} 启用流式翻译".format(transtarget))
    data_save(transstreamconfig, streamlist)


argfilter = PlugArgFilter()
argfilter.addArg('transtarget',
                 '翻译目标',
                 '目标唯一ID',
                 verif='uint',
                 canSkip=True,
                 vlimit={'': ''})


@on_message(msgfilter='([！!]关闭流式翻译)',
            argfilter=argfilter,
            des='关闭流式翻译 目标 - 关闭流式翻译',
            bindsendperm='streamtrans',
            at_to_me=False)
async def _(session: Session):
    transtarget = str(session.filterargs['transtarget'])
    res = dictGet(streamlist, session.bottype, session.botgroup,
                  session.botuuid, session.uuid)
    if transtarget == '':
        transtarget = session.senduuid
    if res is None:
        session.send("{0} 不在流式翻译列表中...".format(transtarget))
        return
    if transtarget not in res:
        session.send("{0} 不在流式翻译列表中...".format(transtarget))
        return
    del res[transtarget]
    session.send("{0} 的流式翻译已关闭".format(transtarget))
    data_save(transstreamconfig, streamlist)


def getstreamlist(streamlist, page: int = 1):
    msg = '目标,引擎,源语言->目标语言'
    page = page - 1
    i = 0
    lll = len(streamlist)
    if page > int(lll / 5):
        page = 0
    for streamunit in streamlist.values():
        if i >= page * 5 and i < (page + 1) * 5:
            msg += '\n{0},{1},{2}->{3}'.format(streamunit['transtarget'],
                                               streamunit['engine'],
                                               streamunit['source'],
                                               streamunit['target'])
        i += 1
    msg += '\n当前页{0}/{1} (共{2}个对象)'.format(page + 1, int(lll / 5) + 1, lll)
    return msg


argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'': 1}  # 设置默认值
)


@on_message(msgfilter='([！!]流式翻译列表)',
            argfilter=argfilter,
            des='流式翻译列表 - 流式翻译列表',
            bindsendperm='streamtrans',
            at_to_me=False)
async def _(session: Session):
    page = session.filterargs['page']
    res = dictGet(streamlist, session.bottype, session.botgroup,
                  session.botuuid, session.uuid)
    if res is None:
        session.send("流式翻译列表为空！")
        return
    msg = getstreamlist(res, page)
    session.send(msg)


@on_message(msgfilter='([！!]清空流式翻译列表)',
            des='清空流式翻译列表 - 清空流式翻译列表',
            bindsendperm='streamtrans',
            sourceAdmin=True,
            at_to_me=False)
async def _(session: Session):
    res = dictGet(streamlist, session.bottype, session.botgroup,
                  session.botuuid, session.uuid)
    if res is None:
        session.send("流式翻译列表为空！")
        return
    res.clear()
    session.send('流式翻译列表已清空')
    data_save(transstreamconfig, streamlist)
