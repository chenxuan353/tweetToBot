# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,plugGetNamePlug,PluginsManage
from pluginsinterface.PluginLoader import SendMessage,plugGetListStr,PlugMsgTypeEnum
from pluginsinterface.PluginLoader import PlugArgFilter,plugGetNameList,plugGetNamePlugDes
import asyncio
import config
from helper import getlogger
logger = getlogger(__name__)
"""
    插件管理
"""
@plugRegistered('插件管理','plugmanage')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'chenxuan',#插件作者  
        'des':'用于管理插件的插件'#插件描述  
        }

@on_plugloaded()
def _(plug:PluginsManage):
    if plug:
        #注册权限
        plug.registerPerm('manage',des = '全局管理权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('selfmanage',des = '管理自己插件的权限',defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('infocheck',des = '信息查看权限',defaultperm=PlugMsgTypeEnum.none)

@on_preprocessor()
async def _(session:Session) -> PlugMsgReturn:
    msg:str = session.sourcefiltermsg
    if msg.startswith(('!','！')):
        session.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Allow
    return PlugMsgReturn.Refuse

#自动参数过滤器的使用
argfilter = PlugArgFilter()
argfilter.addArg(
    'plugnick',
    '插件昵称',
    '需要输入插件的昵称',
    prefunc=(lambda arg:(arg if arg in plugGetNameList() else None)),
    canSkip=True,
    vlimit={'':''}
    )
argfilter.addArg(
    'page',
    '页码',
    '帮助的页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='(help)|(帮助)',argfilter=argfilter,des='help或帮助 插件名 页码 - 获取帮助信息，插件名与页码可选，不显示被禁用插件',at_to_me=False)
async def _(session:Session):
    mastername = config.mastername
    project_des = config.project_des
    project_addr = config.project_addr
    if not mastername:
        mastername = '未知'
    if not project_des:
        project_des = '没有描述'
    if not project_addr:
        project_addr = '暂无'
    page = session.filterargs['page']
    plugnick = session.filterargs['plugnick']
    if plugnick != '':
        plug = plugGetNamePlug(plugnick)
        if not plug:
            session.send('插件不存在')
            return
        msg = ''
        if page == 1:
            msg += plug.getPlugDes().strip() + '\n------\n'
        msg += plug.getPlugFuncsDes(page).strip()
        session.send(msg)
        return
    if page == 1:
        msg = '----帮助----\n维护者：{mastername}\n项目描述：{project_des}\n项目地址：{project_addr}\n'.format(
                mastername=mastername,
                project_des=project_des,
                project_addr=project_addr
            )
    else:
        msg = '----帮助----\n'
    msg += plugGetListStr(page)
    session.send(msg)

argfilter = PlugArgFilter()
argfilter.addArg(
    'plugnick',
    '插件昵称',
    '需要输入插件的昵称',
    prefunc=(lambda arg:(arg if arg in plugGetNameList() else None)),
    canSkip=False
    )
@on_message(msgfilter='全局禁用插件',argfilter=argfilter,bindsendperm='manage',des='全局禁用插件 插件名 - 全局禁用插件')
async def _(session:Session):
    plugnick = session.filterargs['plugnick']
    plug:PluginsManage = plugGetNamePlug(plugnick)
    if plug:
        if not plug.open:
            session.send('插件 {0} 未启用'.format(plugnick))
        else:
            plug.switchPlug(False)
            session.send('插件 {0} 禁用成功'.format(plugnick))
    else:
        session.send('未查找到名为 {0} 的插件'.format(plugnick))

@on_message(msgfilter='全局启用插件',argfilter=argfilter,bindsendperm='manage',des='全局启用插件 插件名 - 全局启用插件')
async def _(session:Session):
    plugnick = session.filterargs['plugnick']
    plug:PluginsManage = plugGetNamePlug(plugnick)
    if plug:
        if plug.open:
            session.send('插件 {0} 已经是启用状态'.format(plugnick))
        else:
            plug.switchPlug(True)
            session.send('插件 {0} 启用成功'.format(plugnick))
    else:
        session.send('未查找到名为 {0} 的插件'.format(plugnick))


@on_message(msgfilter='禁用插件',argfilter=argfilter,sourceAdmin=True,des='禁用插件 插件名 - 在当前聊天中禁用插件')
async def _(session:Session):
    plugnick = session.filterargs['plugnick']
    plug:PluginsManage = plugGetNamePlug(plugnick)
    if plug:
        if session.authCheckSendDeny(plug.groupname,'plugopen'):
            session.send('插件 {0} 未启用'.format(plugnick))
        else:
            res = session.authDenySelf(plug.groupname,'plugopen')
            if not res[0]:
                session.send('插件 {0} 禁用失败，{1}'.format(plugnick,res[1]))
                return
            session.send('插件 {0} 禁用成功'.format(plugnick))
    else:
        session.send('未查找到名为 {0} 的插件'.format(plugnick))

@on_message(msgfilter='启用插件',argfilter=argfilter,sourceAdmin=True,des='启用插件 插件名 - 在当前聊天中启用插件')
async def _(session:Session):
    plugnick = session.filterargs['plugnick']
    plug:PluginsManage = plugGetNamePlug(plugnick)
    if plug:
        if not session.authCheckSendDeny(plug.groupname,'plugopen'):
            session.send('插件 {0} 已启用'.format(plugnick))
        else:
            res = session.authDenyRemovalSelf(plug.groupname,'plugopen')
            if not res[0]:
                session.send('插件 {0} 启用失败，{1}'.format(plugnick,res[1]))
                return
            session.send('插件 {0} 启用成功'.format(plugnick))
    else:
        session.send('未查找到名为 {0} 的插件'.format(plugnick))

argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='插件列表',argfilter=argfilter,bindsendperm='infocheck',des='插件列表 页码 - 插件列表')
async def _(session:Session):
    page = session.filterargs['page']
    msg = plugGetListStr(page,displaynone=True)
    session.send(msg)

