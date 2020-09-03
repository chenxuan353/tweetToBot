# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,PlugMsgTypeEnum,PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

from pluginsinterface.PermissionGroup import permNameCheck,authLegalGetGroupListDes,authLegalGetList,authObjGetList
import asyncio
from helper import getlogger
logger = getlogger(__name__)
"""
    权限管理插件
"""

@plugRegistered('权限管理','permission')
def _():
    return {
        'plugmanagement':'1.0',# 插件注册管理(原样)  
        'version':'1.0',# 插件版本  
        'auther':'chenxuan',# 插件作者  
        'des':'用于管理权限的插件'# 插件描述  
        }

@on_plugloaded()
def _(plug:PluginsManage):
    if plug:
        # 注册权限
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
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}# 设置默认值
    )

@on_message(msgfilter='合法权限组列表',argfilter=argfilter,bindsendperm='infocheck',des='合法权限组列表 页码 - 合法权限组列表')
async def _(session:Session):
    page = session.filterargs['page']
    msg = authLegalGetGroupListDes(page)
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
    'groupname',
    '权限组',
    '需要输入有效的权限组名称',
    prefunc=(lambda arg:(arg if permNameCheck(arg) else None)),
    vlimit={'':None},
    canSkip=True
    )
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}# 设置默认值
    )
@on_message(msgfilter='合法权限列表',argfilter=argfilter,bindsendperm='infocheck',des='合法权限列表 页码 - 合法权限列表')
async def _(session:Session):
    groupname = session.filterargs['groupname']
    page = session.filterargs['page']
    msg = authLegalGetList(groupname,page)
    session.send(msg)
@on_message(msgfilter='查看授权',argfilter=argfilter,des='查看授权 页码 - 查看授权权限')
async def _(session:Session):
    page = session.filterargs['page']
    msg = authObjGetList(session.bottype,
                        session.botuuid,
                        PlugMsgTypeEnum.getMsgtype(session.msgtype),
                        session.uuid,
                        page
                    )
    session.send(msg)

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
argfilter.addArg(
    'groupname',
    '权限组',
    '需要输入有效的权限组名称',
    prefunc=(lambda arg:(arg if permNameCheck(arg) else None)),
    canSkip=False
    )
argfilter.addArg(
    'perm',
    '权限名',
    '需要输入有效的权限名',
    prefunc=(lambda arg:(arg if permNameCheck(arg) else None)),
    canSkip=False
    )
@on_message(msgfilter='远程授权',argfilter=argfilter,bindsendperm='manage',des='远程授权 消息来源标识 消息来源ID 权限组 权限名 - 消息来源标识为群聊、私聊中的任意一项')
async def _(session:Session):
    msgtype = session.filterargs['msgtype']
    uuid = session.filterargs['uuid']
    groupname = session.filterargs['groupname']
    perm = session.filterargs['perm']
    res = session.authAllow(session.bottype,session.botuuid,msgtype,uuid,groupname,perm)
    session.send(res[1])

@on_message(msgfilter='远程取消授权',argfilter=argfilter,bindsendperm='manage',des='远程取消授权 消息来源标识 消息来源ID 权限组 权限名 - 消息来源标识为群聊、私聊中的任意一项')
async def _(session:Session):
    msgtype = session.filterargs['msgtype']
    uuid = session.filterargs['uuid']
    groupname = session.filterargs['groupname']
    perm = session.filterargs['perm']
    res = session.authRemoval(session.bottype,session.botuuid,msgtype,uuid,groupname,perm)
    session.send(res[1])

@on_message(msgfilter='远程授权禁用',argfilter=argfilter,bindsendperm='manage',des='远程授权禁用 消息来源标识 消息来源ID 权限组 权限名 - 消息来源标识为群聊、私聊中的任意一项')
async def _(session:Session):
    msgtype = session.filterargs['msgtype']
    uuid = session.filterargs['uuid']
    groupname = session.filterargs['groupname']
    perm = session.filterargs['perm']
    res = session.authDeny(session.bottype,session.botuuid,msgtype,uuid,groupname,perm)
    session.send(res[1])

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
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}# 设置默认值
    )
@on_message(msgfilter='查询授权',argfilter=argfilter,bindsendperm='infocheck',des='查询授权 消息来源标识 消息来源ID 页码 - 查询指定对象的权限')
async def _(session:Session):
    msgtype = session.filterargs['msgtype']
    uuid = session.filterargs['uuid']
    page = session.filterargs['page']
    msg = authObjGetList(session.bottype,
                        session.botuuid,
                        msgtype,
                        uuid,
                        page
                    )
    session.send(msg)
