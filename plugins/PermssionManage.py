# -*- coding: UTF-8 -*-
from pluginsinterface.PluginLoader import on_message,StandEven,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,plugGet,PluginsManage
from pluginsinterface.PluginLoader import SendMessage,plugGetListStr
from helper import getlogger
logger = getlogger(__name__)
"""
    权限管理插件
"""

@plugRegistered('权限管理插件','permission')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'chenxuan',#插件作者  
        'des':'用于管理权限的插件'#插件描述  
        }
