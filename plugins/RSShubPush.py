from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,PlugMsgTypeEnum,PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

import time
from module.pollingRSShub import Priority_getlist,Priority_set,setStreamOpen

from module.RSS import pushlist
from module.pollingRSShub import rssapps
from helper import getlogger
logger = getlogger(__name__)
"""
    RSShub推送管理
"""

@plugRegistered('RSShub推送管理','RSShubPush')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'chenxuan',#插件作者  
        'des':'用于管理RSShub推送的插件'#插件描述  
        }
@on_plugloaded()
def _(plug:PluginsManage):
    if plug:
        #注册权限
        plug.registerPerm('manage',des = '管理权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('use',des = '使用权限',defaultperm=PlugMsgTypeEnum.private)
        plug.registerPerm('manageself',des = '管理自己的权限',defaultperm=PlugMsgTypeEnum.allowall)
        #plug.registerPerm('cacheinfo',des = '获取缓存信息的权限',defaultperm=PlugMsgTypeEnum.allowall)

@on_preprocessor()
async def _(session:Session) -> PlugMsgReturn:
    msg:str = session.sourcefiltermsg
    if msg.startswith(('!','！')):
        session.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Allow
    return PlugMsgReturn.Refuse


@on_message(msgfilter='启动RSS监听',bindsendperm='manage',des='启动RSS监听 - 启动RSS推送的主要监听')
async def _(session:Session):
    setStreamOpen(True)
    session.send('已响应')
@on_message(msgfilter='关闭RSS监听',bindsendperm='manage',des='关闭RSS监听 - 启动RSS推送的主要监听')
async def _(session:Session):
    setStreamOpen(False)
    session.send('已响应')

@on_message(msgfilter='RSS订阅授权',bindsendperm='manage',des='RSS订阅授权 - RSS订阅授权')
async def _(session:Session):
    if session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'RSShubPush','use'):
        session.send('已经拥有授权！')
        return
    res = session.authAllowSelf('RSShubPush','use')
    if not res[0]:
        session.send(res[1])
    session.send('授权成功')

@on_message(msgfilter='取消RSS订阅授权',bindsendperm='manage',des='取消RSS订阅授权 - 取消RSS订阅授权')
async def _(session:Session):
    if not session.authCheck(PlugMsgTypeEnum.getMsgtype(session.msgtype),'RSShubPush','use'):
        session.send('尚无授权！')
        return
    res = session.authRemovalSelf('RSShubPush','use')
    if not res[0]:
        session.send("默认授权不可取消")
        return
    session.send('取消授权成功')

argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='RSS优先级设置列表',argfilter=argfilter,bindsendperm='manage',des='RSS优先级设置列表 - RSS优先级设置列表')
async def _(session:Session):
    page = session.filterargs['page']
    msg = Priority_getlist(page)
    session.send(msg)

def getPath(arg:str):
    arg = arg.strip()
    arg = arg.replace('·','/')
    if arg.startswith('https://rsshub.app') or arg.startswith('http://rsshub.app'):
        arg = arg.replace('https://rsshub.app','')
        arg = arg.replace('http://rsshub.app','')
    if not arg.startswith('/'):
        arg = '/'+arg
    return arg
argfilter = PlugArgFilter()
argfilter.addArg(
        'path',
        '订阅路径',
        '仅限RSShub支持的路径，参数为根域名后的相对路径，无法输入的路径用·替代/',
        prefunc=getPath,
        verif='str'
    )
argfilter.addArg(
        'value',
        '优先级',
        '优先级设置，范围1-15',
        prefunc=(lambda arg: int(arg) if arg.isdigit() and 0 < int(arg) <= 15 else None),
        verif='intnozero',
        vlimit={'':1}
    )
@on_message(msgfilter='设置RSS优先级',argfilter=argfilter,bindsendperm='manage',des='设置RSS优先级 路径 优先级 - 设置轮询优先级')
async def _(session:Session):
    path = session.filterargs['path']
    value = session.filterargs['value']
    res = Priority_set(value,path)
    session.send(res[1])

argfilter = PlugArgFilter()
argfilter.addArg(
        'path',
        '订阅路径',
        '仅限RSShub支持的路径，参数为根域名后的相对路径，无法输入的路径用·替代/',
        prefunc=getPath,
        verif='str'
    )
