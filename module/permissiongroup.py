# -*- coding: UTF-8 -*-
from helper import data_save,data_read,getlogger
from nonebot import CommandSession
from enum import Enum
import os
import traceback
import re
import time
logger = getlogger(__name__)

config_filename = 'permission.json'
"""
权限授权与验证模块
"""

#可用权限列表，键名使用模块名或自定义名称，不能重复
legalPermissionList = {
    'perms':{},
    'roles':{},
    'default':{}
}

#默认权限组
groupPermissionList = {

}

#授权权限表
permissionList = {}

#初始化
def init():
    global permissionList
    #读取已授权的权限列表
    res = data_read(config_filename)
    if res[0]:
        permissionList = res[2]
init()

"""
合法权限与角色及默认授权表
启动时由注册函数注册，标识可授权权限及权限默认授权状态

·模块授权注册
固定标识:{权限组名:{模块名:'',组名:'',组昵称:'',组描述:'',权限列表:{权限名:{权限元对象},权限名:{},...}}}
perms:{groupname:{moudel:'',name:'',nick:'',des:'xxx',premlist:{perm:{},perm:{},...}}}
·权限元对象
权限名、权限描述

·角色权限注册
启动时由注册函数注册，标识
固定标识:{角色:{权限组1:{拥有的权限},权限组2:{...},...}}
roles:{role:{groupname:{permlist}}}
"""
def permNameCheck(name:str):
    #权限组与权限名,以字母开头,只能包含字母、数字与下划线
    res = re.match(r'(([A-Za-z]{1}[A-Za-z0-9_]*)|\*)',name)
    if res == None:
        #权限组验证不通过
        return False
    return True
def permRegisterGroup(moudelname:str,groupname:str,groupnick:str,groupdes:str,permlist:dict = {}):
    global legalPermissionList
    if permNameCheck(groupname):
        raise Exception("权限组注册异常,{0} 不能作为权限组组名".format(groupname))
    if groupname in legalPermissionList['perms']:
        raise Exception("权限组注册冲突,名为 {0} 的组已存在".format(groupname))
    if type(permlist) != dict:
        raise Exception("权限组注册异常,名为 {0} 的组，权限列表不为字典".format(groupname))
    legalPermissionList['perms'][groupname] = {
        'moudel':moudelname,
        'name':groupname,
        'nick':groupnick,
        'des':groupdes,
        'permlist':permlist.copy()
    }
def permRegisterPerm(groupname:str,name:str,des:str):
    global legalPermissionList
    if permNameCheck(name):
        raise Exception("权限注册异常,{0} 不能作为权限名".format(name))
    if groupname not in legalPermissionList['perms']:
        raise Exception("权限注册异常,名为 {0} 的组不存在".format(groupname))
    if name in legalPermissionList['perms'][groupname]['permlist']:
        raise Exception("权限注册冲突,名为 {0} 的组中已存在 {1} 权限".format(groupname,name))
    legalPermissionList['perms'][groupname]['permlist'][name] = des
def legalPermHas(groupname:str,name:str = None):
    global legalPermissionList
    if groupname not in legalPermissionList['perms']:
        return False
    if name != None:
        if name not in legalPermissionList['perms'][groupname]:
            return False
    return True 
def illegalPermClear():
    #执行对不存在权限(非法权限)授权的清理
    raise Exception("illegalPermClear 暂未实现")

def permGetRole(role:str):
    global legalPermissionList
    if role not in legalPermissionList['roles']:
        return None
    return legalPermissionList['roles'][role]
def permRoleMerge(rolename:str,permgroup:str,permlist:set):
    global legalPermissionList
    #合并组权限至角色
    if rolename not in legalPermissionList['roles']:
        legalPermissionList['roles'][rolename] = {}
    if type(permlist) != set:
        raise Exception("权限组注册异常,名为 {0} 的组，权限列表类型不为集合(set)".format(permgroup))
    #if permgroup in legalPermissionList['roles'][rolename]:
    #    raise Exception("此角色的 {0} 权限组已存在，无法多次合并同一组权限".format(permgroup))
    if permgroup in legalPermissionList['roles'][rolename]:
        permlist = permlist.union(legalPermissionList['roles'][rolename][permgroup])
    legalPermissionList['roles'][rolename][permgroup] = permlist.copy()

"""
·默认角色注册
固定标识:{机器人标识(CQHttp、dingding...):{机器人组(group、private...):默认权限组名称}
default:{bottype:{botgroup:{groupname:{perm:{unit}...}...}}}
判断授权时将读取default内对应组名进行授权判断
"""
allow_bottype = ['cqhttp','dingding']
def permSetDefaultRoles(bottype:str,botgroup:str,roles:set):
    global legalPermissionList,allow_bottype
    if bottype not in allow_bottype:
        logger.info(allow_bottype)
        raise Exception('不被允许的bottype')
    if bottype not in legalPermissionList['default']:
        legalPermissionList['default'][bottype] = {}
    perms = {}
    try:
        roles = set(roles)
        for rolename in roles:
            role = permGetRole(rolename)
            #permGroupName
            for pgn in role:
                if pgn not in perms:
                    perms[pgn] = set()
                perms[pgn].union(role[pgn])
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        raise Exception('默认角色设置异常，请检查默认角色设置代码与角色注册代码。')
    legalPermissionList['default'][bottype][botgroup] = perms
    logger.debug("已设置默认组权限{0}->{1}->".format(bottype,botgroup))
    logger.debug(perms)

