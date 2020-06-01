# -*- coding: UTF-8 -*-
from helper import data_save,data_read,getlogger
import os
import traceback
import re
logger = getlogger(__name__)
config_filename = 'permission.json'
allow_msg_type = ('private','group')
permissionList = {
    'private':{},
    'group':{}
}
legalPermissionList = {} #权限列表
res = data_read(config_filename)
if res[0]:
    permissionList = res[2]
    for k1 in permissionList:
        for k2 in list(permissionList[k1].keys()):
            permissionList[k1][int(k2)] = permissionList[k1][k2]
            del permissionList[k1][k2]
#权限名称是否合法
def perm_isLegalPerm(perm_group:str,perm_unit:str = None):
    #权限组与权限名,以字母开头,只能包含字母、数字与下划线
    res = re.match(r'(([A-Za-z]{1}[A-Za-z0-9_]*)|\*)',perm_group)
    if res == None:
        #权限组验证不通过
        return False
    if perm_unit != None:
        #以减号开头表示权限拒绝(优先于*号,-*的权限将拒绝所有)
        res = re.match(r'-?(([A-Za-z]{1}[A-Za-z0-9_]*)|\*)',perm_unit)
        if res == None:
            return False
        return True
    return True
#获取权限组
def perm_getGroup(perm_group:str):
    global legalPermissionList
    if perm_group not in legalPermissionList:
        return None
    return legalPermissionList[perm_group]
#权限/权限组是否存在
def perm_hasPermUnit(perm_group:str,perm_unit:str = None):
    global legalPermissionList
    res = perm_getGroup(perm_group)
    if perm_unit == None:
        return res != None
    if perm_unit == '*' or perm_unit == '-*':
        return True
    return (perm_unit in legalPermissionList[perm_group]['perms']) or (('-'+perm_unit) in legalPermissionList[perm_group]['perms'])
#添加权限组(权限所在模块名，权限描述，权限组名)
def perm_addLegalPermGroup(name:str,des:str,perm_group:str):
    global legalPermissionList
    if perm_group in legalPermissionList:
        return
    legalPermissionList[perm_group] = {
        'name':name,
        'des':des,
        'perms':[]
    }
#添加权限(权限组名，权限名)
def perm_addLegalPermUnit(perm_group:str,perm_unit:str):
    global legalPermissionList
    if perm_group not in legalPermissionList:
        return
    legalPermissionList[perm_group]['perms'].append(perm_unit)
#权限组是否存在
def hasPermGroup(msg_type:str,sid:int,perm_group:str):
    global permissionList
    if msg_type not in allow_msg_type:
        return False
    if sid not in permissionList[msg_type]:
        return False
    if perm_group not in permissionList[msg_type][sid]:
        return False
    return True
#授权(授权类型，授权对象，授权操作人，权限组，权限名)
def perm_add(msg_type:str,sid:int,opid:int,perm_group:str,perm_unit:str = None) -> tuple:
    global permissionList
    if not perm_hasPermUnit(perm_group,perm_unit):
        return (False,'权限或权限组不存在')
    if msg_type not in allow_msg_type:
        return (False,'不支持的消息类型')
    if sid not in permissionList[msg_type]:
        permissionList[msg_type][sid] = {}
    if perm_group not in permissionList[msg_type][sid]:
        permissionList[msg_type][sid][perm_group] = {}
    if perm_unit != None:
        permissionList[msg_type][sid][perm_group][perm_unit] = {
            'perm_unit':perm_unit,
            'msg_type':msg_type,
            'sid':sid,
            'opid':opid,
            'perm_group':perm_group
        }
    res = data_save(config_filename,permissionList)
    if not res[0]:
        return (False,'授权保存失败，请联系管理者')
    return (True,'授权设置成功')
#取消授权
def perm_del(msg_type:str,sid:int,opid:int,perm_group:str,perm_unit:str = None) -> tuple:
    global permissionList
    if not hasPermGroup(msg_type,sid,perm_group):
        #权限组不存在
        return (False,'权限组不存在')
    if perm_unit != None:
        if perm_unit in permissionList[msg_type][sid][perm_group]:
            del permissionList[msg_type][sid][perm_group][perm_unit]
    else:
        del permissionList[msg_type][sid][perm_group]
    res = data_save(config_filename,permissionList)
    if not res[0]:
        return (False,'授权保存失败，请联系管理者')
    return (True,'移除授权成功')

#权限检查，通过为True
def perm_check(msg_type:str,sid:int,perm_group:str,perm_unit:str = None) -> bool:
    global permissionList
    if not hasPermGroup(msg_type,sid,perm_group):
        #权限组不存在
        return False
    if perm_unit != None:
        if '-' + perm_unit in permissionList[msg_type][sid][perm_group]:
            return False
        if '*' in permissionList[msg_type][sid][perm_group]:
            return True
        if perm_unit in permissionList[msg_type][sid][perm_group]:
            return True
        else:
            return False
    return True
#获取权限组授权列表
def perm_getPermList(msg_type:str,sid:int,perm_group:str) -> tuple:
    global permissionList
    if not hasPermGroup(msg_type,sid,perm_group):
        #权限组不存在
        return (False,'权限组不存在')
    permgroup = {
        'permlist':permissionList[msg_type][sid][perm_group],
        'info':perm_getGroup(perm_group)
    }
    return (True,'获取成功',permgroup)
#获取权限组列表
def perm_getPermGroupList(msg_type:str,sid:int) -> list:
    global permissionList
    res = []
    if sid not in permissionList[msg_type]:
        return (True,"成功",[])
    group = permissionList[msg_type][sid]
    for key,val in group.items():
        permgroup = {
            'groupname':key,
            'permlist':val,
            'info':perm_getGroup(key)
        }
        res.append(permgroup)
    return (True,"成功",res)

