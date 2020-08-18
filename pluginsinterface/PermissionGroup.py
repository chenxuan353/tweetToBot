# -*- coding: UTF-8 -*-
import os
import traceback
import re
import time
import config
from pluginsinterface.TypeExtension import PlugMsgTypeEnum
from helper import data_save,data_read_auto,getlogger
logger = getlogger(__name__)

DEBUG = config.DEBUG
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
permissionList = data_read_auto(config_filename,default={})
def permissionList_save():
    return data_save(config_filename,permissionList)

"""
合法权限与角色及默认授权表
启动时由注册函数注册，标识可授权权限及权限默认授权状态
同插件权限检查及授权可以使用session
跨权限组(跨插件)授权可以使用权限管理插件
跨权限组(跨插件)检查请使用插件管理类自行定义


·模块授权注册
固定标识:{权限组名:{模块名:'',组名:'',组昵称:'',组描述:'',权限列表:{权限名:{权限元对象},权限名:{},...}}}
perms:{groupname:{module:'',name:'',nick:'',des:'xxx',premlist:{perm:{},perm:{},...}}}
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
def permRegisterGroup(modulename:str,groupname:str,groupnick:str,groupdes:str,permlist:dict = {}):
    global legalPermissionList
    if not permNameCheck(groupname):
        raise Exception("权限组注册异常,{0} 不能作为权限组组名".format(groupname))
    if groupname in legalPermissionList['perms']:
        raise Exception("权限组注册冲突,名为 {0} 的组已存在".format(groupname))
    if type(permlist) != dict:
        raise Exception("权限组注册异常,名为 {0} 的组，权限列表不为字典".format(groupname))
    legalPermissionList['perms'][groupname] = {
        'module':modulename,
        'name':groupname,
        'nick':groupnick,
        'des':groupdes,
        'permlist':permlist.copy()
    }
def permRegisterPerm(groupname:str,name:str,des:str):
    global legalPermissionList
    if not permNameCheck(name):
        raise Exception("权限注册异常,{0} 不能作为权限名".format(name))
    if groupname not in legalPermissionList['perms']:
        raise Exception("权限注册异常,名为 {0} 的组不存在".format(groupname))
    if name in legalPermissionList['perms'][groupname]['permlist']:
        raise Exception("权限注册冲突,名为 {0} 的组中已存在 {1} 权限".format(groupname,name))
    legalPermissionList['perms'][groupname]['permlist'][name] = des
def legalPermHas(groupname:str,name:str = None):
    global legalPermissionList
    if name is not None and name.startswith('-'):
        name = name[1:]
    if groupname not in legalPermissionList['perms']:
        return False
    if name is not None:
        if name not in legalPermissionList['perms'][groupname]['permlist']:
            return False
    return True 
def legalPermGet(groupname:str = None,name:str = None) -> dict:
    global legalPermissionList
    if groupname is None:
        return legalPermissionList['perms']
    if name is not None and name.startswith('-'):
        name = name[1:]
    if groupname not in legalPermissionList['perms']:
        return {}
    if name is not None:
        if name in legalPermissionList['perms'][groupname]['permlist']:
            return legalPermissionList['perms'][groupname]['permlist'][name]
    return legalPermissionList['perms'][groupname]
def legalPermGroupGetDes(group:dict,simple = False) -> str:
    if simple:
        #组名，昵称，描述
        msg = '{0}:{1}:{2}'.format(
                group['name'],
                group['nick'],
                group['des'],
        )
    else:
        regperm = ''
        for perm in group['permlist']:
            if regperm:
                regperm += ','
            regperm += perm
        msg = '所属模块：{0}\n组名：{1}\n昵称：{2}\n描述：{3}\n注册权限：{4}'.format(
                group['module'],
                group['name'],
                group['nick'],
                group['des'],
                regperm,
        )
    return msg
def legalPermGetDes(group:dict,perm:dict) -> str:
    return "{0}:{1}:{2}".format(group['nick'],perm,group['permlist'][perm])
def illegalPermClear():
    #执行对不存在权限(非法权限)授权的清理
    raise Exception("illegalPermClear 暂未实现")

def permGetRole(rolename:str) -> dict:
    """
        获取角色，角色不存在时返回空字典
    """
    global legalPermissionList
    if rolename not in legalPermissionList['roles']:
        return {}
    return legalPermissionList['roles'][rolename]
def permRoleMerge(rolename:str,permgroup:str,permlist:set):
    """
        合并权限到指定角色
        角色不存在时将创建一个新角色
    """
    global legalPermissionList
    #合并组权限至角色
    if rolename not in legalPermissionList['roles']:
        legalPermissionList['roles'][rolename] = {}
    if type(permlist) != set:
        raise Exception("角色注册异常,{0} · {1}，权限列表类型不为集合(set)".format(rolename,permgroup))
    if permgroup in legalPermissionList['roles'][rolename]:
        permlist = permlist.union(legalPermissionList['roles'][rolename][permgroup])
    legalPermissionList['roles'][rolename][permgroup] = permlist

"""
·默认角色注册
角色：roles:{rolename:{permgroup:{permlist},...},...}
固定标识:{机器人标识(CQHttp、dingding...):{机器人组(group、private...):默认权限组名称}
default:{bottype:{botgroup:{groupname:{perm:{unit}...}...}}}
判断授权时将读取default内对应组名进行授权判断
"""
allow_bottype = ['cqhttp','dingding']
def permSetDefaultRoles(msgtypename,roles:set):
    """
        合并角色权限并设置至msgtype对应的所有权限组中
            bottype:bot标识
            magtype:消息类型
            roles:规则列表
    """
    global legalPermissionList
    perms = {}
    try:
        #角色权限合并
        roles = set(roles)
        for rolename in roles:
            role = permGetRole(rolename)
            #permGroupName
            for pgn in role:
                if pgn not in perms:
                    perms[pgn] = set()
                perms[pgn] = perms[pgn].union(role[pgn])
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        raise Exception('默认角色设置异常，请检查默认角色设置代码与角色注册代码。')
    #默认权限添加
    legalPermissionList['default'][msgtypename] = perms
    if DEBUG:
        logger.info("已注册默认组权限{0}->".format(msgtypename))
        logger.info(perms)
def permDefaultInit():
    """
        初始化各msgtype的默认权限设置
    """
    ls = PlugMsgTypeEnum.getAllowlist(PlugMsgTypeEnum.allowall)
    for msgtypename in ls:
        permSetDefaultRoles(msgtypename,{msgtypename})

"""
插件权限注册接口
"""
def authRegisterGroup(modulename:str,groupname:str,groupnick:str,groupdes:str):
    """
        注册插件权限组
    """
    return permRegisterGroup(modulename,groupname,groupnick,groupdes)
def authRegisterPerm(groupname:str,name:str,des:str):
    """
        注册插件权限
    """
    return permRegisterPerm(groupname,name,des)
def authRegisterDefaultPerm(groupname:str,perm:str,msgtype:PlugMsgTypeEnum):
    """
        注册插件默认权限
        msgtype:默认授予对象
    """
    msgtypelist = PlugMsgTypeEnum.getAllowlist(msgtype)
    for msgtypename in msgtypelist:
        permRoleMerge(msgtypename,groupname,{perm})
    return 


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
#核心函数
def perm_add(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str,authunit:dict) -> tuple:
    """
        设定权限
            authunit = {
                'bottype':bottype,
                'botuuid':botuuid,
                'msgtype':msgtype,
                'uuid':uuid,
                'groupname':groupname,
                'prem':perm,
                'createTimestamp':createTimestamp,
                'expireTimestamp':expireTimestamp,#大于0将在权限检查时检查是否过期，过期时此授权无效
                'objectRecognition':objectRecognition
            }
    """
    global permissionList
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = perm))
    dictSet(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm,obj=authunit)
    permissionList_save()
    return (True,'成功')
def perm_del(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> tuple:
    global permissionList
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = perm))
    #初始化层次字典
    if not dictHas(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm):
        return (False,"{groupname}->{perm},权限未曾授权".format(groupname = groupname,perm = perm))
    del permissionList[bottype][botuuid][msgtype][uuid][groupname][perm]
    permissionList_save()
    return (True,'成功')
#信息获取函数
def perm_getList(bottype:str,botuuid:str,msgtype:str,uuid:str) -> dict:
    global permissionList
    return dictGet(permissionList,bottype,botuuid,msgtype,uuid,default={})
def perm_get(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> tuple:
    """
        获取授权单元，不存在时返回False与原因
    """
    global permissionList
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = perm))
    if not dictHas(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm):
        return (False,"{groupname}->{perm},权限未曾授权".format(groupname = groupname,perm = perm))
    return (True,permissionList[bottype][botuuid][msgtype][uuid][groupname][perm])
def perm_has(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> bool:
    """
        检查授权单元是否存在
    """
    global permissionList
    if not legalPermHas(groupname,perm):
        return False
    if not dictHas(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm):
        return False
    return True

def perm_uuidGet(bottype:str,botuuid:str,msgtype:str,uuid:str) -> dict:
    global legalPermissionList,permissionList
    default:dict = dictGet(legalPermissionList['default'],msgtype,default=dict()).copy()
    if dictHas(permissionList,bottype,botuuid,msgtype,uuid):
        default.update(permissionList[bottype][botuuid][msgtype][uuid])
    return default
def perm_uuidAuthGet(bottype:str,botuuid:str,msgtype:str,uuid:str) -> dict:
    return dictGet(permissionList,bottype,botuuid,msgtype,uuid,default={}.copy())
#扩展函数
def perm_checkdeny(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> bool:
    """
        检查权限是否被显式禁用
    """
    global legalPermissionList,permissionList
    if perm.startswith('-'):
        perm = perm[1:]
    default:dict = dictGet(legalPermissionList['default'],msgtype,default={})
    if dictHas(default,groupname,'-*'):
        return True
    if dictHas(default,groupname,'-'+perm):
        return True
    nowtime = time.time()
    def authcheck(authunit:dict):
        if authunit == None:
            return False
        if 'expireTimestamp' in authunit:
            if authunit['expireTimestamp'] <= 0 or nowtime > authunit['expireTimestamp']:
                return True
        else:
            return True
        return True
    if authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,'-*')):
        return True
    if authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,'-'+perm)):
        return True
    return False
def perm_check(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> bool:
    global legalPermissionList,permissionList
    if perm.startswith('-'):
        raise Exception('无法检测')
    default:dict = dictGet(legalPermissionList['default'],msgtype,default={})
    if dictHas(default,groupname,'-*'):
        return False
    if dictHas(default,groupname,'-'+perm):
        return False
    res = dictHas(default,groupname,'*')
    res = res or dictHas(default,groupname,perm)
    nowtime = time.time()
    def authcheck(authunit:dict):
        if authunit is None:
            return False
        if 'expireTimestamp' in authunit:
            if authunit['expireTimestamp'] <= 0 or nowtime > authunit['expireTimestamp']:
                return True
        else:
            return True
        return False
    if not dictHas(permissionList,bottype,botuuid,msgtype,uuid,groupname):
        return res
    if authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,'-*')):
        return False
    if authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,'-'+perm)):
        return False
    if authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,'*')):
        return True
    if authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm)):
        return True
    return res

def perm_deny(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str,authunit:dict) -> tuple:
    if not perm.startswith('-'):
        perm = '-' + perm
    return perm_add(bottype,botuuid,msgtype,uuid,groupname,perm,authunit)
def perm_allow(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str,authunit:dict) -> tuple:
    if perm.startswith('-'):
        perm = perm[1:]
    if perm_checkdeny(bottype,botuuid,msgtype,uuid,groupname,perm):
        return (False,"{groupname}->{perm},授权被禁用请检查是否存在“-*”或“-{perm}”授权".format(groupname = groupname,perm = perm))
    res = perm_add(bottype,botuuid,msgtype,uuid,groupname,perm,authunit)
    if not res[0]:
        return res
    return res
"""
权限操作接口
"""
def authObjGetList(bottype:str,botuuid:str,msgtype:str,uuid:str,page:int = 1) -> str:
    msg = '--权限列表--'
    page = page - 1
    i = 0
    permlist = perm_getList(bottype,botuuid,msgtype,uuid)
    for groupname in permlist:
        for perm in permlist[groupname]:
            if i >= page*5 and i < (page+1)*5:
                msg += '\n' + groupname + ':' + perm
            i += 1
    lll = i
    msg += '\n当前页{0}/{1} (共{2}个权限)'.format(page+1,int(lll/5)+1,lll)
    return msg
def authLegalGetList(findgroupname = '',page:int = 1) -> str:
    msg = '--可用权限列表--'
    page = page - 1
    i = 0
    legalpermlist = legalPermGet()
    for groupname in legalpermlist:
        groupdict = legalPermGet(groupname)
        #i += 1
        #msg += '\n' + legalPermGroupGetDes(groupdict,simple=True)
        if not findgroupname or findgroupname == groupname:
            for perm in legalpermlist[groupname]['permlist']:
                if i >= page*5 and i < (page+1)*5:
                    msg += '\n' + legalPermGetDes(groupdict,perm)
                i += 1
    lll = i
    msg += '\n当前页{0}/{1} (共{2}个权限)'.format(page+1,int(lll/5)+1,lll)
    return msg
def authLegalGetGroupListDes(page:int = 1) -> str:
    msg = '--合法权限组列表--'
    legalpermlist = legalPermGet()
    page = page - 1
    i = 0
    lll = len(legalpermlist)
    if page > int(lll/5):
        page = 0
    for groupname in legalpermlist:
        groupdict = legalPermGet(groupname)
        if i >= page*5 and i < (page+1)*5:
            msg += '\n' + legalPermGroupGetDes(groupdict,simple=True)
        i += 1
    msg += '\n当前页{0}/{1} (共{2}个权限组)'.format(page+1,int(lll/5)+1,lll)
    return msg
def authGet(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> dict:
    """
        获取授权单元，不存在时返回空字典
            authunit = {
                'bottype':bottype,
                'botuuid':botuuid,
                'msgtype':msgtype,
                'uuid':uuid,
                'groupname':groupname,
                'prem':perm,
                'createTimestamp':createTimestamp,
                'expireTimestamp':expireTimestamp,#大于0将在权限检查时检查是否过期，过期时此授权无效
                'objectRecognition':objectRecognition
            }
    """
    botuuid = str(botuuid)
    uuid = str(uuid)
    return perm_get(bottype,botuuid,msgtype,uuid,groupname,perm)
def authBaleObjectRecognition(bottype:str,botuuid:str,msgtype:str,uuid:str,standmsg:str) -> dict:
    """
        打包授权来源单元objectRecognition
        objectRecognition:授权来源
        {
            'bottype':bottype,
            'botuuid':botuuid,
            'msgtype':msgtype,
            'uuid':uuid,
            'standmsg':standmsg,
            'createTimestamp':createTimestamp
        }
    """
    return {
        'bottype':bottype,
        'botuuid':botuuid,
        'msgtype':msgtype,
        'uuid':uuid,
        'standmsg':standmsg,
        'createTimestamp':time.time()
    }
def authAllow(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str,objectRecognition:dict,overlapping = True,**kw) -> tuple:
    """
        授权
        overlapping:是否覆盖授权(有可能已经授权)
        objectRecognition:授权来源
        {
            'bottype':bottype,
            'botuuid':botuuid,
            'msgtype':msgtype,
            'uuid':uuid,
            'standmsg':standmsg,
            'createTimestamp':createTimestamp
        }
    """
    botuuid = str(botuuid)
    uuid = str(uuid)
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = perm))
    nowtime = time.time()
    def authcheck(authunit:dict):
        if authunit is None:
            return False
        if 'expireTimestamp' in authunit:
            if authunit['expireTimestamp'] <= 0 or nowtime > authunit['expireTimestamp']:
                return True
        else:
            return True
        return False
    if overlapping and authcheck(dictGet(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm)):
        return (False,'授权重复！')
    createTimestamp = (kw['createTimestamp'] if 'createTimestamp' in kw else time.time())
    expireTimestamp = (kw['expireTimestamp'] if 'expireTimestamp' in kw else 0)
    authunit = {
        'bottype':bottype,
        'botuuid':botuuid,
        'msgtype':msgtype,
        'uuid':uuid,
        'groupname':groupname,
        'prem':perm,
        'createTimestamp':createTimestamp,
        'expireTimestamp':expireTimestamp,#大于0将在权限检查时检查是否过期，过期时此授权无效
        'objectRecognition':objectRecognition
    }
    return perm_allow(bottype,botuuid,msgtype,uuid,groupname,perm,authunit)
def authRemoval(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> tuple:
    """
        授权移除，仅对正常授权有效
    """
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = perm))
    return perm_del(bottype,botuuid,msgtype,uuid,groupname,perm)
def authDeny(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str,objectRecognition:dict,overlapping = True,**kw) -> tuple:
    """
        权限禁用
        overlapping:是否覆盖授权(有可能已经禁用)
        objectRecognition:授权来源
        {
            'bottype':bottype,
            'botuuid':botuuid,
            'msgtype':msgtype,
            'uuid':uuid,
            'standmsg':standmsg,
            'createTimestamp':createTimestamp
        }
    """
    botuuid = str(botuuid)
    uuid = str(uuid)
    if perm.startswith('-'):
        perm = perm[1:]
    if not legalPermHas(groupname,perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = perm))

    if overlapping and dictHas(permissionList,bottype,botuuid,msgtype,uuid,groupname,perm):
        return (False,'授权重复！')
    createTimestamp = (kw['createTimestamp'] if 'createTimestamp' in kw else time.time())
    expireTimestamp = (kw['expireTimestamp'] if 'expireTimestamp'in kw else 0)
    authunit = {
        'bottype':bottype,
        'botuuid':botuuid,
        'msgtype':msgtype,
        'uuid':uuid,
        'groupname':groupname,
        'prem':perm,
        'createTimestamp':createTimestamp,
        'expireTimestamp':expireTimestamp,#大于0将在权限检查时检查是否过期，过期时此授权无效
        'objectRecognition':objectRecognition
    }
    return perm_deny(bottype,botuuid,msgtype,uuid,groupname,perm,authunit)
def authDenyRemoval(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> tuple:
    if not legalPermHas(groupname,'-'+perm):
        return (False,"{groupname}->{perm},此权限不存在".format(groupname = groupname,perm = '-'+perm))
    return perm_del(bottype,botuuid,msgtype,uuid,groupname,'-'+perm)
def authCheck(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> bool:
    """
        权限检查，检查是否拥有指定权限
    """
    botuuid = str(botuuid)
    uuid = str(uuid)
    return perm_check(bottype,botuuid,msgtype,uuid,groupname,perm)
def authCheckDeny(bottype:str,botuuid:str,msgtype:str,uuid:str,groupname:str,perm:str) -> bool:
    """
        权限检查，检查是否拥有指定权限
    """
    botuuid = str(botuuid)
    uuid = str(uuid)
    return perm_checkdeny(bottype,botuuid,msgtype,uuid,groupname,perm)
