argfilter.addArg(
        'nick',
        '推送昵称',
        '推送昵称',
        verif='str',
        vlimit={'':''}
    )
argfilter.addArg(
        'unitdes',
        '项目描述',
        '推送的项目描述',
        verif='str',
        vlimit={'':''}
    )
@on_message(msgfilter='订阅',argfilter=argfilter,des='订阅 路径 昵称(可选) 推送描述(可选) 选项(可选)- 增加一个RSS订阅,路径为根域名后的相对路径,无法输入的路径用·替代/',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    option:str = session.filterargs['tail'].strip()
    path = session.filterargs['path']
    nick = session.filterargs['nick']
    unitdes = session.filterargs['unitdes']
    if not rssapps.testconnect(path):
        session.send('错误，此路径不可用！')
        return
    res = pushlist.dealOption(path,option)
    if not res[0]:
        session.send(res[1])
        return
    options = res[1]
    pushconfig = pushlist.baleForConfig(
        nick = nick,
        unitdes = unitdes,
        options = options
    )
    unit = pushlist.baleToPushUnit(
        session.bottype,session.botuuid,
        session.botgroup,session.uuid,path,
        pushconfig,session.senduuid,time.time(),
        session.senduuid,time.time(),receiveobj=session.sourceObj
    )
    res = pushlist.addPushunit(unit,{})
    if not res[0]:
        session.send('订阅添加失败，'+res[1])
        return
    session.send('添加路径：{0}\n订阅添加成功！如需要优化推送，请联系维护者。'.format(path))

argfilter = PlugArgFilter()
argfilter.addArg(
        'path',
        '订阅路径',
        '仅限RSShub支持的路径，参数为根域名后的相对路径，无法输入的路径用·替代/',
        prefunc=getPath,
        verif='str'
    )
@on_message(msgfilter='取消订阅',argfilter=argfilter,des='取消订阅 路径 - 减少一个推送订阅',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    path = session.filterargs['path']
    unit = pushlist.findPushunit(session.bottype,session.botuuid,session.botgroup,session.uuid,path)
    if unit is None:
        session.send('找不到订阅对象...')
        return
    res = pushlist.delPushunit(unit)
    if not res[0]:
        session.send('订阅删除失败，'+res[1])
        return
    session.send('路径：{0}\n订阅删除成功！'.format(path))

@on_message(msgfilter='订阅源解码',argfilter=argfilter,des='订阅源解码 路径 - 获取解码后的路径',sourceAdmin=True,bindperm='use',bindsendperm='manageself',at_to_me=False)
async def _(session:Session):
    path = session.filterargs['path']
    session.send('路径：'+path)


def getSpyList(spylist,page:int = 1):
    msg = '昵称,路径,描述'
    page = page - 1
    i = 0
    lll = len(spylist)
    if page > int(lll/5):
        page = 0
    for spyunit in spylist:
        nick = spyunit['pushconfig']['nick'] if spyunit['pushconfig']['nick'] else "未设置"
        des = spyunit['pushconfig']['unitdes'] if spyunit['pushconfig']['unitdes'] else "未设置"
        if des == "未设置":
            pkg = rssapps.getPath(spyunit['spyuuid'])
            if pkg is not None:
                des = pkg.title
        if i >= page*5 and i < (page+1)*5:
            msg += "\n{0},{1},{2}".format(nick,spyunit['spyuuid'].replace('/','·'),des)
        i += 1
    msg += '\n当前页{0}/{1} (共{2}个订阅)'.format(page+1,int(lll/5)+1,lll)
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
@on_message(msgfilter='订阅列表',argfilter=argfilter,des='订阅列表 页码 - 获取订阅列表',sourceAdmin=True,bindperm='use',bindsendperm='manageself',at_to_me=False)
async def _(session:Session):
    page = session.filterargs['page']
    l = pushlist.getLitsFromPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
    msg = getSpyList(l,page)
    session.send(msg)

@on_message(msgfilter='清空订阅',des='清空订阅 - 清空订阅列表',sourceAdmin=True,bindperm='use',bindsendperm='manageself')
async def _(session:Session):
    res = pushlist.delPushunitFromPushTo(session.bottype,session.botuuid,session.botgroup,session.uuid)
    if not res[0]:
        session.send(res[1])
        return
    session.send("推送已清空")