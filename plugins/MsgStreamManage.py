# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,PlugMsgTypeEnum,PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

from module.msgStream import getMsgStreamInfo,getStream,QueueStream

import asyncio
from helper import getlogger
logger = getlogger(__name__)

@plugRegistered('消息流管理','msgstream')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'chenxuan',#插件作者  
        'des':'用于管理发送消息流的插件'#插件描述  
        }

@on_plugloaded()
def _(plug:PluginsManage):
    if plug:
        #注册权限
        plug.registerPerm('manage',des = '管理权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('infocheck',des = '信息查看权限',defaultperm=PlugMsgTypeEnum.none)

@on_preprocessor()
async def _(session:Session) -> PlugMsgReturn:
    msg:str = session.sourcefiltermsg
    if msg.startswith(('!','！')):
        session.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Allow
    return PlugMsgReturn.Refuse

argfilter = PlugArgFilter()
argfilter.addArg(
    'bottype',
    'bot标识',
    'bot的标识',
    vlimit=['cqhttp','dingding']
    )
argfilter.addArg(
    'botuuid',
    'bot唯一ID',
    'bot的唯一ID'
    )
@on_message(msgfilter='查询指定消息流状态',argfilter=argfilter,bindsendperm='infocheck',des='查询指定消息流状态 bot标识 bot唯一ID - 查询指定消息流状态')
async def _(session:Session):
    bottype = session.filterargs['bottype']
    botuuid = session.filterargs['botuuid']
    msg = getMsgStreamInfo(bottype,botuuid)
    session.send(msg)
@on_message(msgfilter='关闭指定消息流',argfilter=argfilter,bindsendperm='manage',des='关闭指定消息流 bot标识 bot唯一ID- 关闭指定消息流')
async def _(session:Session):
    bottype = session.filterargs['bottype']
    botuuid = session.filterargs['botuuid']
    stream:QueueStream = getStream(bottype,botuuid)
    if not stream.open:
        session.send('消息流已经是关闭状态')
        return
    stream.streamSwitch(False)
    session.send('消息流关闭成功')
@on_message(msgfilter='开启指定消息流',argfilter=argfilter,bindsendperm='manage',des='开启指定消息流 bot标识 bot唯一ID- 开启指定消息流')
async def _(session:Session):
    bottype = session.filterargs['bottype']
    botuuid = session.filterargs['botuuid']
    stream:QueueStream = getStream(bottype,botuuid)
    if stream.open:
        session.send('消息流已经是开启状态')
        return
    stream.streamSwitch(True)
    session.send('消息流开启成功')



@on_message(msgfilter='消息流状态',bindsendperm='infocheck',des='消息流状态 - 获取当前消息流状态')
async def _(session:Session):
    msg = getMsgStreamInfo(session.bottype,session.botuuid)
    session.send(msg)
@on_message(msgfilter='关闭消息流',bindsendperm='manage',des='关闭消息流- 关闭当前发送消息流')
async def _(session:Session):
    stream:QueueStream = getStream(session.bottype,session.botuuid)
    if not stream.open:
        session.send('消息流已经是关闭状态')
        return
    stream.streamSwitch(False)
    session.send('消息流关闭成功')
@on_message(msgfilter='开启消息流',bindsendperm='manage',des='开启消息流- 开启当前发送消息流')
async def _(session:Session):
    stream:QueueStream = getStream(session.bottype,session.botuuid)
    if stream.open:
        session.send('消息流已经是开启状态')
        return
    stream.streamSwitch(True)
    session.send('消息流开启成功')

@on_message(msgfilter='获取消息流组标识',bindsendperm='infocheck',des='获取消息流组标识 - 获取当前组标识')
async def _(session:Session):
    session.send("当前组标识为："+session.botgroup)

argfilter = PlugArgFilter()
argfilter.addArg(
    'botgroup',
    '消息来源组',
    '需要输入有效的消息来源组名称',
    canSkip=False
    )
argfilter.addArg(
    'uuid',
    '消息来源ID',
    '需要输入有效的消息来源名称',
    canSkip=False,
    )
@on_message(msgfilter='消息流定向放行',argfilter=argfilter,bindsendperm='manage',des='消息流定向放行 消息来源组 ID- 消息流定向放行')
async def _(session:Session):
    stream:QueueStream = getStream(session.bottype,session.botuuid)
    if not stream.open:
        return
    botgroup = session.filterargs['botgroup']
    uuid = session.filterargs['uuid']
    if stream.setAllow(botgroup,uuid):
        session.send('放行成功')
    else:
        session.send('放行失败')
@on_message(msgfilter='消息流定向阻止',argfilter=argfilter,bindsendperm='manage',des='消息流定向阻止 消息来源组 ID- 消息流定向阻止')
async def _(session:Session):
    stream:QueueStream = getStream(session.bottype,session.botuuid)
    if not stream.open:
        return
    botgroup = session.filterargs['botgroup']
    uuid = session.filterargs['uuid']
    if stream.setDeny(botgroup,uuid):
        session.send('阻止成功')
    else:
        session.send('阻止失败')

@on_message(msgfilter='消息流放行',bindsendperm='manage',des='消息流放行 - 消息流放行')
async def _(session:Session):
    stream:QueueStream = getStream(session.bottype,session.botuuid)
    if not stream.open:
        return
    if stream.setAllow(session.botgroup,session.uuid):
        session.send('放行成功')
    else:
        session.send('放行失败')
@on_message(msgfilter='消息流阻止',bindsendperm='manage',des='消息流阻止 - 消息流阻止')
async def _(session:Session):
    stream:QueueStream = getStream(session.bottype,session.botuuid)
    if not stream.open:
        return
    if stream.setDeny(session.botgroup,session.uuid):
        session.send('阻止成功')
    else:
        session.send('阻止失败')