"""
权限表
默认使用文件存储方式
设置的值将在启动后加载到内存中
权限表的授权将覆盖默认权限进行判定
机器人标识(CQHttp、dingding...):{机器人组(group、private...):对象唯一标识:{权限组名:{授权识别代码,授权代码,对象识别代码}}}
bottype:{botuuid:{botgroup:{uuid:{groupname:{prem:{unit},...}}}}}

·授权识别代码
机器人标识
机器人识别码
机器人组名
被授权对象唯一标识(对象唯一标识)
授权截止时间戳
授权创建时间戳
·授权代码
权限值
·对象识别代码
由添加授权的函数指定，一般由被授权对象标识以及授权人标识组成

"""
from helper import dictInit,dictHas,dictGet,dictSet

def perm_add(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str,authunit:dict):
    global permissionList
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname,perm))
    #初始化层次字典
    res = dictInit(permissionList,bottype,botuuid,botgroup,uuid,groupname,perm,endobj=authunit)
    if res:
        return (True,'成功')
    else:
        return (False,'')
def perm_del(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str):
    global permissionList
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname,perm))
    #初始化层次字典
    dictInit(permissionList,bottype,botuuid,botgroup,uuid,groupname)
    if perm not in permissionList[bottype][botuuid][botgroup][uuid][groupname]:
        return (False,"{groupname}->{perm},权限未曾授权".format(groupname,perm)) 
    del permissionList[bottype][botuuid][botgroup][uuid][groupname][perm]
    return (True,'成功')
def perm_uuidGet(bottype:str,botuuid:str,botgroup:str,uuid:str):
    global legalPermissionList,permissionList
    default:dict = dictGet(legalPermissionList['default'],bottype,botgroup,default={})
    if dictHas(permissionList,bottype,botuuid,botgroup,uuid):
        default.update(permissionList[bottype][botuuid][botgroup][uuid])
    return default
def perm_uuidAuthGet(bottype:str,botuuid:str,botgroup:str,uuid:str):
    return dictGet(permissionList,bottype,botuuid,botgroup,uuid,default={}.copy())

def perm_has(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str):
    global legalPermissionList,permissionList
    default:dict = dictGet(legalPermissionList['default'],bottype,botgroup,default={})
    if dictHas(default,groupname,'-*'):
        return False
    if perm[0] != '-' and dictHas(default,groupname,'-'+perm):
        return False
    res = dictHas(default,groupname,'*')
    res = res or dictHas(default,groupname,perm)
    nowtime = time.time()
    def authcheck(authunit:dict):
        if authunit == None:
            return False
        if 'expireTimestamp' in authunit:
            if authunit['expireTimestamp'] > 0 and nowtime > authunit['expireTimestamp']:
                return True
        else:
            return True
        return False
    if not dictHas(permissionList,bottype,botuuid,botgroup,uuid,groupname):
        return res
    if authcheck(dictGet(permissionList,bottype,botuuid,botgroup,uuid,groupname,'-*')):
        return False
    if authcheck(dictHas(permissionList,bottype,botuuid,botgroup,uuid,groupname,'-'+perm)):
        return False
    if authcheck(dictHas(permissionList,bottype,botuuid,botgroup,uuid,groupname,'*')):
        return True
    if authcheck(dictGet(permissionList,bottype,botuuid,botgroup,uuid,groupname,perm)):
        return True
    return res
def perm_check(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str):
    return perm_has(bottype,botuuid,botgroup,uuid,groupname,perm)

def authget(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str):
    botuuid = str(botuuid)
    uuid = str(uuid)
    permhas = perm_has(bottype,botuuid,botgroup,uuid,groupname,perm)
    return permhas
def authadd(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str,objectRecognition = None,overlapping = True,**kw):
    global legalPermissionList
    botuuid = str(botuuid)
    uuid = str(uuid)
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname,perm))
    if overlapping and dictHas(permissionList,bottype,botuuid,botgroup,uuid,groupname,perm):
        return (False,'授权重复！')
    createTimestamp = (kw['createTimestamp'] if kw['createTimestamp'] else time.time())
    expireTimestamp = (kw['expireTimestamp'] if kw['expireTimestamp'] else 0)
    authunit = {
        'bottype':bottype,
        'botuuid':botuuid,
        'botgroup':botgroup,
        'uuid':uuid,
        'groupname':groupname,
        'prem':perm,
        'createTimestamp':createTimestamp,
        'expireTimestamp':expireTimestamp,#大于0将在权限检查时检查是否过期，过期时此授权无效
        'objectRecognition':objectRecognition
    }
    return perm_add(bottype,botuuid,botgroup,uuid,groupname,perm,authunit)
def authdel(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str):
    botuuid = str(botuuid)
    uuid = str(uuid)
    return perm_del(bottype,botuuid,botgroup,uuid,groupname,perm)
def authcheck(bottype:str,botuuid:str,botgroup:str,uuid:str,groupname:str,perm:str):
    botuuid = str(botuuid)
    uuid = str(uuid)
    return perm_check(bottype,botuuid,botgroup,uuid,groupname,perm)
















