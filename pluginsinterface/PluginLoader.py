# -*- coding: UTF-8 -*-
#插件装载
from pluginsinterface.TypeExtension import PlugMsgReturn, PlugMsgTypeEnum
from pluginsinterface.PlugFilter import PlugArgFilter
from pluginsinterface.EventHandling import StandEven
from pluginsinterface.PlugSession import SessionManagement, Session
from pluginsinterface.PlugFilter import SendMessage
#插件相关类
from pluginsinterface.Plugmanagement import PluginsManage, plugGetListStr, plugGetNameList
from pluginsinterface.Plugmanagement import plugLoads, plugRegistered, on_message, on_preprocessor, on_plugloaded
from pluginsinterface.Plugmanagement import plugGetNamePlug, plugGet, plugGetNamePlugDes
#启动
from pluginsinterface.PlugAsyncio import RunLoop as plugRunLoop
"""
本类用于创建插件制作与使用者可见类型
并尽可能保证这些类的稳定性
注：类仅保证含有使用注释部分的兼容性
其他代码可能会有不兼容改动
"""
"""
通用插件接口
用于给各类bot添加通用插件

通用插件特点：
消息从哪来回哪去
使用pluginsinterface.PlugSession获取Session
使用pluginsinterface.PermissionGroup管理权限
使用module.msgStream发送信息
不处理聊天以外的数据，使用有限的信息处理数据
消息类型：私聊(一对一)、群聊(一对多)、临时聊天(一对一)、临时群聊(一对多)
来源是否匿名：True/False (例如QQ群匿名等)
"""
